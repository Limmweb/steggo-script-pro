# utils.py
import math
import re

def get_optimal_size(raw_bytes_len):
    total_bits = 16 + raw_bytes_len * 8
    needed_blocks = math.ceil(total_bits / 24.0)
    side_blocks = math.ceil(math.sqrt(needed_blocks))
    side = max(64, side_blocks * 8)
    return side

def sanitize_filename(text, max_len=20):
    clean = re.sub(r'[^\w\s-]', '', text).strip()
    clean = re.sub(r'[\s-]+', '_', clean)
    return clean[:max_len] or "steggo_chip"
