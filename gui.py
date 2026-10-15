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
from writers import MODE_LABELS, build_image, canvas_size

I18N = {
    "ru": {
        "app_title": "Steggo Script / Chips Maker",
        "codec_label": "Режим кодирования:",
        "codecs": {"stego": "Стего", "braille": "Брайль", "morse": "Морзе", "qr": "QR-код"},
        "header_cb": "Включить контрольную строку (инструкция для ИИ)",
        "text_label": "Текст для кодирования:",
        "btn_create": "СОЗДАТЬ",
        "chip_size": "Размер чипа: {w}x{h} px",
        "error_fmt": "Ошибка: {err}",
        "warn_title": "Внимание",
        "warn_no_text": "Введите текст для кодирования.",
        "save_title": "Сохранить стегго-чип",
        "success_title": "Успех",
        "success_msg": "Изображение успешно сохранено:\n{path}",
        "error_title": "Ошибка",
        "error_save": "Не удалось создать файл:\n{err}",
        "footer": "By Alexander Belmont, Gemini and Grok",
    },
    "en": {
        "app_title": "Steggo Script / Chips Maker",
        "codec_label": "Encoding Mode:",
        "codecs": {"stego": "Stego", "braille": "Braille", "morse": "Morse", "qr": "QR Code"},
        "header_cb": "Include control line (AI instruction)",
        "text_label": "Text to encode:",
        "btn_create": "CREATE",
        "chip_size": "Chip size: {w}x{h} px",
        "error_fmt": "Error: {err}",
        "warn_title": "Warning",
        "warn_no_text": "Please enter text to encode.",
        "save_title": "Save steggo chip",
        "success_title": "Success",
        "success_msg": "Image saved successfully:\n{path}",
        "error_title": "Error",
        "error_save": "Failed to save file:\n{err}",
        "footer": "By Alexander Belmont, Gemini and Grok",
    },
}


class SteggoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang_var = tk.StringVar(value="ru")
        
        self.title(I18N["ru"]["app_title"])
        self.geometry("840x700")
        self.configure(bg=BG_COLOR)

        self.current_image = None
        self.tk_image = None

        self._create_widgets()
        self._update_language()

    def _create_widgets(self):
        # Top frame for controls
        top_frame = tk.Frame(self, bg=BG_COLOR, padx=10, pady=10)
        top_frame.pack(fill=tk.X, side=tk.TOP)

        # Row 0: Codec Selection & Language Switcher
        self.lbl_codec = tk.Label(top_frame, text="", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold"))
        self.lbl_codec.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.codec_var = tk.StringVar(value="stego")
        self.rb_codecs = {}
        for idx, code in enumerate(["stego", "braille", "morse", "qr"]):
            rb = tk.Radiobutton(
                top_frame,
                text="",
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
            self.rb_codecs[code] = rb

        # Language Toggle Frame on the right
        lang_frame = tk.Frame(top_frame, bg=BG_COLOR)
        lang_frame.grid(row=0, column=5, sticky=tk.E, padx=(20, 5), pady=5)
        top_frame.columnconfigure(5, weight=1)

        self.rb_ru = tk.Radiobutton(
            lang_frame,
            text="RU",
            value="ru",
            variable=self.lang_var,
            indicatoron=False,
            bg=ENTRY_BG,
            fg=FG_COLOR,
            selectcolor=ACCENT_PINK,
            activebackground=ACCENT_PINK,
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
            bd=0,
            command=self._update_language
        )
        self.rb_ru.pack(side=tk.LEFT, padx=2)

        self.rb_en = tk.Radiobutton(
            lang_frame,
            text="EN",
            value="en",
            variable=self.lang_var,
            indicatoron=False,
            bg=ENTRY_BG,
            fg=FG_COLOR,
            selectcolor=ACCENT_PINK,
            activebackground=ACCENT_PINK,
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=2,
            bd=0,
            command=self._update_language
        )
        self.rb_en.pack(side=tk.LEFT, padx=2)

        # Row 1: Header Checkbox
        self.header_var = tk.BooleanVar(value=True)
        self.cb_header = tk.Checkbutton(
            top_frame,
            text="",
            variable=self.header_var,
            bg=BG_COLOR,
            fg=FG_COLOR,
            selectcolor=ENTRY_BG,
            activebackground=BG_COLOR,
            activeforeground=ACCENT_PINK,
            font=("Segoe UI", 9),
            command=self._on_input_change
        )
        self.cb_header.grid(row=1, column=0, columnspan=5, sticky=tk.W, padx=5, pady=5)

        # Text input area
        input_frame = tk.Frame(self, bg=BG_COLOR, padx=10, pady=5)
        input_frame.pack(fill=tk.X, side=tk.TOP)

        self.lbl_text_editor = tk.Label(input_frame, text="", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold"))
        self.lbl_text_editor.pack(anchor=tk.W, pady=(0, 5))
        
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
            text="",
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
        
        self.lbl_footer = tk.Label(
            footer_frame,
            text="",
            bg=BG_COLOR,
            fg="#888888",
            font=("Segoe UI", 9, "italic")
        )
        self.lbl_footer.pack(side=tk.RIGHT, padx=15)

    def _update_language(self):
        lang = self.lang_var.get()
        t = I18N.get(lang, I18N["ru"])

        self.title(t["app_title"])
        self.lbl_codec.config(text=t["codec_label"])
        
        for code, rb in self.rb_codecs.items():
            rb.config(text=t["codecs"][code])
            
        self.cb_header.config(text=t["header_cb"])
        self.lbl_text_editor.config(text=t["text_label"])
        self.btn_create.config(text=t["btn_create"])
        self.lbl_footer.config(text=t["footer"])

        self._on_input_change()

    def _on_input_change(self):
        text = self.text_editor.get("1.0", tk.END).strip()
        lang = self.lang_var.get()
        t = I18N.get(lang, I18N["ru"])

        if not text:
            self.lbl_info.config(text="")
            self.canvas_lbl.config(image="")
            self.current_image = None
            return

        codec = self.codec_var.get()
        with_hdr = self.header_var.get()

        try:
            w, h = canvas_size(codec, text, with_header=with_hdr)
            self.lbl_info.config(text=t["chip_size"].format(w=w, h=h))
            
            # Generate preview image
            img = build_image(codec, text, with_header=with_hdr)
            self.current_image = img

            # Scale for preview canvas
            preview_img = img.copy()
            preview_img.thumbnail((280, 280), Image.NEAREST if w < 100 else Image.BICUBIC)
            
            self.tk_image = ImageTk.PhotoImage(preview_img)
            self.canvas_lbl.config(image=self.tk_image)
        except Exception as err:
            self.lbl_info.config(text=t["error_fmt"].format(err=err))

    def _generate_and_save(self):
        text = self.text_editor.get("1.0", tk.END).strip()
        lang = self.lang_var.get()
        t = I18N.get(lang, I18N["ru"])

        if not text:
            messagebox.showwarning(t["warn_title"], t["warn_no_text"])
            return

        codec = self.codec_var.get()
        with_hdr = self.header_var.get()

        try:
            img = build_image(codec, text, with_header=with_hdr)
            w, h = img.size
            
            default_name = f"{sanitize_filename(text)}_{codec}_{w}x{h}.png"
            save_path = filedialog.asksaveasfilename(
                title=t["save_title"],
                initialfile=default_name,
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
            )

            if save_path:
                img.save(save_path)
                messagebox.showinfo(t["success_title"], t["success_msg"].format(path=save_path))
        except Exception as err:
            messagebox.showerror(t["error_title"], t["error_save"].format(err=err))


if __name__ == "__main__":
    app = SteggoApp()
    app.mainloop()
