import os
import subprocess
import signal
import psutil
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, create_spinner, render_scan_table, pad_visual,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import select_menu, confirm_menu
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

CRITICAL_PROCESS_NAMES = {"launchd", "kernel_task", "windowserver", "loginwindow"}


def is_protected_pid(target_pid: int, current_pid: int, parent_pid: int, proc_name: str) -> bool:
    """True if target_pid must never be SIGKILL'd from this tool: Nexus
    itself, its parent shell, PID 0/1, or a handful of macOS processes
    whose death takes the whole session (or the machine) down with it."""
    if target_pid in (current_pid, parent_pid, 0, 1):
        return True
    return proc_name.lower() in CRITICAL_PROCESS_NAMES


class PortRadar:
    def __init__(self):
        pass

    def scan_ports(self) -> List[Dict[str, Any]]:
        """Scan all active listening TCP ports on the system."""
        ports = []
        try:
            out = subprocess.check_output(["lsof", "+c", "0", "-iTCP", "-sTCP:LISTEN", "-n", "-P"], text=True)
            lines = out.strip().splitlines()
            if len(lines) > 1:
                for l in lines[1:]:
                    parts = l.split()
                    if len(parts) >= 9:
                        proc = parts[0]
                        pid = parts[1]
                        user = parts[2]
                        addr = parts[8]
                        port_str = addr.split(":")[-1]
                        ports.append({
                            "port": port_str,
                            "process": proc,
                            "pid": int(pid),
                            "user": user,
                            "address": addr
                        })
        except Exception:
            pass
        return ports

    def scan_high_memory_processes(self, limit: int = 8) -> List[Dict[str, Any]]:
        """Find processes consuming large amount of RAM or CPU."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'username']):
            try:
                mem = p.info['memory_info'].rss if p.info['memory_info'] else 0
                if mem > 150 * 1024 * 1024: # > 150MB
                    procs.append({
                        "pid": p.info['pid'],
                        "name": p.info['name'],
                        "memory": mem,
                        "cpu": p.info['cpu_percent'] or 0.0,
                        "user": p.info['username'] or "-"
                    })
            except Exception:
                pass
        
        procs.sort(key=lambda x: x['memory'], reverse=True)
        return procs[:limit]

    def render(self):
        """Render Port & Process Radar with clean aligned tables."""
        console.print(create_header("PORT & HAYALET SÜREÇ RADARI", "Dinlenen TCP Portları, Yüksek Bellek Tüketen Süreçler & Kill", "📡", tier="caution"))

        ports = self.scan_ports()
        high_procs = self.scan_high_memory_processes()

        # 1. Ports Table
        if ports:
            table_p = render_scan_table(ports, [
                {"header": "Port", "key": "port", "style": f"bold {C_AMBER}", "width": 8},
                {"header": "Süreç Adı (Process)", "key": "process", "style": "bold white", "width": 22},
                {"header": "PID", "key": "pid", "style": f"bold {C_BLUE}", "width": 8},
                {"header": "Kullanıcı", "key": "user", "style": C_MUTED, "width": 12},
                {"header": "Adres", "key": "address", "style": C_MUTED, "overflow": "ellipsis"},
            ], title="[bold #38bdf8]🌐 Aktif Dinlenen TCP Portları[/]", numbered=False)
            console.print(table_p)
        else:
            console.print(f"[{C_EMERALD}]✓ Dinlenen açık port bulunamadı.[/]")

        # 2. High-Memory Processes Table
        if high_procs:
            table_m = render_scan_table(high_procs, [
                {"header": "PID", "key": "pid", "style": f"bold {C_BLUE}", "width": 8},
                {"header": "Süreç Adı", "key": "name", "style": "bold white", "width": 25},
                {"header": "RAM Tüketimi", "key": "memory", "style": f"bold {C_AMBER}", "justify": "right", "width": 14, "format": "bytes"},
                {"header": "Kullanıcı", "key": "user", "style": C_MUTED},
            ], title="[bold #38bdf8]🔥 Yüksek Bellek Tüketen Arka Plan Süreçleri[/]", numbered=False)
            console.print(table_m)

        choices = []
        if ports:
            choices.append(Separator("--- Dinlenen Portlar (Kill) ---"))
            for p in ports:
                choices.append(Choice(p['pid'], f"Port {pad_visual(p['port'], 6)} | {pad_visual(p['process'], 18)} (PID {p['pid']})"))

        if high_procs:
            choices.append(Separator("--- Yüksek RAM Tüketen Süreçler (Kill) ---"))
            for pr in high_procs:
                choices.append(Choice(pr['pid'], f"{pad_visual(pr['name'], 22)} | {pad_visual(format_bytes(pr['memory']), 10)} (PID {pr['pid']})"))

        choices.append(Separator())
        choices.append(Choice(None, "Geri Dön"))

        target_pid = select_menu("Sonlandırmak istediğiniz portu veya süreci seçin:", choices)
        if target_pid:
            try:
                proc_name = psutil.Process(target_pid).name()
            except Exception:
                proc_name = "?"
            if is_protected_pid(target_pid, os.getpid(), os.getppid(), proc_name):
                console.print(f"[{C_RED}]✖ Güvenlik: PID {target_pid} ({proc_name}) kritik bir sistem/kabuk süreci (ya da Nexus'un kendisi) olduğu için sonlandırılamaz.[/]\n")
                return
            if confirm_menu(f"PID {target_pid} ({proc_name}) sürecini zorla sonlandırmak (SIGKILL) istiyor musunuz?", default=False, danger=True):
                try:
                    os.kill(target_pid, signal.SIGKILL)
                    console.print(f"[{C_EMERALD}]✓ Süreç (PID {target_pid}) başarıyla sonlandırıldı.[/]\n")
                except PermissionError:
                    # Sudo ile otomatik yetkilendir
                    res = subprocess.run(["sudo", "kill", "-9", str(target_pid)], check=False)
                    if res.returncode == 0:
                        console.print(f"[{C_EMERALD}]✓ Süreç (PID {target_pid}) yetkilendirilerek başarıyla sonlandırıldı.[/]\n")
                    else:
                        console.print(f"[{C_RED}]✖ Süreç sonlandırılamadı: Erişim reddedildi.[/]\n")
                except Exception as e:
                    console.print(f"[{C_RED}]Hata: {e}[/]\n")
