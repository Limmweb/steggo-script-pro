# writers.py
import functools
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.fftpack import dct, idct

from core import POSITIONS
from utils import get_optimal_size

CONTROL_BRAILLE = "This is Braile font written text, read it left to right, top to bottom"
CONTROL_STEGO = (
    "DCT stego. Data fills the square below this line, full width, left to right, top to bottom. "
    "Blocks 8x8, step 8, channels R G B. "
    "8 DCT coeffs per channel, order (1,2) (2,1) (3,0) (0,3) (1,3) (2,2) (3,1) (4,0). "
    "Density 3 bytes per block. Bit 1 = +360, bit 0 = -360, read the sign. "
    "First 16 bits = UTF-8 byte length, MSB first, then the text."
)
CONTROL_MORSE = (
    "This is Morse code, read left to right, top to bottom, the next row continues. "
    "Dot is 1 unit, dash is 3. Gap inside a letter is 1, between letters 3, between words 7, "
    "a new text line is 11. Capital prefix is ..-.- , yo is ..--. , "
    "opening quote is -..-.- , closing quote is --..-. ."
)
CONTROLS = {
    "stego": CONTROL_STEGO,
    "braille": CONTROL_BRAILLE,
    "morse": CONTROL_MORSE,
}
MODE_LABELS = {"stego": "Стего", "braille": "Брайль", "morse": "Морзе"}

HEADER_MAX_RATIO = 0.20
HEADER_FONT_MIN = 6
HEADER_FONT_MAX = 28
READABLE_FONT = 11
PAD_X = 6
PAD_Y = 4
RULE = 2

MIN_CELL_W = 8
MIN_CELL_H = 12
BRAILLE_MARGIN = 3

MIN_UNIT = 3
MORSE_ROW_GAP = 2
MORSE_MARGIN = 3
NEWLINE_UNITS = 11

CAPITAL_DOTS = (4, 5)
NUMBER_DOTS = (3, 4, 5, 6)
CAPITAL_PREFIX = "..-.-"


def _cell(dots):
    bits = 0
    for dot in dots:
        bits |= 1 << (dot - 1)
    return chr(0x2800 + bits)


CAPITAL_SIGN = _cell(CAPITAL_DOTS)
NUMBER_SIGN = _cell(NUMBER_DOTS)

BRAILLE_LETTERS = {
    "а": (1,), "б": (1, 2), "в": (2, 4, 5, 6), "г": (1, 2, 4, 5),
    "д": (1, 4, 5), "е": (1, 5), "ё": (1, 6), "ж": (2, 4, 5),
    "з": (1, 3, 5, 6), "и": (2, 4), "й": (1, 2, 3, 4, 6), "к": (1, 3),
    "л": (1, 2, 3), "м": (1, 3, 4), "н": (1, 3, 4, 5), "о": (1, 3, 5),
    "п": (1, 2, 3, 4), "р": (1, 2, 3, 5), "с": (2, 3, 4), "т": (2, 3, 4, 5),
    "у": (1, 3, 6), "ф": (1, 2, 4), "х": (1, 2, 5), "ц": (1, 4),
    "ч": (1, 2, 3, 4, 5), "ш": (1, 5, 6), "щ": (1, 3, 4, 6), "ъ": (1, 2, 3, 5, 6),
    "ы": (2, 3, 4, 6), "ь": (2, 3, 4, 5, 6), "э": (2, 4, 6), "ю": (1, 2, 5, 6),
    "я": (1, 2, 4, 6),
}
BRAILLE_PUNCT = {
    ".": (2, 5, 6), ",": (2,), ":": (2, 5), ";": (2, 3),
    "!": (2, 3, 5), "?": (2, 6), "-": (3, 6), "—": (3, 6), "–": (3, 6),
    "«": (2, 3, 6), "»": (3, 5, 6), '"': (2, 3, 6),
    "(": (1, 2, 6), ")": (3, 4, 5),
}
BRAILLE_LATIN = {
    "a": (1,), "b": (1, 2), "c": (1, 4), "d": (1, 4, 5), "e": (1, 5),
    "f": (1, 2, 4), "g": (1, 2, 4, 5), "h": (1, 2, 5), "i": (2, 4), "j": (2, 4, 5),
    "k": (1, 3), "l": (1, 2, 3), "m": (1, 3, 4), "n": (1, 3, 4, 5), "o": (1, 3, 5),
    "p": (1, 2, 3, 4), "q": (1, 2, 3, 4, 5), "r": (1, 2, 3, 5), "s": (2, 3, 4),
    "t": (2, 3, 4, 5), "u": (1, 3, 6), "v": (1, 2, 3, 6), "w": (2, 4, 5, 6),
    "x": (1, 3, 4, 6), "y": (1, 3, 4, 5, 6), "z": (1, 3, 5, 6),
}
BRAILLE_CHAR = {ch: _cell(dots) for ch, dots in {**BRAILLE_LETTERS, **BRAILLE_LATIN, **BRAILLE_PUNCT}.items()}
BRAILLE_FROM = {}
for _ch, _glyph in BRAILLE_CHAR.items():
    BRAILLE_FROM.setdefault(_glyph, _ch)
