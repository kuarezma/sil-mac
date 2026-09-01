import sys
import os
import argparse
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from nexus.banner import print_banner
from nexus.ui_helpers import (
    console, create_header,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import select_menu, confirm_menu
from nexus.deletion_engine import execute_deletion_with_live_report
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator

from nexus.ai_radar import AIRadar
from nexus.dev_cleaner import DevCleaner
from nexus.system_cleaner import SystemCleaner
from nexus.app_uninstaller import AppUninstaller
from nexus.hardware_dashboard import HardwareDashboard
from nexus.port_radar import PortRadar
from nexus.optimizer import SystemOptimizer

def show_main_menu():
    """Display interactive main menu with laser-aligned columns."""
    while True:
        os.system("clear")
        print_banner()

        choices = [
            Choice("ai",       "🤖   AI & Yerel Model Radarı        │  Hugging Face, Ollama, MLX, Torch, GGUF"),
            Choice("dev",      "💻   Geliştirici Önbellekleri       │  Xcode, Android, Node, Rust, Python, Go"),
            Choice("clean",    "🧹   macOS Sistem & Temizlik        │  Önbellekler, Günlükler, Tarayıcılar, Çöp"),
            Choice("apps",     "🗑️   Akıllı Uygulama Kaldırıcı      │  Kalıntısız silme & Yetim artık avcısı"),
            Choice("status",   "⚡   Donanım & Telemetri Paneli     │  Apple Silicon M-Serisi, RAM, Pil, Disk"),
            Choice("ports",    "📡   Port & Hayalet Süreç Radarı    │  Açık Portlar, Bellek Sömürenler & Kill"),
            Choice("optimize", "🚀   macOS Servis Optimizasyonu     │  DNS, RAM Senkronizasyonu, QuickLook"),
            Choice("quick",    "✨   Hızlı Akıllı Temizlik          │  Güvenli sistem çöpleri & AI yetimleri"),
            Separator("────────────────────────────────────────────────────────────────────────────"),
            Choice("exit",     "❌   Çıkış                          │  Nexus konsolundan ayrıl")
        ]

        action = select_menu("Çalıştırmak istediğiniz modülü yön tuşlarıyla seçin:", choices)

        if not action or action == "exit":
            console.print(f"\n[bold {C_CYAN}]Nexus'tan çıkılıyor. İyi çalışmalar![/]\n")
            break
        elif action == "ai":
            os.system("clear")
            AIRadar().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "dev":
            os.system("clear")
            DevCleaner().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "clean":
            os.system("clear")
            SystemCleaner().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "apps":
            os.system("clear")
            AppUninstaller().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "status":
            os.system("clear")
            HardwareDashboard().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "ports":
            os.system("clear")
            PortRadar().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "optimize":
            os.system("clear")
            SystemOptimizer().render()
            input("\nAna menüye dönmek için Enter'a basın...")
        elif action == "quick":
            os.system("clear")
            _quick_clean()
            input("\nAna menüye dönmek için Enter'a basın...")

def _quick_clean():
    """Run safe quick cleaning across multiple modules with live visual report."""
    console.print(create_header("HIZLI & GÜVENLİ SİSTEM TEMİZLİĞİ", "Güvenli Sistem Önbellekleri, Günlükler & AI Yetimleri", "✨"))
    
    if not confirm_menu("Güvenli sistem çöpleri, günlükler ve yetim AI dosyaları otomatik temizlensin mi?", default=True):
        return

    sc = SystemCleaner()
    sys_items = sc.scan()
    safe_sys = [it for it in sys_items if it['category'] in ['Sistem', 'Günlükler', 'Tanılama', 'Çöp']]

    ai = AIRadar()
    ai_items = ai.scan()
    safe_ai = [it for it in ai_items if "orphan" in it['category'] or "temp" in it['category']]

    combined_items = safe_sys + safe_ai
    if combined_items:
        execute_deletion_with_live_report(combined_items, "Hızlı Akıllı Temizlik")
    else:
        console.print(f"\n[{C_EMERALD}]✓ Temizlenecek güvenli çöp veya artık bulunamadı. Sistem zaten temiz![/]\n")

def main():
    parser = argparse.ArgumentParser(description="Nexus: Next-Gen macOS Deep Optimizer & AI/Dev Powerhouse")
    parser.add_argument("module", nargs="?", choices=["ai", "dev", "clean", "apps", "status", "system", "ports", "optimize", "quick"], help="Doğrudan çalıştırılacak modül")
    parser.add_argument("--version", "-v", action="version", version="Nexus 2.0.0 Pro (macOS Apple Silicon Native)")

    args = parser.parse_args()

    if not args.module:
        show_main_menu()
    elif args.module == "ai":
        print_banner()
        AIRadar().render()
    elif args.module == "dev":
        print_banner()
        DevCleaner().render()
    elif args.module in ["clean"]:
        print_banner()
        SystemCleaner().render()
    elif args.module == "apps":
        print_banner()
        AppUninstaller().render()
    elif args.module in ["status", "system"]:
        print_banner()
        HardwareDashboard().render()
    elif args.module == "ports":
        print_banner()
        PortRadar().render()
    elif args.module == "optimize":
        print_banner()
        SystemOptimizer().render()
    elif args.module == "quick":
        print_banner()
        _quick_clean()

if __name__ == "__main__":
    main()
