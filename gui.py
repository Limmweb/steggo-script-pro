# gui.py
# Steggo Script Pro - GUI Implementation
# Created by Alexander Belmont, Gemini and Grok

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from PIL import Image, ImageTk

from style import ACCENT_PINK, BG_COLOR, BTN_ACTIVE_PINK, ENTRY_BG, FG_COLOR, TEXT_FG
from utils import sanitize_filename
from writers import MODE_LABELS, build_image, build_image_info, canvas_size


class SoraStegoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steggo Script / Chips Maker — By Alexander Belmont, Gemini and Grok")
        self.geometry("820x700")
        self.configure(bg=BG_COLOR)

        self.current_image = None
        self.tk_image = None

        self._create_widgets()

    def _create_widgets(self):
        # Top frame for controls
        top_frame = tk.Frame(self, bg=BG_COLOR, padx=10, pady=10)
        top_frame.pack(fill=tk.X, side=tk.TOP)

        # Codec Selection
        tk.Label(top_frame, text="Режим кодирования:", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.codec_var = tk.StringVar(value="stego")
        for idx, (code, label) in enumerate(MODE_LABELS.items()):
            rb = tk.Radiobutton(
                top_frame,
                text=label,
                value=code,
                variable=self.codec_var,
                bg=BG_COLOR,
                fg=FG_COLOR,
                selectcolor=ENTRY_BG,
                activebackground=BG_COLOR,
                activeforeground=ACCENT_PINK,
                font=("Segoe UI", 10),
                command=self._on_input_change
            )
            rb.grid(row=0, column=1 + idx, padx=5, pady=5, sticky=tk.W)

        # Header Checkbox
        self.header_var = tk.BooleanVar(value=True)
        cb_header = tk.Checkbutton(
            top_frame,
            text="Включить контрольную строку (инструкция для ИИ)",
            variable=self.header_var,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=ACCENT_PINK,
            font=("Segoe UI", 9),
            command=self._on_input_change
        )
        cb_header.grid(row=1, column=0, columnspan=4, sticky=tk.W, padx=5, pady=5)

        # Text input area
        input_frame = tk.Frame(self, bg=BG_COLOR, padx=10, pady=5)
        input_frame.pack(fill=tk.X, side=tk.TOP)

        tk.Label(input_frame, text="Текст для кодирования:", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.text_editor = ScrolledText(
            input_frame,
            height=11,
            bg=ENTRY_BG,
            fg=TEXT_FG,
            insertbackground=FG_COLOR,
            font=("Consolas", 10),
            relief=tk.FLAT,
            bd=2
        )
        self.text_editor.pack(fill=tk.X, expand=True)
        self.text_editor.bind("<KeyRelease>", lambda e: self._on_input_change())

        # Action Buttons
        btn_frame = tk.Frame(self, bg=BG_COLOR, padx=10, pady=8)
        btn_frame.pack(fill=tk.X, side=tk.TOP)

        self.btn_create = tk.Button(
            btn_frame,
            text="« СОЗДАТЬ »",
            bg=ACCENT_PINK,
            fg="#ffffff",
            activebackground=BTN_ACTIVE_PINK,
            activeforeground="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self._generate_and_save
        )
        self.btn_create.pack(side=tk.LEFT, padx=5)

        # Info Label
        self.lbl_info = tk.Label(btn_frame, text="", bg=BG_COLOR, fg=ACCENT_PINK, font=("Segoe UI", 9, "bold"))
        self.lbl_info.pack(side=tk.LEFT, padx=15)

        # Image Preview Frame
        preview_frame = tk.Frame(self, bg=ENTRY_BG, bd=1, relief=tk.SOLID)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(5, 5))

        self.canvas_lbl = tk.Label(preview_frame, bg=ENTRY_BG)
        self.canvas_lbl.pack(fill=tk.BOTH, expand=True)

        # Attribution Footer Bar
        footer_frame = tk.Frame(self, bg=BG_COLOR, pady=5)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        lbl_footer = tk.Label(
            footer_frame,
            text="By Alexander Belmont, Gemini and Grok",
            bg=BG_COLOR,
            fg="#888888",
            font=("Segoe UI", 9, "italic")
        )
        lbl_footer.pack(side=tk.RIGHT, padx=15)

    def _on_input_change(self):
        text = self.text_editor.get("1.0", tk.END).strip()
        if not text:
            self.lbl_info.config(text="")
            self.canvas_lbl.config(image="")
            self.current_image = None
            return

        codec = self.codec_var.get()
        with_hdr = self.header_var.get()

        try:
            w, h = canvas_size(codec, text, with_header=with_hdr)
            self.lbl_info.config(text=f"Размер чипа: {w}x{h} px")
            
            # Generate preview image
            img = build_image(codec, text, with_header=with_hdr)
            self.current_image = img

            # Scale for preview canvas
            preview_img = img.copy()
            preview_img.thumbnail((280, 280), Image.NEAREST if w < 100 else Image.BICUBIC)
            
            self.tk_image = ImageTk.PhotoImage(preview_img)
            self.canvas_lbl.config(image=self.tk_image)
        except Exception as err:
            self.lbl_info.config(text=f"Ошибка: {err}")

    def _generate_and_save(self):
        text = self.text_editor.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Внимание", "Введите текст для кодирования.")
            return

        codec = self.codec_var.get()
        with_hdr = self.header_var.get()

        try:
            img = build_image(codec, text, with_header=with_hdr)
            w, h = img.size
            
            default_name = f"{sanitize_filename(text)}_{codec}_{w}x{h}.png"
            save_path = filedialog.asksaveasfilename(
                title="Сохранить стегго-чип",
                initialfile=default_name,
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
            )

            if save_path:
                img.save(save_path)
                messagebox.showinfo("Успех", f"Изображение успешно сохранено:\n{save_path}")
        except Exception as err:
            messagebox.showerror("Ошибка", f"Не удалось создать файл:\n{err}")


if __name__ == "__main__":
    app = SoraStegoApp()
    app.mainloop()