DIGIT_CELLS = {str(n): BRAILLE_CHAR["j" if n == 0 else "abcdefghij"[n - 1]] for n in range(10)}
DIGIT_FROM = {glyph: digit for digit, glyph in DIGIT_CELLS.items()}

MORSE_LETTERS = {
    "а": ".-", "б": "-...", "в": ".--", "г": "--.", "д": "-..", "е": ".",
    "ж": "...-", "з": "--..", "и": "..", "й": ".---", "к": "-.-", "л": ".-..",
    "м": "--", "н": "-.", "о": "---", "п": ".--.", "р": ".-.", "с": "...",
    "т": "-", "у": "..-", "ф": "..-.", "х": "....", "ц": "-.-.", "ч": "---.",
    "ш": "----", "щ": "--.-", "ъ": "--.--", "ы": "-.--", "ь": "-..-",
    "э": "..-..", "ю": "..--", "я": ".-.-", "ё": "..--.",
    "a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".", "f": "..-.",
    "g": "--.", "h": "....", "i": "..", "j": ".---", "k": "-.-", "l": ".-..",
    "m": "--", "n": "-.", "o": "---", "p": ".--.", "q": "--.-", "r": ".-.",
    "s": "...", "t": "-", "u": "..-", "v": "...-", "w": ".--", "x": "-..-",
    "y": "-.--", "z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", ":": "---...", ";": "-.-.-.",
    "!": "-.-.--", "?": "..--..", "-": "-....-",
    "(": "-.--.", ")": "-.--.-",
    "«": "-..-.-", "»": "--..-.", '"': ".-..-.",
}
MORSE_FROM = {}
for _ch, _pat in MORSE_LETTERS.items():
    MORSE_FROM.setdefault(_pat, _ch)

@functools.lru_cache(maxsize=128)
def _load_font(size):
    for path in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ):
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


_DUMMY_DRAW = ImageDraw.Draw(Image.new("RGB", (1, 1)))


def _text_width(text, font):
    return _DUMMY_DRAW.textlength(text, font=font)


@functools.lru_cache(maxsize=128)
def _font_word_widths(text, font_size):
    font = _load_font(font_size)
    words = text.split(" ")
    space_w = font.getlength(" ")
    widths = [font.getlength(w) for w in words]
    return words, space_w, widths


def _wrap(text, font, max_width):
    font_size = getattr(font, "size", 12)
    words, space_w, widths = _font_word_widths(text, font_size)
    lines = []
    current_words = []
    current_w = 0.0
    for w, w_len in zip(words, widths):
        added = w_len if not current_words else space_w + w_len
        if current_w + added <= max_width:
            current_words.append(w)
            current_w += added
        else:
            if current_words:
                lines.append(" ".join(current_words))
            current_words = [w]
            current_w = w_len
    if current_words:
        lines.append(" ".join(current_words))
    return lines or [""]


def _fit_header(text, width, max_height):
    inner = max(40, width - PAD_X * 2)
    fallback = None
    for size in range(HEADER_FONT_MAX, HEADER_FONT_MIN - 1, -1):
        font = _load_font(size)
        lines = _wrap(text, font, inner)
        ascent, descent = font.getmetrics()
        line_h = ascent + descent + 1
        header_h = PAD_Y + line_h * max(1, len(lines)) + PAD_Y + RULE
        fallback = (font, lines, line_h, header_h)
        if " ".join(lines) == text and header_h <= max_height:
            return font, lines, line_h, header_h
    return fallback


