# Steggo Script / Chips Maker Pro

> **Created by Alexander Belmont, Gemini and Grok**

A desktop application for generating and decoding text chips and steganographic images using three encoding codecs:
1. **DCT Steganography (Стего)** — Invisible data embedding in 8x8 DCT spectrum blocks across RGB channels.
2. **Braille Code (Брайль)** — Auto-wrapped 6-dot Braille cell grids with loss-free roundtrip decoding.
3. **Morse Code (Морзе)** — Continuous wrapped Morse mark/space signal rendering.

---

## 🚀 Options to Run

### Option 1: Standalone Portable EXE (Windows)
No Python installation or dependencies required.

* **File:** `dist/SteggoScriptPro.exe` (or download from [GitHub Releases](../../releases))
* Simply double-click `SteggoScriptPro.exe` to run.

### Option 2: Run from Python Source Code
If you want to modify, customize, or inspect the source code:

1. Clone or download the repository:
   ```bash
   git clone https://github.com/Limmweb/steggo-script-pro.git
   cd steggo-script-pro
   ```
2. Install required dependencies:
   ```bash
   pip install pillow numpy scipy
   ```
3. Run the application:
   ```bash
   python main.py
   ```

---

## 🛡️ Antivirus Check & Security Verification

The compiled `SteggoScriptPro.exe` has been verified with **Windows Defender** and found **0 threats**.

* **SHA-256 Checksum:** `6d0a82984b45eb5afe816eaf1aa25d463adc450f881cea86026161c47490a036`
* **Scan Result:** Clean (0 / 0 threats found)

### How to verify the file checksum yourself:
In Windows PowerShell, run:
```powershell
Get-FileHash .\dist\SteggoScriptPro.exe -Algorithm SHA256
```
Compare the output hash with the SHA-256 string above or upload to [VirusTotal](https://www.virustotal.com/) for complete multi-engine verification.

---

## 📄 License & Attribution

Created collaboratively by **Alexander Belmont**, **Gemini**, and **Grok**.
Free to use, modify, and distribute.
