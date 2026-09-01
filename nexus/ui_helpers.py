import os
import sys
import math
from typing import List, Dict, Any, Optional, Union
from wcwidth import wcswidth
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich import box

console = Console(force_terminal=True, color_system="truecolor")

# Theme Colors
C_CYAN = "#00f0ff"
C_BLUE = "#38bdf8"
C_PURPLE = "#a855f7"
C_INDIGO = "#6366f1"
C_GREEN = "#10b981"
C_EMERALD = "#34d399"
C_AMBER = "#f59e0b"
C_RED = "#ef4444"
C_MUTED = "#94a3b8"
C_DARK = "#0f172a"

# Semantic aliases: use these when styling by risk level, not just color name.
C_DANGER = C_RED       # irreversible / destructive actions (kill, uninstall, prune)
C_SAFE = C_EMERALD      # safe / reversible actions (cache cleanup)
C_WARN = C_AMBER        # requires attention but not destructive

def pad_visual(text: str, width: int, fill: str = " ") -> str:
    """Pad text to a target *display* width, accounting for wide/emoji glyphs.
    Plain str.format ('{:<30}') counts code points, not terminal columns, so
    emoji and CJK-width characters silently break column alignment. This uses
    wcwidth to measure actual rendered width instead."""
    visual_w = wcswidth(text)
    if visual_w is None or visual_w < 0:
        visual_w = len(text)
    if visual_w >= width:
        return text
    return text + fill * (width - visual_w)

def truncate_visual(text: str, max_width: int, ellipsis: str = "…") -> str:
    """Truncate text to a target display width, respecting wide glyphs."""
    if wcswidth(text) is None:
        return text[:max_width]
    if wcswidth(text) <= max_width:
        return text
    out = ""
    for ch in text:
        w = wcswidth(out + ch + ellipsis)
        if w is not None and w > max_width:
            break
        out += ch
    return out + ellipsis

def format_bytes(size: Optional[Union[int, float]]) -> str:
    """Format bytes into a human readable string (KB, MB, GB, TB)."""
    if size is None or size < 0:
        return "0 B"
    try:
        size = float(size)
        if math.isnan(size) or math.isinf(size):
            return "0 B"
    except (TypeError, ValueError):
        return "0 B"

    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            if unit == 'B':
                return f"{int(size)} B"
            elif unit in ['KB', 'MB']:
                return f"{size:.1f} {unit}"
            else:
                return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

_HEADER_TIER_COLOR = {"safe": C_SAFE, "caution": C_WARN}

def create_header(title: str, subtitle: str = "", icon: str = "⚡", tier: Optional[str] = None) -> Panel:
    """Create a stylized glowing header panel.

    tier: optional "safe" (emerald border — read-only modules like status/log)
    or "caution" (amber border — modules that can kill processes, uninstall
    apps, or otherwise change the system), so the risk level of a module is
    visible the instant its screen opens, not just inside individual confirm
    prompts. Omit for the default cyan border (the common case: cache/file
    cleanup, always gated by its own confirm)."""
    accent = _HEADER_TIER_COLOR.get(tier, C_CYAN)
    t = Text()
    t.append(f" {icon} ", style=f"bold {accent}")
    t.append(title.upper(), style="bold white")
    if subtitle:
        t.append(f"  •  {subtitle}", style=f"italic {C_MUTED}")

    return Panel(
        t,
        box=box.DOUBLE,
        border_style=accent,
        padding=(0, 2),
        style=f"on {C_DARK}"
    )

def create_gauge(percentage: float, width: int = 20) -> str:
    """Create a high-tech colored gauge bar with unicode blocks."""
    try:
        percentage = float(percentage)
        if math.isnan(percentage) or math.isinf(percentage):
            percentage = 0.0
    except (TypeError, ValueError):
        percentage = 0.0

    percentage = max(0.0, min(100.0, percentage))
    filled_len = int(round(width * percentage / 100.0))
    filled_len = max(0, min(width, filled_len))
    empty_len = width - filled_len
    
    if percentage < 60:
        color = C_EMERALD
    elif percentage < 85:
        color = C_AMBER
    else:
        color = C_RED
        
    bar = "█" * filled_len + "░" * empty_len
    return f"[{color}]{bar}[/{color}] [{color}]{percentage:5.1f}%[/{color}]"

def get_path_size(path: str) -> int:
    """Calculate the on-disk size of a file or directory without following symlinks."""
    if not path or not os.path.lexists(path):
        return 0
    if os.path.islink(path) or os.path.isfile(path):
        try:
            return os.lstat(path).st_size
        except OSError:
            return 0

    total = 0
    try:
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
                except OSError:
                    continue
    except OSError:
        pass
    return total

def render_scan_table(
    items: List[Dict[str, Any]],
    columns: List[Dict[str, Any]],
    title: Optional[str] = None,
    numbered: bool = True,
    start_index: int = 1
) -> Table:
    """Build a consistently styled scan-result table from a list of dict items,
    eliminating the repeated Table/add_column/add_row boilerplate that used to
    be duplicated (with drifting styles/widths) across every module.

    Each column spec: {"header", "key", "style"=white, "width"=None,
    "justify"="left", "format"="bytes"|None, "no_wrap"=True}.
    A key of "size" formats via format_bytes automatically unless overridden.
    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style=C_INDIGO,
        header_style=f"bold {C_CYAN}",
        expand=True,
        show_header=True
    )
    if numbered:
        table.add_column("#", style=C_MUTED, width=4, no_wrap=True)
    for col in columns:
        table.add_column(
            col.get("header", ""),
            style=col.get("style", "white"),
            width=col.get("width"),
            justify=col.get("justify", "left"),
            no_wrap=col.get("no_wrap", True),
            overflow=col.get("overflow")
        )

    for i, item in enumerate(items, start_index):
        row = [str(i)] if numbered else []
        for col in columns:
            val = item.get(col["key"], "")
            fmt = col.get("format") or ("bytes" if col["key"] == "size" else None)
            if fmt == "bytes":
                val = format_bytes(val)
            row.append(str(val))
        table.add_row(*row)

    return table

def create_spinner(description: str):
    """Create a sleek futuristic spinner for long operations."""
    return Progress(
        SpinnerColumn(spinner_name="dots12", style=f"bold {C_CYAN}"),
        TextColumn(f"[bold {C_BLUE}]{{task.description}}"),
        transient=True,
        console=console
    )

def confirm_action(prompt_text: str, default: bool = False) -> bool:
    """Interactive confirmation prompt."""
    default_str = "Y/n" if default else "y/N"
    console.print(f"\n[bold {C_AMBER}]?[/] [{C_CYAN}]{prompt_text}[/] [{C_MUTED}]({default_str})[/]: ", end="")
    try:
        choice = input().strip().lower()
        if not choice:
            return default
        return choice in ['y', 'yes', 'e', 'evet']
    except (KeyboardInterrupt, EOFError):
        console.print("\n[italic red]İptal edildi.[/]")
        return False