def _paint_header(image, lines, font, line_h, header_h):
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    y = PAD_Y
    for line in lines:
        draw.text((PAD_X, y), line, font=font, fill=(0, 0, 0))
        y += line_h
    draw.rectangle((0, header_h - RULE, image.width, header_h), fill=(0, 0, 0))


def _rect_capacity(width, height):
    blocks_x = (width - 7) // 8
    blocks_y = (height - 7) // 8
    if blocks_x < 1 or blocks_y < 1:
        return 0
    return blocks_x * blocks_y * 3 - 2


def _embed_rect(width, height, text):
    data = text.encode("utf-8")
    bits = [int(b) for b in format(len(data), "016b")]
    for byte in data:
        bits.extend(int(x) for x in format(byte, "08b"))
    signed = [360.0 if bit else -360.0 for bit in bits]
    base = np.full((height, width, 3), 252, dtype=np.uint8)
    noise = np.random.randint(-7, 8, (height, width, 3), dtype=np.int16)
    arr = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.float32)
    idx = 0
    total = len(bits)
    for y in range(0, height - 7, 8):
        for x in range(0, width - 7, 8):
            for ch in range(3):
                if idx >= total:
                    break
                block = arr[y:y + 8, x:x + 8, ch]
                spectrum = dct(dct(block.T, norm="ortho").T, norm="ortho")
                for dy, dx in POSITIONS:
                    if idx >= total:
                        break
                    spectrum[dy, dx] += signed[idx]
                    idx += 1
                arr[y:y + 8, x:x + 8, ch] = idct(idct(spectrum.T, norm="ortho").T, norm="ortho")
            if idx >= total:
                break
        if idx >= total:
            break
    if idx < total:
        raise ValueError("Текст не помещается в квадрат стего")
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


NEWLINE_SIGN = _cell((3, 4, 6))


def _braille_cells(text):
    cells = []
    lines = text.splitlines() if text else [""]
    for line_idx, line in enumerate(lines):
        if line_idx > 0:
            cells.append(NEWLINE_SIGN)
        number_mode = False
        for ch in line:
            if ch == " ":
                cells.append(chr(0x2800))
                number_mode = False
                continue
            if ch.isdigit():
                if not number_mode:
                    cells.append(NUMBER_SIGN)
                    number_mode = True
                cells.append(DIGIT_CELLS[ch])
                continue
            number_mode = False
            lower = ch.lower()
            glyph = BRAILLE_CHAR.get(lower) or BRAILLE_CHAR.get(ch)
            if glyph is None:
                continue
            if (ch.isupper() and lower in BRAILLE_LETTERS) or (ch.isupper() and lower in BRAILLE_LATIN):
                cells.append(CAPITAL_SIGN)
            cells.append(glyph)
    return cells


def _pack_braille_rows(cells, max_cols=None):
    if not cells:
        return [[]]
    N = len(cells)
    if max_cols is None:
        max_cols = max(8, math.ceil(math.sqrt(1.5 * N)))
    rows = []
    curr = []
    for c in cells:
        if len(curr) >= max_cols:
            rows.append(curr)
            curr = []
        curr.append(c)
    if curr:
        rows.append(curr)
    return rows


