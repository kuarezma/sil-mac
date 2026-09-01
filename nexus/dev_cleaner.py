import os
import shutil
import subprocess
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, create_spinner,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import checkbox_menu, confirm_menu
from nexus.deletion_engine import execute_deletion_with_live_report
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

class DevCleaner:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.global_caches: List[Dict[str, Any]] = []
        self.project_artifacts: List[Dict[str, Any]] = []

    def docker_available(self) -> bool:
        """Check whether the Docker CLI is installed and the daemon is reachable."""
        if not shutil.which("docker"):
            return False
        try:
            subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    def get_docker_reclaimable(self) -> Dict[str, str]:
        """Query docker for reclaimable build cache / dangling image / stopped container space."""
        info = {}
        try:
            out = subprocess.check_output(["docker", "system", "df"], text=True, timeout=10)
            info["raw"] = out.strip()
        except Exception:
            info["raw"] = ""
        return info

    def clean_docker(self):
        """Safely reclaim Docker disk space: dangling images, stopped containers,
        unused networks and build cache. Never touches named/tagged images or running
        containers/volumes."""
        console.print(f"\n[bold {C_CYAN}]🐳 Docker temizliği başlatılıyor (yalnızca yetim/dangling veriler)...[/]\n")
        commands = [
            (["docker", "container", "prune", "-f"], "Durdurulmuş konteynerler"),
            (["docker", "image", "prune", "-f"], "Yetim (dangling) imajlar"),
            (["docker", "network", "prune", "-f"], "Kullanılmayan ağlar"),
            (["docker", "builder", "prune", "-f"], "Derleme (build) önbelleği"),
        ]
        for cmd, label in commands:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                out = (res.stdout or "").strip().splitlines()
                reclaimed = next((l for l in out if "reclaimed" in l.lower() or "Total" in l), "")
                console.print(f"[{C_EMERALD}]✓ {label}:[/] [{C_MUTED}]{reclaimed or 'temiz'}[/]")
            except Exception as e:
                console.print(f"[{C_RED}]✖ {label}: {e}[/]")
        console.print()

    def scan_global_caches(self) -> List[Dict[str, Any]]:
        """Scan system-wide development caches and SDK stores."""
        self.global_caches = []
        
        known_caches = [
            ("Xcode DerivedData", "Xcode", os.path.join(self.home, "Library/Developer/Xcode/DerivedData")),
            ("Xcode Archives", "Xcode", os.path.join(self.home, "Library/Developer/Xcode/Archives")),
            ("iOS Simulator Caches", "Xcode/iOS", os.path.join(self.home, "Library/Developer/CoreSimulator/Caches")),
            ("Android Gradle Cache", "Android/Java", os.path.join(self.home, ".gradle/caches")),
            ("CocoaPods Cache", "iOS/macOS", os.path.join(self.home, "Library/Caches/CocoaPods")),
            ("Rust / Cargo Cache", "Rust", os.path.join(self.home, ".cargo/registry/cache")),
            ("Go Build Cache", "Go", os.path.join(self.home, ".cache/go-build")),
            ("npm Cache", "Node.js", os.path.join(self.home, ".npm/_cacache")),
            ("pnpm Store", "Node.js", os.path.join(self.home, "Library/pnpm/store")),
            ("Yarn Cache", "Node.js", os.path.join(self.home, "Library/Caches/Yarn")),
            ("pip Cache", "Python", os.path.join(self.home, "Library/Caches/pip")),
            ("uv Cache", "Python", os.path.join(self.home, ".cache/uv")),
        ]

        for name, category, path in known_caches:
            if os.path.exists(path):
                sz = self._get_dir_size(path)
                if sz > 1024 * 1024: # > 1MB
                    self.global_caches.append({
                        "name": name,
                        "category": category,
                        "path": path,
                        "size": sz,
                        "type": "dir"
                    })

        return self.global_caches

    def scan_project_artifacts(self, scan_dirs: List[str] = None) -> List[Dict[str, Any]]:
        """Scan workspace folders for heavyweight dev build artifacts."""
        if scan_dirs is None:
            scan_dirs = [
                os.path.join(self.home, "Desktop"),
                os.path.join(self.home, "Documents"),
                os.path.join(self.home, "Developer"),
                os.path.join(self.home, "Projects")
            ]

        self.project_artifacts = []
        target_names = {
            "node_modules": "Node.js Modules",
            ".next": "Next.js Build",
            ".turbo": "Turborepo Cache",
            "target": "Rust / Java Target",
            ".venv": "Python Virtualenv",
            "venv": "Python Virtualenv",
            ".gradle": "Gradle Build Cache",
            ".parcel-cache": "Parcel Cache"
        }

        ignore_dirs = {
            ".git", ".svn", ".gemini", ".kimi-code", ".local", "Library", "Applications",
            ".Trash", "node_modules", "dist", "build", ".cache", "venv", ".venv"
        }

        with create_spinner("Çalışma alanları taranıyor...") as progress:
            task = progress.add_task("scan", total=None)
            for base_dir in scan_dirs:
                if not os.path.exists(base_dir):
                    continue
                for root, dirs, _ in os.walk(base_dir):
                    dirs[:] = [d for d in dirs if d not in ignore_dirs and not (d.startswith(".") and d not in target_names)]
                    rel = os.path.relpath(root, base_dir)
                    if rel != "." and len(rel.split(os.sep)) >= 3:
                        dirs[:] = []
                        continue

                    for d in list(dirs):
                        if d in target_names:
                            full_path = os.path.join(root, d)
                            sz = self._get_dir_size(full_path)
                            if sz > 5 * 1024 * 1024: # > 5MB
                                parent_folder = os.path.basename(os.path.dirname(full_path)) or os.path.basename(root)
                                self.project_artifacts.append({
                                    "name": f"{parent_folder}/{d}",
                                    "category": target_names[d],
                                    "path": full_path,
                                    "size": sz,
                                    "type": "dir"
                                })
                            dirs.remove(d)

        return self.project_artifacts

    def render(self):
        """Render Dev Cleaner dashboard with arrow-key multi-selection."""
        console.print(create_header("GELİŞTİRİCİ DERLEME & ÖNBELLEK TEMİZLEYİCİ", "Node, Xcode, Android, Rust, Python, Go & Caches", "💻"))

        caches = self.scan_global_caches()
        artifacts = self.scan_project_artifacts()

        total_caches = sum(x['size'] for x in caches)
        total_artifacts = sum(x['size'] for x in artifacts)
        grand_total = total_caches + total_artifacts

        # 1. Global Dev Caches Table
        if caches:
            table_c = Table(title="[bold #38bdf8]📦 Global Geliştirici Önbellekleri & SDK Depoları[/]", box=box.ROUNDED, border_style=C_INDIGO, header_style=f"bold {C_CYAN}", expand=True)
            table_c.add_column("#", style=C_MUTED, width=4)
            table_c.add_column("Ekosistem", style=f"bold {C_PURPLE}", width=16)
            table_c.add_column("Önbellek Türü", style="bold white")
            table_c.add_column("Boyut", style=f"bold {C_AMBER}", justify="right", width=12)

            for i, c in enumerate(caches, 1):
                table_c.add_row(str(i), c['category'], c['name'], format_bytes(c['size']))
            console.print(table_c)
        else:
            console.print(f"[{C_EMERALD}]✓ Global geliştirici önbelleği tertemiz.[/]")

        # 2. Project Build Artifacts Table
        if artifacts:
            table_a = Table(title="[bold #38bdf8]📁 Proje Derleme & Bağımlılık Artıkları (node_modules, target, .next)[/]", box=box.ROUNDED, border_style=C_INDIGO, header_style=f"bold {C_CYAN}", expand=True)
            table_a.add_column("#", style=C_MUTED, width=4)
            table_a.add_column("Tür", style=f"bold {C_BLUE}", width=20)
            table_a.add_column("Proje / Dizin Yolu", style="bold white")
            table_a.add_column("Boyut", style=f"bold {C_AMBER}", justify="right", width=12)

            for i, a in enumerate(artifacts, 1):
                rel_p = a['path'].replace(self.home, "~")
                table_a.add_row(str(i + len(caches)), a['category'], rel_p, format_bytes(a['size']))
            console.print(table_a)
        else:
            console.print(f"[{C_EMERALD}]✓ Proje dizinlerinde ağır derleme artığı bulunamadı.[/]")

        console.print(f"\n[{C_PURPLE}]Geliştirici Toplam Potansiyel Alan:[/] [bold {C_CYAN}]{format_bytes(grand_total)}[/]\n")

        docker_ok = self.docker_available()
        if docker_ok:
            df = self.get_docker_reclaimable()
            if df.get("raw"):
                console.print(f"[bold #38bdf8]🐳 Docker Disk Kullanımı[/]\n[{C_MUTED}]{df['raw']}[/]\n")

        choices = []
        if caches:
            choices.append(Separator("--- Global Geliştirici Önbellekleri ---"))
            for c in caches:
                choices.append(Choice(c, f"[{c['category']:<12}] {c['name']:<24} │  ({format_bytes(c['size'])})"))
        
        if artifacts:
            choices.append(Separator("--- Proje Derleme Klasörleri ---"))
            for a in artifacts:
                rel_p = a['path'].replace(self.home, "~")
                choices.append(Choice(a, f"[{a['category']:<16}] {rel_p:<30} │  ({format_bytes(a['size'])})"))

        DOCKER_MARKER = "__docker_prune__"
        if docker_ok:
            choices.append(Separator("--- Docker ---"))
            choices.append(Choice(DOCKER_MARKER, "🐳  Docker Yetim Verileri              │  Dangling imaj, durdurulmuş konteyner, build cache"))

        if not choices:
            return

        selected_items = checkbox_menu(
            "Temizlemek istediğiniz geliştirici öğelerini seçin (Space: İşaretle, Enter: Onayla):",
            choices
        )

        clean_docker = DOCKER_MARKER in selected_items
        selected_items = [x for x in selected_items if x != DOCKER_MARKER]

        if selected_items:
            sel_sz = sum(x['size'] for x in selected_items)
            if confirm_menu(f"Seçilen {len(selected_items)} geliştirici önbellek/proje klasörünü ({format_bytes(sel_sz)}) silmek istiyor musunuz?", default=False):
                execute_deletion_with_live_report(selected_items, "Geliştirici Artıkları Temizliği")
        elif not clean_docker:
            console.print(f"[{C_MUTED}]Hiçbir öğe seçilmedi.[/]")

        if clean_docker:
            if confirm_menu("Docker'daki yetim (dangling) imajlar, durdurulmuş konteynerler ve build cache temizlensin mi?", default=False):
                self.clean_docker()

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
