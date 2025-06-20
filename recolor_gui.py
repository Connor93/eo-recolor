import tkinter as tk
from tkinter import filedialog, colorchooser
from tkinter import ttk
import os
from PIL import Image, ImageTk
import numpy as np

from advanced_recolor import (
    recolor_image, recolor_folder,
    extract_unique_colors_from_image,
    generate_smart_color_map,
    generate_color_map,
    load_color_map,
    save_color_map,
    load_palette_file,
    apply_color_map,
    generate_color_scheme_palette
)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

class RecolorApp:
    def __init__(self, root):
        self.root = root
        root.title("Image Recoloring Tool with Schemes")

        tk.Label(root, text="Input (File or Folder):").grid(row=0, column=0, sticky="w")
        self.input_entry = tk.Entry(root, width=50)
        self.input_entry.grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.browse_input).grid(row=0, column=2)

        tk.Label(root, text="Output (File or Folder):").grid(row=1, column=0, sticky="w")
        self.output_entry = tk.Entry(root, width=50)
        self.output_entry.grid(row=1, column=1)
        tk.Button(root, text="Browse", command=self.browse_output).grid(row=1, column=2)

        tk.Label(root, text="Random Seed (Optional):").grid(row=2, column=0, sticky="w")
        self.seed_entry = tk.Entry(root)
        self.seed_entry.grid(row=2, column=1)

        tk.Label(root, text="Color Scheme:").grid(row=3, column=0, sticky="w")
        self.scheme_var = tk.StringVar(value="random")
        self.scheme_menu = ttk.Combobox(root, textvariable=self.scheme_var, state="readonly",
                                        values=["random", "complementary", "analogous", "triadic", "monochrome"])
        self.scheme_menu.grid(row=3, column=1, sticky="w")

        tk.Label(root, text="Base Color (Hex, Optional):").grid(row=4, column=0, sticky="w")
        self.color_entry = tk.Entry(root)
        self.color_entry.grid(row=4, column=1, sticky="w")
        tk.Button(root, text="Pick", command=self.pick_color).grid(row=4, column=2)

        self.preview_label = tk.Label(root, text="Palette Preview:")
        self.preview_label.grid(row=5, column=0, sticky="nw")
        self.palette_canvas = tk.Canvas(root, width=250, height=30, bg="white")
        self.palette_canvas.grid(row=5, column=1, columnspan=2, sticky="w")

        self.orig_label = tk.Label(root, text="Original Preview")
        self.orig_label.grid(row=6, column=0, sticky="nw")
        self.orig_canvas = tk.Canvas(root, width=200, height=200, bg="gray")
        self.orig_canvas.grid(row=6, column=1, sticky="w")

        self.recolor_label = tk.Label(root, text="Recolored Preview")
        self.recolor_label.grid(row=6, column=2, sticky="nw")
        self.recolor_canvas = tk.Canvas(root, width=200, height=200, bg="gray")
        self.recolor_canvas.grid(row=6, column=3, sticky="w")

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=7, column=0, columnspan=4, pady=5)

        self.run_button = tk.Button(root, text="🎨 Recolor", command=self.run_recolor)
        self.run_button.grid(row=8, column=0, columnspan=4, pady=10)

        self.status = tk.Label(root, text="", fg="green")
        self.status.grid(row=9, column=0, columnspan=4)

    def pick_color(self):
        color = colorchooser.askcolor(title="Choose Base Color")
        if color[1]:
            self.color_entry.delete(0, tk.END)
            self.color_entry.insert(0, color[1])

    def browse_input(self):
        path = filedialog.askopenfilename(title="Select File") or filedialog.askdirectory(title="Select Folder")
        if path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, path)
            self.load_original_preview()

    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".bmp") if os.path.isfile(self.input_entry.get()) \
               else filedialog.askdirectory(title="Select Folder")
        if path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, path)

    def load_original_preview(self):
        path = self.input_entry.get()
        if os.path.isfile(path):
            try:
                img = Image.open(path)
                img.thumbnail((200, 200))
                self.tk_img = ImageTk.PhotoImage(img)
                self.orig_canvas.delete("all")
                self.orig_canvas.create_image(100, 100, image=self.tk_img)
            except:
                pass

    def draw_palette_preview(self, colors):
        self.palette_canvas.delete("all")
        swatch_width = 25
        for i, rgb in enumerate(colors[:10]):
            hex_color = rgb_to_hex(rgb)
            x0 = i * swatch_width
            self.palette_canvas.create_rectangle(x0, 0, x0 + swatch_width, 30, fill=hex_color, outline="black")

    def run_recolor(self):
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()
        scheme = self.scheme_var.get()
        base_hex = self.color_entry.get().strip()
        base_rgb = None
        if base_hex:
            try:
                base_rgb = hex_to_rgb(base_hex)
            except:
                self.status.config(text="Invalid base color hex.", fg="red")
                return

        seed = self.seed_entry.get()
        seed = int(seed) if seed.isdigit() else None

        try:
            if os.path.isdir(input_path):
                files = [f for f in os.listdir(input_path) if f.lower().endswith((".bmp", ".png", ".jpg"))]
                self.progress["value"] = 0
                self.progress["maximum"] = len(files)
                unique_colors = extract_unique_colors_from_image(os.path.join(input_path, files[0]))

                color_map = generate_smart_color_map(unique_colors, seed=seed, base_rgb=base_rgb, scheme=scheme if scheme != "random" else None)
                self.draw_palette_preview(list(color_map.values()))

                for i, file in enumerate(files):
                    recolor_image(os.path.join(input_path, file), os.path.join(output_path, file), color_map)
                    self.progress["value"] = i + 1
                    self.root.update_idletasks()

            else:
                unique_colors = extract_unique_colors_from_image(input_path)
                color_map = generate_smart_color_map(unique_colors, seed=seed, base_rgb=base_rgb, scheme=scheme if scheme != "random" else None)
                self.draw_palette_preview(list(color_map.values()))

                img = Image.open(input_path)
                arr = np.array(img)
                recolored = apply_color_map(arr, color_map, background_color=tuple(arr[0, 0]))
                out_img = Image.fromarray(recolored)
                out_img.save(output_path)
                out_img.thumbnail((200, 200))
                self.tk_recolor = ImageTk.PhotoImage(out_img)
                self.recolor_canvas.delete("all")
                self.recolor_canvas.create_image(100, 100, image=self.tk_recolor)
                self.progress["value"] = 100

            self.status.config(text="✅ Done!", fg="green")
        except Exception as e:
            self.status.config(text=f"❌ Error: {e}", fg="red")
            self.progress["value"] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = RecolorApp(root)
    root.mainloop()