def _braille_grid(rows, content_w, content_h):
    n_cols = max((len(row) for row in rows), default=1)
    n_rows = max(1, len(rows))
    margin = BRAILLE_MARGIN
    cell_w = MIN_CELL_W
    cell_h = MIN_CELL_H
    diam = max(2, min(cell_w // 3, cell_h // 4))
    radius = diam // 2
    dx = max(diam + 1, (cell_w - diam) // 2)
    dy = max(diam + 1, (cell_h - diam) // 3)
    return {
        "n_cols": n_cols,
        "n_rows": n_rows,
        "margin": margin,
        "cell_w": cell_w,
        "cell_h": cell_h,
        "radius": radius,
        "dx": dx,
        "dy": dy,
    }


def _dot_centers(grid, col, row):
    x0 = grid["margin"] + col * grid["cell_w"] + grid["radius"]
    y0 = grid["margin"] + row * grid["cell_h"] + grid["radius"]
    dx, dy = grid["dx"], grid["dy"]
    return (
        (x0, y0),
        (x0, y0 + dy),
        (x0, y0 + dy * 2),
        (x0 + dx, y0),
        (x0 + dx, y0 + dy),
        (x0 + dx, y0 + dy * 2),
    )


def _render_braille(rows, content_w, content_h):
    grid = _braille_grid(rows, content_w, content_h)
    image = Image.new("RGB", (content_w, content_h), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    radius = grid["radius"]
    for row_i, row in enumerate(rows):
        for col_i, glyph in enumerate(row):
            bits = ord(glyph) - 0x2800
            if bits <= 0:
                continue
            for bit, (cx, cy) in enumerate(_dot_centers(grid, col_i, row_i)):
                if bits & (1 << bit):
                    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(0, 0, 0))
    return image, grid


def _morse_tokens(line):
    tokens = []
    pending_word = False
    started = False
    for ch in line:
        if ch.isspace():
            if started:
                pending_word = True
            continue
        parts = []
        if ch.isupper() and ch.lower() in MORSE_LETTERS and ch.lower() not in "0123456789":
            parts.append(CAPITAL_PREFIX)
        pattern = MORSE_LETTERS.get(ch.lower(), MORSE_LETTERS.get(ch))
        if pattern is None:
            continue
        parts.append(pattern)
        for pattern in parts:
            if started and pending_word:
                tokens.append(("gap", 7))
                pending_word = False
            elif started:
                tokens.append(("gap", 3))
            tokens.append(("mark", pattern))
            started = True
            pending_word = False
    return tokens


def _mark_units(pattern):
    total = 0
    for index, symbol in enumerate(pattern):
        total += 3 if symbol == "-" else 1
        if index != len(pattern) - 1:
            total += 1
    return total


def _morse_groups(text):
    groups = []
    gap = 0
    lines = text.splitlines() or [""]
    for index, line in enumerate(lines):
        if index:
            gap += NEWLINE_UNITS
        for kind, value in _morse_tokens(line):
            if kind == "gap":
                gap += value
            else:
                groups.append((gap, value))
                gap = 0
    return groups


def _group_units(group):
    gap, pattern = group
    return gap + _mark_units(pattern)


def _pack_morse(groups, max_units):
    rows = []
    current = []
    used = 0
    for group in groups:
        need = _group_units(group)
        if current and used + need > max_units:
            rows.append(current)
            current = []
            used = 0
        current.append(group)
        used += need
    if current:
        rows.append(current)
    return rows or [[]]


def _render_morse(rows, content_w, content_h, unit):
    line_h = unit + MORSE_ROW_GAP
    image = Image.new("RGB", (content_w, content_h), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for row_i, groups in enumerate(rows):
        x = MORSE_MARGIN
        y = MORSE_MARGIN + row_i * line_h
        for gap, pattern in groups:
            x += gap * unit
            for index, symbol in enumerate(pattern):
                mark_w = (3 if symbol == "-" else 1) * unit
                draw.rectangle((x, y, x + mark_w - 1, y + unit - 1), fill=(0, 0, 0))
                x += mark_w
                if index != len(pattern) - 1:
                    x += unit
    return image


def _header_budget(side):
    return max(18, int(side * HEADER_MAX_RATIO))


def _header_at(text, width, size):
    font = _load_font(size)
    inner = max(40, width - PAD_X * 2)
    lines = _wrap(text, font, inner)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 1
    header_h = PAD_Y + line_h * max(1, len(lines)) + PAD_Y + RULE
    return font, lines, line_h, header_h


def _plan_stego(text, with_header=True):
    raw = len(text.encode("utf-8"))
    side = get_optimal_size(raw)
    if not with_header:
        return side, side
    while side < 8000:
        _font, lines, _line_h, header_h = _header_at(CONTROL_STEGO, side, READABLE_FONT)
        payload_h = side - header_h
        if " ".join(lines) == CONTROL_STEGO and _rect_capacity(side, payload_h) >= raw:
            return side, payload_h
        side += 8
    return side, side // 2


def _plan_braille(text, with_header=True):
    cells = _braille_cells(text or "")
    rows = _pack_braille_rows(cells)
    n_cols = max((len(row) for row in rows), default=1)
    n_rows = max(1, len(rows))
    content_w = n_cols * MIN_CELL_W + BRAILLE_MARGIN * 2
    content_h = n_rows * MIN_CELL_H + BRAILLE_MARGIN * 2
    content_need = max(content_w, content_h)
    if not with_header:
        return content_need, 0, rows
    side = content_need
    header_h = 0
    for _ in range(12):
        _font, lines, _line_h, header_h = _fit_header(CONTROL_BRAILLE, side, _header_budget(side))
        need = max(
            content_w,
            content_h + header_h,
        )
        if need <= side and " ".join(lines) == CONTROL_BRAILLE:
            return side, header_h, rows
        side = need
    return side, header_h, rows


def _plan_morse(text, with_header=True):
    groups = _morse_groups(text or "")
    total = sum(_group_units(group) for group in groups) or 1
    max_group = max((_group_units(g) for g in groups), default=1)
    unit = MIN_UNIT
    line_h = unit + MORSE_ROW_GAP
    est_content_side = math.ceil(math.sqrt(total * unit * line_h))
    min_side_for_group = max_group * unit + MORSE_MARGIN * 2
    start_side = max(64, est_content_side, min_side_for_group)
    side = int(math.ceil(start_side / 8.0) * 8)
    header_h = 16 if with_header else 0
    rows = [[]]
    while side < 2400:
        if with_header:
            _font, lines, _line_h, header_h = _fit_header(CONTROL_MORSE, side, _header_budget(side))
            header_ok = " ".join(lines) == CONTROL_MORSE
        else:
            header_h = 0
            header_ok = True

        content_h = side - header_h
        cols = max(1, (side - MORSE_MARGIN * 2) // unit)
        fit_rows = max(1, (content_h - MORSE_MARGIN * 2) // line_h)
        if cols >= max_group and cols * fit_rows >= total and header_ok:
            rows = _pack_morse(groups, cols)
            if len(rows) <= fit_rows:
                return side, header_h, rows, unit
        side += 8
    rows = _pack_morse(groups, max(1, (side - MORSE_MARGIN * 2) // unit))
    return side, header_h, rows, unit


def build_image(mode, text, with_header=True):
    image, _header_h, _extra = build_image_info(mode, text, with_header=with_header)
    return image


def build_image_info(mode, text, with_header=True):
    if mode == "stego":
        side, payload_h = _plan_stego(text, with_header=with_header)
        if with_header:
            font, lines, line_h, header_h = _header_at(CONTROL_STEGO, side, READABLE_FONT)
            payload_h = side - header_h
            payload = _embed_rect(side, payload_h, text)
            image = Image.new("RGB", (side, side), (255, 255, 255))
            _paint_header(image, lines, font, line_h, header_h)
            image.paste(payload, (0, header_h))
            return image, header_h, {"mode": mode}
        else:
            payload = _embed_rect(side, side, text)
            return payload, 0, {"mode": mode}

    if mode == "braille":
        side, header_h, rows = _plan_braille(text, with_header=with_header)
        if with_header:
            font, lines, line_h, header_h = _fit_header(CONTROL_BRAILLE, side, _header_budget(side))
            content_h = side - header_h
            content, grid = _render_braille(rows, side, content_h)
            image = Image.new("RGB", (side, side), (255, 255, 255))
            _paint_header(image, lines, font, line_h, header_h)
            image.paste(content, (0, header_h))
            return image, header_h, grid
        else:
            content, grid = _render_braille(rows, side, side)
            return content, 0, grid

    side, header_h, rows, unit = _plan_morse(text, with_header=with_header)
    if with_header:
        font, lines, line_h, header_h = _fit_header(CONTROL_MORSE, side, _header_budget(side))
        content = _render_morse(rows, side, side - header_h, unit)
        image = Image.new("RGB", (side, side), (255, 255, 255))
        _paint_header(image, lines, font, line_h, header_h)
        image.paste(content, (0, header_h))
        return image, header_h, {"unit": unit, "line_h": unit + MORSE_ROW_GAP}
    else:
        content = _render_morse(rows, side, side, unit)
        return content, 0, {"unit": unit, "line_h": unit + MORSE_ROW_GAP}


def canvas_size(mode, text, with_header=True):
    if mode == "stego":
        side, _payload_h = _plan_stego(text, with_header=with_header)
    elif mode == "braille":
        side, _header_h, _rows = _plan_braille(text, with_header=with_header)
    else:
        side, _header_h, _rows, _unit = _plan_morse(text, with_header=with_header)
    return side, side


def content_origin(image):
    gray = np.asarray(image.convert("L"))
    full_black = np.where(np.all(gray == 0, axis=1))[0]
    if len(full_black) == 0:
        return 0
    end = int(full_black[0])
    for row in full_black[1:]:
        if row <= end + 1:
            end = int(row)
        else:
            break
    return end + 1


def decode_braille(image, grid):
    gray = np.asarray(image.convert("L"))
    decoded_chunks = []
    caps = False
    number_mode = False
    for row_i in range(grid["n_rows"]):
        for col_i in range(grid["n_cols"]):
            bits = 0
            for bit, (cx, cy) in enumerate(_dot_centers(grid, col_i, row_i)):
                if 0 <= cy < gray.shape[0] and 0 <= cx < gray.shape[1] and gray[cy, cx] < 128:
                    bits |= 1 << bit
            if bits == 0:
                decoded_chunks.append(" ")
                caps = False
                number_mode = False
                continue
            glyph = chr(0x2800 + bits)
            if glyph == NEWLINE_SIGN:
                decoded_chunks.append("\n")
                caps = False
                number_mode = False
                continue
            if glyph == CAPITAL_SIGN:
                caps = True
                number_mode = False
                continue
            if glyph == NUMBER_SIGN:
                number_mode = True
                caps = False
                continue
            if number_mode and glyph in DIGIT_FROM:
                decoded_chunks.append(DIGIT_FROM[glyph])
                continue
            number_mode = False
            ch = BRAILLE_FROM.get(glyph, "")
            if not ch:
                continue
            if caps and ch.isalpha():
                ch = ch.upper()
            caps = False
            decoded_chunks.append(ch)
    res = "".join(decoded_chunks)
    lines = [l.rstrip() for l in res.split("\n")]
    return "\n".join(lines).rstrip("\n")


def decode_morse(image, layout):
    unit = layout["unit"]
    line_h = layout["line_h"]
    gray = np.asarray(image.convert("L"))
    n_lines = max(0, (gray.shape[0] - MORSE_MARGIN) // line_h)
    symbols = []
    letters = []
    words = []
    lines = []
    caps = False

    def flush_letter():
        nonlocal symbols, caps
        if not symbols:
            return
        pattern = "".join(symbols)
        symbols = []
        if pattern == CAPITAL_PREFIX:
            caps = True
            return
        ch = MORSE_FROM.get(pattern, "")
        if caps and ch.isalpha():
            ch = ch.upper()
        caps = False
        if ch:
            letters.append(ch)

    def flush_word():
        nonlocal letters
        flush_letter()
        if letters:
            words.append("".join(letters))
            letters = []

    def apply_gap(units):
        if units <= 2:
            return
        if units <= 5:
            flush_letter()
            return
        if units <= 9:
            flush_word()
            return
        flush_word()
        count = max(1, int(round(units / NEWLINE_UNITS)))
        for _ in range(count):
            lines.append(" ".join(words))
            words.clear()

    for row_i in range(n_lines):
        y = MORSE_MARGIN + row_i * line_h + unit // 2
        if y >= gray.shape[0]:
            break
        row = gray[y, MORSE_MARGIN:gray.shape[1] - MORSE_MARGIN]
        ink = row < 128
        if not ink.any():
            continue
        last = int(np.where(ink)[0][-1])
        ink = ink[: last + 1]
        runs = []
        current = bool(ink[0])
        length = 1
        for value in ink[1:]:
            marked = bool(value)
            if marked == current:
                length += 1
            else:
                runs.append((current, length))
                current = marked
                length = 1
        runs.append((current, length))
        for is_black, run in runs:
            units = max(1, int(round(run / unit)))
            if is_black:
                symbols.append("-" if units >= 2 else ".")
            else:
                apply_gap(units)
    flush_word()
    lines.append(" ".join(words))
    return "\n".join(lines).rstrip("\n")
