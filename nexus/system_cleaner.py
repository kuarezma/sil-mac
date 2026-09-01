import os
import glob
import shutil
import subprocess
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, create_spinner, render_scan_table, pad_visual,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import checkbox_menu, confirm_menu
from nexus.deletion_engine import execute_deletion_with_live_report
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

class SystemCleaner:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.targets: List[Dict[str, Any]] = []

    def scan(self) -> List[Dict[str, Any]]:
        """Deep scan macOS system, browser, log and installer caches."""
        self.targets = []

        scan_definitions = [
            ("macOS Kullanıcı Önbellekleri", "Sistem", os.path.join(self.home, "Library/Caches"), True),
            ("macOS Kullanıcı Günlükleri (Logs)", "Günlükler", os.path.join(self.home, "Library/Logs"), True),
            ("Çökme & Tanılama Raporları", "Tanılama", os.path.join(self.home, "Library/Logs/DiagnosticReports"), True),
            ("Çöp Sepeti (~/.Trash)", "Çöp", os.path.join(self.home, ".Trash"), True),
            ("Homebrew İndirme Önbelleği", "Paketler", os.path.join(self.home, "Library/Caches/Homebrew"), False),
            ("Google Chrome Önbelleği", "Tarayıcı", os.path.join(self.home, "Library/Caches/Google/Chrome"), False),
            ("Safari Önbelleği", "Tarayıcı", os.path.join(self.home, "Library/Caches/com.apple.Safari"), False),
            ("Brave Tarayıcı Önbelleği", "Tarayıcı", os.path.join(self.home, "Library/Caches/BraveSoftware"), False),
            ("Arc Tarayıcı Önbelleği", "Tarayıcı", os.path.join(self.home, "Library/Caches/company.thebrowser.Browser"), False),
            ("QuickLook & İkon Önbellekleri", "Sistem", os.path.join(self.home, "Library/Caches/com.apple.QuickLook.thumbnailcache"), False)
        ]

        with create_spinner("macOS sistem önbellekleri ve günlükleri taranıyor...") as progress:
            task = progress.add_task("scan", total=None)

            for name, category, path, is_sub_scan in scan_definitions:
                if os.path.exists(path):
                    sz = self._get_dir_size(path)
                    if sz > 1024 * 1024: # > 1MB
                        self.targets.append({
                            "name": name,
                            "category": category,
                            "path": path,
                            "size": sz,
                            "type": "dir"
                        })

            # Check for downloaded installers (.dmg, .pkg, .iso) in Downloads
            downloads_dir = os.path.join(self.home, "Downloads")
            if os.path.exists(downloads_dir):
                for ext in ["*.dmg", "*.pkg", "*.iso"]:
                    for f in glob.glob(os.path.join(downloads_dir, ext)):
                        try:
                            sz = os.path.getsize(f)
                            if sz > 5 * 1024 * 1024: # > 5MB
                                self.targets.append({
                                    "name": f"Yükleyici: {os.path.basename(f)}",
                                    "category": "İndirilenler",
                                    "path": f,
                                    "size": sz,
                                    "type": "file"
                                })
                        except Exception:
                            pass

        return self.targets

    def render(self):
        """Render System Cleaner dashboard with arrow-key checkbox selection."""
        console.print(create_header("macOS SİSTEM & ÖNBELLEK TEMİZLEYİCİ", "Caches, Logs, CrashReports, Tarayıcılar & Çöp Sepeti", "🧹"))

        targets = self.scan()
        if not targets:
            console.print(Panel(
                f"[{C_EMERALD}]✓ Sistem önbellekleri ve günlükleri tertemiz.[/]",
                border_style=C_EMERALD,
                box=box.ROUNDED
            ))
            return

        total_size = sum(t['size'] for t in targets)
        table = render_scan_table(targets, [
            {"header": "Kategori", "key": "category", "style": f"bold {C_PURPLE}", "width": 16},
            {"header": "Öğe / Konum", "key": "name", "style": "bold white"},
            {"header": "Boyut", "key": "size", "style": f"bold {C_AMBER}", "justify": "right", "width": 12},
        ])

        console.print(table)
        console.print(f"[{C_PURPLE}]Toplam Temizlenebilir Sistem Alanı:[/] [bold {C_CYAN}]{format_bytes(total_size)}[/]\n")

        choices = [
            Choice(t, f"[{pad_visual(t['category'], 12)}] {pad_visual(t['name'], 35)} │  ({format_bytes(t['size'])})")
            for t in targets
        ]

        selected_items = checkbox_menu(
            "Temizlemek istediğiniz sistem öğelerini seçin (Space: İşaretle, Enter: Onayla):",
            choices
        )

        if selected_items:
            sel_sz = sum(x['size'] for x in selected_items)
            if confirm_menu(f"Seçilen {len(selected_items)} sistem/önbellek öğesini ({format_bytes(sel_sz)}) temizlemek istiyor musunuz?", default=False):
                execute_deletion_with_live_report(selected_items, "Sistem Önbellek Temizliği")
        else:
            console.print(f"[{C_MUTED}]Hiçbir öğe seçilmedi.[/]")

    def _get_dir_size(self, path: str) -> int:
        total = 0
        try:
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total
