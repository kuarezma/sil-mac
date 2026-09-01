import os
import sys
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

def format_bytes(size: int) -> str:
    """Format bytes into a human readable string (KB, MB, GB, TB)."""
    if size < 0:
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

def create_header(title: str, subtitle: str = "", icon: str = "⚡") -> Panel:
    """Create a stylized glowing header panel."""
    t = Text()
    t.append(f" {icon} ", style=f"bold {C_CYAN}")
    t.append(title.upper(), style="bold white")
    if subtitle:
        t.append(f"  •  {subtitle}", style=f"italic {C_MUTED}")
    
    return Panel(
        t,
        box=box.DOUBLE,
        border_style=C_CYAN,
        padding=(0, 2),
        style=f"on {C_DARK}"
    )

def create_gauge(percentage: float, width: int = 20) -> str:
    """Create a high-tech colored gauge bar with unicode blocks."""
    percentage = max(0.0, min(100.0, float(percentage)))
    filled_len = int(round(width * percentage / 100))
    empty_len = width - filled_len
    
    if percentage < 60:
        color = C_EMERALD
    elif percentage < 85:
        color = C_AMBER
    else:
        color = C_RED
        
    bar = "█" * filled_len + "░" * empty_len
    return f"[{color}]{bar}[/{color}] [{color}]{percentage:5.1f}%[/{color}]"

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
