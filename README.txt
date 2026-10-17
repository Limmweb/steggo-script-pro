==============================================================================
STEGGO SCRIPT / CHIPS MAKER PRO
Created by Alexander Belmont, Gemini and Grok
==============================================================================

Это универсальная программа для создания Чипсов — шифрованных файлов для общения с нейросетями.

A universal desktop application for generating and decoding text chips and 
steganographic images for secure communication with AI neural networks using 
four distinct encoding modes:

1. DCT Steganography (Stego) - Invisible data embedding in 8x8 DCT spectrum 
   blocks across RGB channels.
2. Braille Code (Braille) - Auto-wrapped 6-dot Braille cell grids with 
   loss-free roundtrip decoding.
3. Morse Code (Morse) - Continuous wrapped Morse mark/space signal rendering.
4. QR Code Steganography (QR Code) - Direct high-density QR code chip rendering 
   with automatic error correction and decoding.

------------------------------------------------------------------------------
DOWNLOADS (WINDOWS)
------------------------------------------------------------------------------

* SteggoScriptPro_v1.0.0.zip (Executable + Readmes):
  https://github.com/Limmweb/steggo-script-pro/releases/download/v1.0.0/SteggoScriptPro_v1.0.0.zip

* SteggoScriptPro.exe (Standalone Executable):
  https://github.com/Limmweb/steggo-script-pro/releases/download/v1.0.0/SteggoScriptPro.exe

------------------------------------------------------------------------------
OPTIONS TO RUN
------------------------------------------------------------------------------

Option 1: Standalone Portable EXE / ZIP (Windows)
1. Download SteggoScriptPro_v1.0.0.zip or SteggoScriptPro.exe from the links above.
2. Extract the archive (if ZIP) and run SteggoScriptPro.exe. No installation required.

Option 2: Run from Python Source Code
If you want to modify or inspect the source code:

1. Clone or download the repository:
   git clone https://github.com/Limmweb/steggo-script-pro.git
   cd steggo-script-pro

2. Install required dependencies:
   pip install pillow numpy scipy opencv-python qrcode

3. Run the application:
   python main.py

------------------------------------------------------------------------------
ANTIVIRUS CHECK & SECURITY VERIFICATION
------------------------------------------------------------------------------

The compiled SteggoScriptPro.exe has been verified with Windows Defender 
and found 0 threats.

* SHA-256 Checksum: 6d0a82984b45eb5afe816eaf1aa25d463adc450f881cea86026161c47490a036
* Scan Result: Clean (0 / 0 threats found)

How to verify the file checksum yourself:
In Windows PowerShell, run:
   Get-FileHash .\SteggoScriptPro.exe -Algorithm SHA256

Compare the output hash with the SHA-256 string above or upload to VirusTotal
(https://www.virustotal.com/) for complete multi-engine verification.

------------------------------------------------------------------------------
LICENSE & ATTRIBUTION
------------------------------------------------------------------------------

Created collaboratively by Alexander Belmont, Gemini, and Grok.
Free to use, modify, and distribute.
