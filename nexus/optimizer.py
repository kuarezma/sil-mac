import os
import shutil
import subprocess
from rich.table import Table
from rich.panel import Panel
from rich import box
from nexus.ui_helpers import (
    console, create_header, create_spinner,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import select_menu, confirm_menu
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

class SystemOptimizer:
    def __init__(self):
        pass

    def render(self):
        """Render macOS optimization tools with arrow keys."""
        console.print(create_header("macOS PERFORMANS & SİSTEM SERVİSİ OPTİMİZASYONU", "DNS, Bellek, QuickLook, LaunchServices & Ses/BT", "🚀", tier="caution"))

        choices = [
            Choice("all", "⚡  Tüm Optimizasyonları Sırayla Çalıştır (1-5)"),
            Separator("--- Tekil Eylemler ---"),
            Choice("dns", "🌐  1. DNS Önbelleğini Temizle & Yenile (Flush DNS)"),
            Choice("quicklook", "🔍  2. QuickLook & Thumbnail Daemon Sıfırla"),
            Choice("launchservices", "📁  3. LaunchServices 'Birlikte Aç' Menüsünü Onar"),
            Choice("audio", "🎧  4. CoreAudio Ses Alt Sistemini Yeniden Başlat"),
            Choice("ram", "🧠  5. RAM / Bellek Senkronizasyonu (Purge)"),
            Choice("touchid", "🔐  6. Terminal Sudo için Touch ID Yapılandırması"),
            Choice("brew", "🍺  7. Homebrew Bakımı (cleanup & autoremove)"),
            Separator(),
            Choice("back", "Geri Dön")
        ]

        action = select_menu("Çalıştırmak istediğiniz optimizasyonu seçin:", choices)

        if action == "all":
            self.flush_dns()
            self.reset_quicklook()
            self.rebuild_launchservices()
            self.restart_audio()
            self.purge_ram()
        elif action == "brew":
            self.homebrew_maintenance()
        elif action == "dns":
            self.flush_dns()
        elif action == "quicklook":
            self.reset_quicklook()
        elif action == "launchservices":
            self.rebuild_launchservices()
        elif action == "audio":
            self.restart_audio()
        elif action == "ram":
            self.purge_ram()
        elif action == "touchid":
            self.setup_touchid()

    def flush_dns(self):
        try:
            subprocess.run(["dscacheutil", "-flushcache"], check=False)
            subprocess.run(["killall", "-HUP", "mDNSResponder"], check=False)
            console.print(f"[{C_EMERALD}]✓ DNS önbelleği başarıyla temizlendi ve mDNSResponder yenilendi.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def reset_quicklook(self):
        try:
            subprocess.run(["qlmanage", "-r"], check=False)
            subprocess.run(["qlmanage", "-r", "cache"], check=False)
            console.print(f"[{C_EMERALD}]✓ QuickLook önbellek ve servisleri başarıyla sıfırlandı.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def rebuild_launchservices(self):
        lsregister = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
        if os.path.exists(lsregister):
            try:
                subprocess.run([lsregister, "-kill", "-r", "-domain", "local", "-domain", "system", "-domain", "user"], check=False)
                subprocess.run(["killall", "Finder"], check=False)
                console.print(f"[{C_EMERALD}]✓ LaunchServices veritabanı yeniden oluşturuldu ve Finder yenilendi.[/]")
            except Exception as e:
                console.print(f"[{C_RED}]Hata: {e}[/]")
        else:
            console.print(f"[{C_AMBER}]lsregister aracı bulunamadı.[/]")

    def restart_audio(self):
        try:
            subprocess.run(["killall", "coreaudiod"], check=False)
            console.print(f"[{C_EMERALD}]✓ CoreAudio alt sistemi yeniden başlatıldı.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def purge_ram(self):
        try:
            res = subprocess.run(["purge"], check=False, stderr=subprocess.PIPE)
            if res.returncode == 0:
                console.print(f"[{C_EMERALD}]✓ Bellek başarıyla tazelendi.[/]")
            else:
                console.print(f"[{C_AMBER}]Bellek purge işlemi root izni gerektirebilir: 'sudo purge' komutunu çalıştırabilirsiniz.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def homebrew_maintenance(self):
        """Run `brew cleanup` (old formula/cask versions + download cache)
        and `brew autoremove` (formulae installed only as a now-unused
        dependency). Both are Homebrew's own standard maintenance commands —
        neither touches an explicitly-installed formula or cask you still
        depend on."""
        if not shutil.which("brew"):
            console.print(f"[{C_AMBER}]Homebrew bu sistemde kurulu değil, atlanıyor.[/]")
            return

        if not confirm_menu(
            "Homebrew eski sürümleri, indirme önbelleğini temizleyip artık gerekmeyen "
            "bağımlılık paketlerini (autoremove) kaldıracak. Devam edilsin mi?",
            default=False, danger=True
        ):
            return

        for cmd, label in [
            (["brew", "cleanup", "-s"], "Eski sürümler & indirme önbelleği"),
            (["brew", "autoremove"], "Artık gereksiz bağımlılıklar"),
        ]:
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                out = (res.stdout or "").strip()
                console.print(f"[{C_EMERALD}]✓ {label}:[/]")
                if out:
                    for line in out.splitlines()[:15]:
                        console.print(f"  [{C_MUTED}]{line}[/]")
                else:
                    console.print(f"  [{C_MUTED}]temiz[/]")
            except subprocess.TimeoutExpired:
                console.print(f"[{C_RED}]✖ {label}: zaman aşımı[/]")
            except Exception as e:
                console.print(f"[{C_RED}]✖ {label}: {e}[/]")
        console.print()

    def setup_touchid(self):
        pam_sudo = "/etc/pam.d/sudo"
        pam_tid = "auth       sufficient     pam_tid.so\n"
        try:
            with open(pam_sudo, 'r') as f:
                content = f.read()
            if "pam_tid.so" in content:
                console.print(f"[{C_EMERALD}]✓ Touch ID sudo yetkilendirmesi zaten aktif![/]")
            else:
                console.print(f"[{C_AMBER}]Touch ID'yi sudo için etkinleştirmek için şu komutu çalıştırabilirsiniz:[/]")
                console.print(f"[bold white]sudo sed -i '' '1s;^;auth       sufficient     pam_tid.so\\n;' /etc/pam.d/sudo[/]\n")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")
