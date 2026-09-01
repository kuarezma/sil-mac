import os
import subprocess
import psutil
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from nexus.effects import cyber_gradient, sparkline

console = Console(force_terminal=True, color_system="truecolor")

def get_mini_telemetry():
    """Fetch quick lightweight metrics for the HUD banner."""
    cpu_pct = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    batt_str = "AC"
    try:
        raw = subprocess.check_output(["pmset", "-g", "batt"], text=True)
        if "%" in raw:
            import re
            m = re.search(r"(\d+)%", raw)
            if m:
                batt_str = f"{m.group(1)}%"
    except Exception:
        pass

    return {
        "cpu": cpu_pct,
        "ram": vm.percent,
        "disk": disk.percent,
        "batt": batt_str
    }

def print_banner(version: str = "2.0.0 PRO"):
    """Render symmetric Cyberpunk HUD Banner."""
    logo_ascii = """  ███████╗██╗██╗     
  ██╔════╝██║██║     
  ███████╗██║██║     
  ╚════██║██║██║     
  ███████║██║███████╗
  ╚══════╝╚═╝╚══════╝"""

    grad_logo = cyber_gradient(
        logo_ascii,
        ["#00f0ff", "#38bdf8", "#818cf8", "#a855f7", "#ec4899", "#10b981"]
    )

    hud = get_mini_telemetry()
    cpu_spark = sparkline([10, 25, hud['cpu'], max(5, hud['cpu'] - 10), hud['cpu']])

    t_right = Text()
    t_right.append(" NEXUS DEEP OPTIMIZER\n", style="bold #00f0ff")
    t_right.append(f" v{version} • Apple Silicon Native\n\n", style="italic #94a3b8")
    
    t_right.append(" CPU ", style="bold #94a3b8")
    t_right.append(f"{hud['cpu']:4.1f}% ", style="bold #38bdf8")
    t_right.append(f"[{cpu_spark}]   ", style="#00f0ff")
    t_right.append("RAM ", style="bold #94a3b8")
    t_right.append(f"{hud['ram']:4.1f}%\n", style="bold #a855f7")
    
    t_right.append(" SSD ", style="bold #94a3b8")
    t_right.append(f"{hud['disk']:4.1f}%          ", style="bold #f59e0b")
    t_right.append("BAT ", style="bold #94a3b8")
    t_right.append(f"{hud['batt']} ⚡", style="bold #10b981")

    # Symmetric 2-column grid with a subtle vertical line
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", width=2)
    grid.add_column(justify="left", ratio=1)
    
    divider_text = Text("\n│\n│\n│\n│\n│\n", style="#6366f1")
    grid.add_row(grad_logo, divider_text, t_right)

    panel = Panel(
        grid,
        box=box.ROUNDED,
        border_style="#6366f1",
        style="on #080d1a",
        padding=(1, 2)
    )
    console.print(panel)

if __name__ == "__main__":
    print_banner()
