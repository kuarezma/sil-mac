import time
import math
import sys
from typing import List, Tuple
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich import box

console = Console(force_terminal=True, color_system="truecolor")

def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def interpolate_color(c1: str, c2: str, factor: float) -> str:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return rgb_to_hex(r, g, b)

def cyber_gradient(text: str, colors: List[str] = None) -> Text:
    """Apply a smooth character-by-character gradient across multiple hex colors."""
    if colors is None:
        colors = ["#00f0ff", "#38bdf8", "#818cf8", "#a855f7", "#ec4899", "#10b981"]
    
    t = Text()
    lines = text.splitlines(keepends=True)
    total_chars = max(1, sum(len(line) for line in lines))
    char_idx = 0

    num_segments = len(colors) - 1
    for line in lines:
        for ch in line:
            if ch in ['\n', '\r']:
                t.append(ch)
                continue
            progress = char_idx / total_chars
            seg_idx = min(int(progress * num_segments), num_segments - 1)
            local_factor = (progress * num_segments) - seg_idx
            c1 = colors[seg_idx]
            c2 = colors[seg_idx + 1]
            color = interpolate_color(c1, c2, local_factor)
            t.append(ch, style=f"bold {color}")
            char_idx += 1
    return t

def sparkline(values: List[float], min_val: float = None, max_val: float = None) -> str:
    """Generate a high-tech unicode block sparkline graph."""
    if not values:
        return ""
    bars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    if min_val is None:
        min_val = min(values)
    if max_val is None:
        max_val = max(values)
    if min_val == max_val:
        return bars[0] * len(values)

    result = []
    for v in values:
        norm = (v - min_val) / (max_val - min_val)
        idx = min(int(norm * (len(bars) - 1)), len(bars) - 1)
        result.append(bars[max(0, idx)])
    return "".join(result)

def neon_badge(label: str, bg: str = "#6366f1", fg: str = "bold white") -> str:
    """Render a stylish pill/badge tag."""
    return f"[{fg} on {bg}] {label} [/{fg} on {bg}]"

def celebrate_freed_space(freed_bytes: int):
    """Render a futuristic celebratory freed space summary card with audio chime."""
    from nexus.ui_helpers import format_bytes, C_EMERALD, C_CYAN, C_PURPLE, C_AMBER

    # Terminal bell
    sys.stdout.write("\a")
    sys.stdout.flush()

    card_text = Text()
    card_text.append("\n  ✨ SİSTEM TEMİZLİK OPERASYONU TAMAMLANDI ✨\n\n", style="bold #00f0ff")
    card_text.append("  Geri Kazanılan Depolama Alanı:\n", style="italic #94a3b8")
    card_text.append(f"  + {format_bytes(freed_bytes)}\n\n", style="bold #10b981")
    card_text.append("  ⚡ Apple Silicon NVMe SSD ve RAM optimize edildi.\n", style="bold white")

    panel = Panel(
        card_text,
        box=box.DOUBLE,
        border_style="#00f0ff",
        style="on #0f172a",
        padding=(0, 2)
    )
    console.print(panel)
