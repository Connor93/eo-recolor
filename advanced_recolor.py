import argparse
import os
import random
import json
from PIL import Image
import numpy as np
import colorsys
from sklearn.cluster import KMeans


def rgb_to_hsv(color):
    return colorsys.rgb_to_hsv(*(c / 255.0 for c in color))

def hsv_to_rgb(hsv):
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*hsv))

def rotate_hue(h, degrees):
    return (h + degrees / 360.0) % 1.0

def generate_color_scheme_palette(base_rgb, count, scheme="complementary"):
    base_h, s, v = rgb_to_hsv(base_rgb)
    palette = []

    if scheme == "complementary":
        hues = [base_h, rotate_hue(base_h, 180)]
    elif scheme == "analogous":
        hues = [rotate_hue(base_h, d) for d in (-30, 0, 30)]
    elif scheme == "triadic":
        hues = [rotate_hue(base_h, d) for d in (0, 120, 240)]
    elif scheme == "monochrome":
        hues = [base_h]
    else:
        raise ValueError("Unknown color scheme")

    while len(palette) < count:
        for h in hues:
            rgb = hsv_to_rgb((h, s, v))
            palette.append(rgb)
            if len(palette) >= count:
                break

    return palette[:count]


def generate_smart_color_map(unique_colors, seed=None, base_rgb=None, scheme=None, n_clusters=8):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    unique_colors = np.array(unique_colors)
    hsv_colors = np.array([rgb_to_hsv(c) for c in unique_colors])

    kmeans = KMeans(n_clusters=min(n_clusters, len(unique_colors)), n_init=10)
    labels = kmeans.fit_predict(hsv_colors)

    color_map = {}

    # Generate a base palette from the scheme
    if scheme and base_rgb is not None:
        palette = generate_color_scheme_palette(base_rgb, n_clusters, scheme)
    else:
        palette = [tuple(random.choices(range(256), k=3)) for _ in range(n_clusters)]

    for cluster_id in range(n_clusters):
        cluster_indices = np.where(labels == cluster_id)[0]
        base_hsv = hsv_colors[cluster_indices[0]]
        target_rgb = palette[cluster_id]
        target_hsv = rgb_to_hsv(target_rgb)

        for idx in cluster_indices:
            orig_rgb = tuple(unique_colors[idx])
            hsv = hsv_colors[idx]

            h = target_hsv[0]
            s = hsv[1]  # Preserve original saturation
            v = hsv[2]  # Preserve original brightness/lightness

            new_rgb = hsv_to_rgb((h, s, v))
            color_map[orig_rgb] = new_rgb

    return color_map



def generate_color_map(unique_colors, seed=None, palette=None):
    # fallback basic color map
    if seed is not None:
        random.seed(seed)

    color_map = {}
    used_palette = []

    if palette:
        palette = [tuple(p) for p in palette]
        if len(palette) < len(unique_colors):
            raise ValueError("Palette does not have enough colors for all unique values.")

    for i, color in enumerate(unique_colors):
        if palette:
            new_color = palette[i]
        else:
            new_color = tuple(random.choices(range(256), k=3))

        color_map[tuple(color)] = new_color
        used_palette.append(new_color)

    return color_map


def apply_color_map(img_array, color_map, background_color=None):
    recolor_array = np.copy(img_array)
    for old_color, new_color in color_map.items():
        if background_color and old_color == background_color:
            continue
        mask = np.all(img_array == old_color, axis=-1)
        recolor_array[mask] = new_color
    return recolor_array


def recolor_image(input_path, output_path, color_map):
    original_img = Image.open(input_path)
    img_array = np.array(original_img)
    background_color = tuple(img_array[0, 0])
    recolor_array = apply_color_map(img_array, color_map, background_color)
    recolored_img = Image.fromarray(recolor_array)
    recolored_img.save(output_path)
    print(f"✅ Saved: {output_path}")


def extract_unique_colors_from_image(image_path, ignore_background=True):
    img = Image.open(image_path)
    img_array = np.array(img)
    flat = img_array.reshape(-1, img_array.shape[2])

    if ignore_background:
        background_color = tuple(img_array[0, 0])
        flat = flat[np.any(flat != background_color, axis=1)]

    return np.unique(flat, axis=0)


def load_palette_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    palette = [tuple(map(int, line.strip().split(','))) for line in lines if line.strip()]
    return palette


def save_color_map(color_map, output_path):
    with open(output_path, 'w') as f:
        json.dump({str(k): v for k, v in color_map.items()}, f)


def load_color_map(input_path):
    with open(input_path, 'r') as f:
        data = json.load(f)
    return {eval(k): tuple(v) for k, v in data.items()}


def recolor_folder(input_folder, output_folder, color_map):
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".bmp", ".png", ".jpg")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            recolor_image(input_path, output_path, color_map)
