import os
import re
import plistlib
import shutil
import glob
from typing import List, Dict, Any, Tuple
from rich.table import Table
from rich.panel import Panel
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, create_spinner, render_scan_table, pad_visual,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import select_menu, checkbox_menu, confirm_menu
from nexus.deletion_engine import execute_deletion_with_live_report
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

class AppUninstaller:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.apps_dirs = ["/Applications", os.path.join(self.home, "Applications")]

    def list_installed_apps(self) -> List[Dict[str, Any]]:
        """List all installed third-party and user applications."""
        apps = []
        with create_spinner("Yüklü uygulamalar taranıyor...") as progress:
            task = progress.add_task("scan", total=None)
            for d in self.apps_dirs:
                if not os.path.exists(d):
                    continue
                for item in sorted(os.listdir(d)):
                    if item.endswith(".app"):
                        app_path = os.path.join(d, item)
                        name = item.replace(".app", "")
                        bundle_id = self._get_bundle_id(app_path)
                        sz = self._get_dir_size(app_path)
                        apps.append({
                            "name": name,
                            "path": app_path,
                            "bundle_id": bundle_id,
                            "app_size": sz
                        })
        return apps

    @staticmethod
    def _name_matches(item_lower: str, name_lower: str) -> bool:
        """Word-boundary aware substring match to avoid false positives
        (e.g. app 'Sim' must not match unrelated 'Simulator' or 'Similarity')."""
        pattern = r"(?<![a-z0-9])" + re.escape(name_lower) + r"(?![a-z0-9])"
        return re.search(pattern, item_lower) is not None

    def find_app_residuals(self, app_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all residual files for a given application."""
        residuals = []
        name = app_info['name']
        bid = app_info['bundle_id']
        name_lower = name.lower()

        search_locations = [
            ("Application Support", os.path.join(self.home, "Library/Application Support")),
            ("Caches", os.path.join(self.home, "Library/Caches")),
            ("Containers", os.path.join(self.home, "Library/Containers")),
            ("Group Containers", os.path.join(self.home, "Library/Group Containers")),
            ("Saved State", os.path.join(self.home, "Library/Saved Application State")),
            ("Preferences", os.path.join(self.home, "Library/Preferences")),
            ("Logs", os.path.join(self.home, "Library/Logs")),
            ("HTTPStorages", os.path.join(self.home, "Library/HTTPStorages"))
        ]

        for cat, base_path in search_locations:
            if not os.path.exists(base_path):
                continue
            for item in os.listdir(base_path):
                item_lower = item.lower()
                matched = False
                if bid and bid.lower() in item_lower:
                    matched = True
                elif len(name_lower) > 3 and self._name_matches(item_lower, name_lower):
                    matched = True

                if matched:
                    fp = os.path.join(base_path, item)
                    sz = self._get_dir_size(fp) if os.path.isdir(fp) else os.path.getsize(fp)
                    residuals.append({
                        "category": f"Kalıntı ({cat})",
                        "name": item,
                        "path": fp,
                        "size": sz,
                        "type": "dir" if os.path.isdir(fp) else "file"
                    })

        return residuals

    def scan_orphans(self) -> List[Dict[str, Any]]:
        """Find residual data for apps that are already uninstalled/deleted."""
        orphans = []
        installed = self.list_installed_apps()
        installed_names = {a['name'].lower() for a in installed}
        installed_bids = {a['bundle_id'].lower() for a in installed if a['bundle_id']}

        system_whitelist = {
            "apple", "system", "com.apple", "cloudkit", "finder", "dock", "safari",
            "google", "microsoft", "adobe", "antigravity", "nexus", "uv", "pip", "brew"
        }

        with create_spinner("Yetim ve silinmiş uygulama artıkları taranıyor...") as progress:
            task = progress.add_task("scan", total=None)
            for search_dir, cat in [
                (os.path.join(self.home, "Library/Application Support"), "Application Support"),
                (os.path.join(self.home, "Library/Caches"), "Caches"),
                (os.path.join(self.home, "Library/Saved Application State"), "Saved State")
            ]:
                if not os.path.exists(search_dir):
                    continue
                for item in os.listdir(search_dir):
                    item_lower = item.lower()
                    if any(w in item_lower for w in system_whitelist):
                        continue
                    if not any(app_n in item_lower for app_n in installed_names) and not any(bid in item_lower for bid in installed_bids):
                        fp = os.path.join(search_dir, item)
                        sz = self._get_dir_size(fp) if os.path.isdir(fp) else os.path.getsize(fp)
                        if sz > 2 * 1024 * 1024: # > 2MB
                            orphans.append({
                                "name": item,
                                "category": f"Yetim ({cat})",
                                "path": fp,
                                "size": sz,
                                "type": "dir" if os.path.isdir(fp) else "file"
                            })

        return orphans

    def render(self):
        """Render App Uninstaller & Orphan Hunter with arrow-key menus."""
        console.print(create_header("AKILLI UYGULAMA KALDIRICI & YETİM ARTIK AVCISI", "Kalıntısız Kaldırma & Silinmiş Uygulama Artıkları", "🗑️"))

        mode_choices = [
            Choice("apps", "1. Yüklü Uygulamayı Kalıntılarıyla Kaldır"),
            Choice("orphans", "2. Silinmiş Uygulama Artıklarını (Yetimleri) Tara & Temizle"),
            Separator(),
            Choice("back", "Geri Dön")
        ]

        mode = select_menu("İşlem modunu yön tuşlarıyla seçin:", mode_choices)

        if mode == "apps":
            self._render_installed_apps()
        elif mode == "orphans":
            self._render_orphans()

    def _render_installed_apps(self):
        apps = self.list_installed_apps()
        if not apps:
            console.print(f"[{C_MUTED}]Yüklü uygulama bulunamadı.[/]")
            return

        choices = [
            Choice(a, f"{pad_visual(a['name'], 25)} │  {pad_visual(a['bundle_id'] or '-', 35)} ({format_bytes(a['app_size'])})")
            for a in apps
        ]
        choices.append(Separator())
        choices.append(Choice(None, "Geri Dön"))

        target = select_menu("Kaldırmak istediğiniz uygulamayı seçin:", choices)
        if not target:
            return

        residuals = self.find_app_residuals(target)
        total_sz = target['app_size'] + sum(r['size'] for r in residuals)

        console.print(f"\n[bold {C_AMBER}]Bulunan Kalıntılar ({target['name']}):[/]")
        for r in residuals:
            console.print(f"  • [{C_PURPLE}]{r['category']}:[/] {r['name']} ({format_bytes(r['size'])})")

        if confirm_menu(f"'{target['name']}' uygulaması ve tüm {len(residuals)} kalıntısı ({format_bytes(total_sz)}) silinsin mi?", default=False, danger=True):
            items_to_del = [{
                "name": f"{target['name']}.app",
                "category": "Uygulama İkili Dosyası",
                "path": target['path'],
                "size": target['app_size'],
                "type": "dir"
            }] + residuals
            execute_deletion_with_live_report(items_to_del, f"'{target['name']}' Kaldırma İşlemi")

    def _render_orphans(self):
        orphans = self.scan_orphans()
        if not orphans:
            console.print(Panel(
                f"[{C_EMERALD}]✓ Sistemde silinmiş uygulamalara ait yetim artık dosya bulunamadı.[/]",
                border_style=C_EMERALD,
                box=box.ROUNDED
            ))
            return

        total_sz = sum(o['size'] for o in orphans)
        table = render_scan_table(orphans, [
            {"header": "Kategori", "key": "category", "style": f"bold {C_PURPLE}", "width": 24},
            {"header": "Öğe", "key": "name", "style": "bold white"},
            {"header": "Boyut", "key": "size", "style": f"bold {C_AMBER}", "justify": "right", "width": 12},
        ])
        console.print(table)
        console.print(f"[{C_PURPLE}]Toplam Yetim Artık Boyutu:[/] [bold {C_CYAN}]{format_bytes(total_sz)}[/]\n")

        choices = [
            Choice(o, f"[{pad_visual(o['category'], 24)}] {pad_visual(o['name'], 30)} │  ({format_bytes(o['size'])})")
            for o in orphans
        ]

        selected_orphans = checkbox_menu("Temizlemek istediğiniz yetim artıkları seçin (Space: İşaretle, Enter: Onayla):", choices)

        if selected_orphans:
            sel_sz = sum(x['size'] for x in selected_orphans)
            if confirm_menu(f"Seçilen {len(selected_orphans)} yetim artığı ({format_bytes(sel_sz)}) temizlemek istiyor musunuz?", default=False):
                execute_deletion_with_live_report(selected_orphans, "Yetim Artık Temizliği")

    def _get_bundle_id(self, app_path: str) -> str:
        plist_path = os.path.join(app_path, "Contents/Info.plist")
        if os.path.exists(plist_path):
            try:
                with open(plist_path, 'rb') as f:
                    plist = plistlib.load(f)
                    return plist.get("CFBundleIdentifier", "")
            except Exception:
                pass
        return ""

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
