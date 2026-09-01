import os
import re
import subprocess
import psutil
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, create_gauge,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_DARK, C_INDIGO
)
from nexus.effects import sparkline

class HardwareDashboard:
    def __init__(self):
        pass

    def get_system_info(self):
        info = {
            "chip": "Apple Silicon",
            "cores": os.cpu_count() or 8,
            "os_ver": "macOS",
            "uptime": ""
        }
        try:
            info["chip"] = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
            sw_vers = subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip()
            sw_name = subprocess.check_output(["sw_vers", "-productName"], text=True).strip()
            info["os_ver"] = f"{sw_name} {sw_vers}"
            
            up_raw = subprocess.check_output(["uptime"], text=True).strip()
            if "up" in up_raw:
                info["uptime"] = up_raw.split("up")[1].split(",")[0].strip()
        except Exception:
            pass
        return info

    def get_memory_info(self):
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        pressure = 0.0
        active_gb = wired_gb = compressed_gb = free_gb = 0.0
        try:
            vm_stat = subprocess.check_output(["vm_stat"], text=True)
            stats = {}
            for line in vm_stat.splitlines():
                if ":" in line:
                    parts = line.split(":")
                    val = parts[1].strip().rstrip(".")
                    if val.isdigit():
                        stats[parts[0].strip()] = int(val) * 4096
            
            free = stats.get("Pages free", 0) + stats.get("Pages speculative", 0)
            active = stats.get("Pages active", 0)
            wired = stats.get("Pages wired down", 0)
            compressed = stats.get("Pages occupied by compressor", 0)
            total = free + active + stats.get("Pages inactive", 0) + wired + compressed
            if total > 0:
                pressure = ((active + wired + compressed) / total) * 100.0
            
            active_gb = active / (1024**3)
            wired_gb = wired / (1024**3)
            compressed_gb = compressed / (1024**3)
            free_gb = free / (1024**3)
        except Exception:
            pressure = vm.percent

        return {
            "total": vm.total,
            "used": vm.used,
            "free": vm.available,
            "percent": vm.percent,
            "pressure": pressure,
            "active_gb": active_gb,
            "wired_gb": wired_gb,
            "compressed_gb": compressed_gb,
            "swap_total": swap.total,
            "swap_used": swap.used
        }

    def get_battery_info(self):
        batt = {
            "percent": 100,
            "state": "AC Güç Kaynağı",
            "health": "Normal",
            "cycle_count": "-",
            "is_charging": False
        }
        try:
            raw = subprocess.check_output(["pmset", "-g", "batt"], text=True)
            if "%" in raw:
                match = re.search(r"(\d+)%", raw)
                if match:
                    batt["percent"] = int(match.group(1))
            if "discharging" in raw.lower():
                batt["state"] = "Pilde (Deşarj)"
            elif "charging" in raw.lower():
                batt["state"] = "Şarj Oluyor (AC)"
                batt["is_charging"] = True
            else:
                batt["state"] = "AC Adaptörüne Bağlı"

            sp_raw = subprocess.check_output(["system_profiler", "SPPowerDataType"], text=True)
            for line in sp_raw.splitlines():
                if "Cycle Count" in line:
                    batt["cycle_count"] = line.split(":")[1].strip()
                if "Condition" in line:
                    batt["health"] = line.split(":")[1].strip()
        except Exception:
            pass
        return batt

    def get_disk_info(self):
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }

    def render(self):
        """Render perfectly aligned, zero-overflow hardware telemetry grid."""
        console.print(create_header("APPLE SILICON DONANIM & SİSTEM TELEMETRİSİ", "M-Serisi SoC, Bellek Baskısı & NVMe Depolama", "⚡", tier="safe"))

        sys_info = self.get_system_info()
        mem = self.get_memory_info()
        batt = self.get_battery_info()
        disk = self.get_disk_info()
        per_core = psutil.cpu_percent(percpu=True, interval=0.25)
        total_cpu = sum(per_core) / max(1, len(per_core))

        # Main Telemetry Grid Table
        table = Table(
            box=box.ROUNDED,
            border_style=C_INDIGO,
            header_style=f"bold {C_CYAN}",
            expand=True,
            show_header=True,
            padding=(0, 1)
        )
        table.add_column("Bileşen", style=f"bold {C_PURPLE}", width=18, no_wrap=True)
        table.add_column("Metrik & Detay", style="white", width=28, no_wrap=True)
        table.add_column("Durum & Gösterge (Gauge)", style="bold", justify="right", width=28, no_wrap=True)

        # 1. SoC & CPU
        core_sparks = sparkline(per_core, 0, 100)
        table.add_row(
            "💻 SoC / İşlemci",
            f"{sys_info['chip']} ({sys_info['cores']}C)",
            f"Yük: {create_gauge(total_cpu, 10)}"
        )
        table.add_row(
            "⚡ Çekirdek Matrisi",
            f"C1-C8 Dağılım: [{C_CYAN}]{core_sparks}[/{C_CYAN}]",
            f"[{C_MUTED}]Uptime: {sys_info['uptime']}[/]"
        )

        # 2. Unified Memory
        table.add_row(
            "🧠 Birleşik Bellek",
            f"Kull: {format_bytes(mem['used'])} / {format_bytes(mem['total'])}",
            f"Baskı: {create_gauge(mem['pressure'], 10)}"
        )
        table.add_row(
            "📊 RAM Katmanları",
            f"Aktif: {mem['active_gb']:.1f}G | ZRAM: {mem['compressed_gb']:.1f}G",
            f"Boş: [{C_EMERALD}]{format_bytes(mem['free'])}[/{C_EMERALD}]"
        )

        # 3. Battery & Power
        table.add_row(
            "🔋 Pil & Güç",
            f"{batt['state']} (Sağlık: {batt['health']})",
            f"Doluluk: {create_gauge(batt['percent'], 10)}"
        )
        table.add_row(
            "⚡ Şarj Döngüsü",
            f"Döngü Sayısı: {batt['cycle_count']}",
            f"[{C_MUTED}]OS: {sys_info['os_ver']}[/]"
        )

        # 4. Storage NVMe
        table.add_row(
            "💾 NVMe SSD",
            f"Dolu: {format_bytes(disk['used'])} / {format_bytes(disk['total'])}",
            f"Doluluk: {create_gauge(disk['percent'], 10)}"
        )
        table.add_row(
            "📂 Boş Depolama",
            f"Kullanılabilir: [{C_EMERALD}]{format_bytes(disk['free'])}[/{C_EMERALD}]",
            f"[{C_MUTED}]Kayıt Yolu: /[/{C_MUTED}]"
        )

        console.print(table)
        console.print()
