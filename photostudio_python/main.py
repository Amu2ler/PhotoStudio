# photostudio_python/main.py
import os
import platform
import subprocess

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from customtkinter import CTkImage
import time


class PhotoStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PhotoStudio • Huffman Edition")
        self.geometry("900x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.current_image_path = None
        self.current_image = None
        self.current_ctk_image = None

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # panneau de gauche
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_rowconfigure(10, weight=1)

        title_label = ctk.CTkLabel(
            sidebar,
            text="PhotoStudio",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        subtitle_label = ctk.CTkLabel(
            sidebar,
            text="Edition + Compression Huffman",
            font=ctk.CTkFont(size=12)
        )
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # boutons fichier
        btn_open = ctk.CTkButton(
            sidebar,
            text="📂 Ouvrir une image",
            command=self.open_image
        )
        btn_open.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        btn_save = ctk.CTkButton(
            sidebar,
            text="💾 Enregistrer sous",
            command=self.save_image_as
        )
        btn_save.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # section filtres
        filter_label = ctk.CTkLabel(
            sidebar,
            text="Filtres",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        filter_label.grid(row=4, column=0, padx=20, pady=(20, 5), sticky="w")

        self.filter_combo = ctk.CTkComboBox(
            sidebar,
            values=[
                "Grayscale",
                "Sepia",
                "Negative",
                "Blur",
                "Sharpen",
                "Edge Enhance",
                "Brightness+",
                "Brightness-",
            ]
        )
        self.filter_combo.set("Grayscale")
        self.filter_combo.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        btn_apply_filter = ctk.CTkButton(
            sidebar,
            text="🎨 Appliquer le filtre",
            command=self.apply_selected_filter
        )
        btn_apply_filter.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # section compression
        comp_label = ctk.CTkLabel(
            sidebar,
            text="Compression Huffman",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        comp_label.grid(row=7, column=0, padx=20, pady=(20, 5), sticky="w")

        btn_compress = ctk.CTkButton(
            sidebar,
            text="🗜️ Compresser l'image",
            command=self.compress_current_image
        )
        btn_compress.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        btn_decompress = ctk.CTkButton(
            sidebar,
            text="📦 Décompresser un fichier",
            command=self.decompress_file
        )
        btn_decompress.grid(row=9, column=0, padx=20, pady=5, sticky="ew")

        # panneau preview
        preview_frame = ctk.CTkFrame(self)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Aucune image chargée",
            anchor="center"
        )
        self.preview_label.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    # ---------- IMG HANDLING ----------
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Choisir une image",
            filetypes=[("Images PNG", "*.png"), ("Toutes les images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not path:
            return

        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'image :\n{e}")
            return

        self.current_image_path = path
        self.current_image = img
        self._update_preview()

    def _update_preview(self):
        if self.current_image is None:
            self.preview_label.configure(text="Aucune image chargée", image=None)
            return

        # redimensionner pour la preview
        max_w, max_h = 650, 500
        img_copy = self.current_image.copy()
        img_copy.thumbnail((max_w, max_h))

        self.current_ctk_image = CTkImage(light_image=img_copy, dark_image=img_copy, size=img_copy.size)
        self.preview_label.configure(text="", image=self.current_ctk_image)

    def save_image_as(self):
        if self.current_image is None:
            messagebox.showinfo("Info", "Aucune image à enregistrer.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            title="Enregistrer l'image sous"
        )
        if not path:
            return

        try:
            self.current_image.save(path, format="PNG")
            messagebox.showinfo("Succès", f"Image enregistrée dans :\n{path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer l'image :\n{e}")

    # ---------- FILTERS ----------
    def apply_selected_filter(self):
        if self.current_image is None:
            messagebox.showinfo("Info", "Charge d'abord une image.")
            return

        choice = self.filter_combo.get()
        img = self.current_image

        try:
            if choice == "Grayscale":
                img = ImageOps.grayscale(img).convert("RGB")
            elif choice == "Sepia":
                gray = ImageOps.grayscale(img)
                img = ImageOps.colorize(gray, "#704214", "#C0C090").convert("RGB")
            elif choice == "Negative":
                img = ImageOps.invert(img)
            elif choice == "Blur":
                img = img.filter(ImageFilter.GaussianBlur(radius=2))
            elif choice == "Sharpen":
                img = img.filter(ImageFilter.SHARPEN)
            elif choice == "Edge Enhance":
                img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            elif choice == "Brightness+":
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.3)
            elif choice == "Brightness-":
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(0.7)

            self.current_image = img
            self._update_preview()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application du filtre :\n{e}")

    # ---------- HUFFMAN C ----------
    def _get_huff_binary(self):
        # binaire 'huff' dans ../compressor_c
        base_dir = os.path.dirname(os.path.abspath(__file__))
        proj_root = os.path.dirname(base_dir)
        huff_path = os.path.join(proj_root, "compressor_c", "huff")

        if platform.system().lower().startswith("win"):
            huff_path += ".exe"

        return huff_path

    def compress_current_image(self):
        if self.current_image_path is None:
            messagebox.showinfo("Info", "Charge d'abord une image à compresser.")
            return

        huff = self._get_huff_binary()
        if not os.path.exists(huff):
            messagebox.showerror(
                "Erreur",
                f"Programme C introuvable.\nCompile-le d'abord dans 'compressor_c' avec 'make'."
            )
            return

        default_name = os.path.splitext(os.path.basename(self.current_image_path))[0] + ".huff"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".huff",
            filetypes=[("Fichiers Huffman", "*.huff"), ("Tous les fichiers", "*.*")],
            initialfile=default_name,
            title="Enregistrer le fichier compressé sous"
        )
        if not out_path:
            return

        try:
            start = time.perf_counter()

            result = subprocess.run(
                [huff, "c", self.current_image_path, out_path],
                capture_output=True,
                text=True
            )

            elapsed = (time.perf_counter() - start) * 1000  # ms
            if result.returncode != 0:
                messagebox.showerror(
                    "Erreur de compression",
                    f"Le programme C a retourné un code d'erreur.\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
                )
            else:
                # --- NEW: calculate compression stats ---
                try:
                    original_size = os.path.getsize(self.current_image_path)
                    compressed_size = os.path.getsize(out_path)

                    reduction = 100 * (1 - compressed_size / original_size)

                    def human(n):
                        for unit in ["B", "KB", "MB", "GB"]:
                            if n < 1024:
                                return f"{n:.2f} {unit}"
                            n /= 1024
                        return f"{n:.2f} TB"

                    report = (
                        "Compression Report\n"
                        "-------------------------\n"
                        f"Original size   : {human(original_size)}\n"
                        f"Compressed size : {human(compressed_size)}\n"
                        f"Reduction       : {reduction:.2f}%\n"
                        f"Time taken      : {elapsed:.2f} ms\n"
                    )


                    messagebox.showinfo("Compression réussie", report)

                except Exception as e:
                    messagebox.showinfo(
                        "Succès",
                        f"Image compressée dans :\n{out_path}\n\n(Impossible de calculer les stats : {e})"
                    )
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exécuter le compresseur C :\n{e}")

    def decompress_file(self):
        huff = self._get_huff_binary()
        if not os.path.exists(huff):
            messagebox.showerror(
                "Erreur",
                f"Programme C introuvable.\nCompile-le d'abord dans 'compressor_c' avec 'make'."
            )
            return

        in_path = filedialog.askopenfilename(
            title="Choisir un fichier compressé (.huff)",
            filetypes=[("Fichiers Huffman", "*.huff"), ("Tous les fichiers", "*.*")]
        )
        if not in_path:
            return

        default_name = os.path.splitext(os.path.basename(in_path))[0] + "_decompressed.png"
        out_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Tous les fichiers", "*.*")],
            initialfile=default_name,
            title="Enregistrer l'image décompressée sous"
        )
        if not out_path:
            return

        try:
            result = subprocess.run(
                [huff, "d", in_path, out_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                messagebox.showerror(
                    "Erreur de décompression",
                    f"Le programme C a retourné un code d'erreur.\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
                )
            else:
                messagebox.showinfo("Succès", f"Image décompressée avec succès dans :\n{out_path}")
                # Optionnel : charger directement l'image décompressée
                try:
                    img = Image.open(out_path).convert("RGB")
                    self.current_image_path = out_path
                    self.current_image = img
                    self._update_preview()
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exécuter le décompresseur C :\n{e}")


if __name__ == "__main__":
    app = PhotoStudioApp()
    app.mainloop()
