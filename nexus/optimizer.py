import os
import re
import shutil
import subprocess
import time
import plistlib
import psutil
import resource
from typing import Dict, Any, List

from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from nexus.ui_helpers import (
    console, create_header, create_gauge, format_bytes, create_spinner,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK,
    C_SAFE, C_WARN, C_DANGER
)
from nexus.menu_helpers import select_menu, confirm_menu, format_menu_item
from InquirerPy.base.control import Choice
from InquirerPy.separator import Separator


class SystemOptimizer:
    """MacBook Health, Deep Diagnostics & Performance Optimization Suite."""

    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # 1. Telemetry & Health Diagnostics Audit Engine
    # -------------------------------------------------------------------------
    def get_health_audit(self) -> Dict[str, Any]:
        """Perform a comprehensive health and stability audit of the MacBook."""
        audit: Dict[str, Any] = {
            "battery": {
                "percent": 100,
                "state": "Bilinmiyor",
                "health_percent": 100.0,
                "condition": "Normal",
                "cycle_count": 0,
                "max_capacity_mah": 0,
                "design_capacity_mah": 0,
                "is_charging": False
            },
            "memory": {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "pressure_percent": 0.0,
                "swap_used_bytes": 0,
                "swap_total_bytes": 0,
                "compressed_gb": 0.0,
                "wired_gb": 0.0
            },
            "storage": {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "percent": 0.0,
                "local_snapshots_count": 0,
                "local_snapshots": []
            },
            "thermal": {
                "status": "Optimal (Kısıtlama Yok)",
                "throttled": False,
                "scheduler_limit": 100
            },
            "stability": {
                "recent_crash_count": 0,
                "top_crashing_apps": []
            },
            "startup": {
                "total_agents": 0,
                "orphan_agents_count": 0,
                "orphan_agents": []
            },
            "score": 100,
            "status_label": "Mükemmel",
            "status_color": C_EMERALD,
            "recommendations": []
        }

        # --- A. Battery Telemetry (ioreg + pmset) ---
        try:
            raw_batt = subprocess.check_output(["pmset", "-g", "batt"], text=True, stderr=subprocess.DEVNULL)
            m_pct = re.search(r"(\d+)%", raw_batt)
            if m_pct:
                audit["battery"]["percent"] = int(m_pct.group(1))

            raw_lower = raw_batt.lower()
            if "discharging" in raw_lower:
                audit["battery"]["state"] = "Pilde (Deşarj)"
            elif "not charging" in raw_lower or "charged" in raw_lower:
                audit["battery"]["state"] = "AC Adaptöründe"
            elif "charging" in raw_lower:
                audit["battery"]["state"] = "Şarj Oluyor (AC)"
                audit["battery"]["is_charging"] = True
            elif "ac" in raw_lower:
                audit["battery"]["state"] = "AC Adaptörüne Bağlı"
        except Exception:
            pass

        try:
            ioreg = subprocess.check_output(["ioreg", "-r", "-c", "AppleSmartBattery"], text=True, stderr=subprocess.DEVNULL)
            m_cycle = re.search(r'"CycleCount"\s*=\s*(\d+)', ioreg)
            if m_cycle:
                audit["battery"]["cycle_count"] = int(m_cycle.group(1))

            m_cond = re.search(r'"Condition"\s*=\s*"([^"]+)"', ioreg)
            if m_cond:
                audit["battery"]["condition"] = m_cond.group(1)

            m_full = re.search(r'"FullChargeCapacity"\s*=\s*(\d+)', ioreg)
            m_design = re.search(r'"DesignCapacity"\s*=\s*(\d+)', ioreg)
            if m_full and m_design:
                full_mah = int(m_full.group(1))
                design_mah = int(m_design.group(1))
                audit["battery"]["max_capacity_mah"] = full_mah
                audit["battery"]["design_capacity_mah"] = design_mah
                if design_mah > 0:
                    health_pct = min(100.0, round((full_mah / design_mah) * 100.0, 1))
                    audit["battery"]["health_percent"] = health_pct
        except Exception:
            pass

        # --- B. Memory & Pressure Telemetry ---
        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()
            audit["memory"]["total_bytes"] = vm.total
            audit["memory"]["used_bytes"] = vm.used
            audit["memory"]["free_bytes"] = vm.available
            audit["memory"]["swap_used_bytes"] = swap.used
            audit["memory"]["swap_total_bytes"] = swap.total

            page_size = resource.getpagesize() if hasattr(resource, 'getpagesize') else 16384
            vm_stat = subprocess.check_output(["vm_stat"], text=True, stderr=subprocess.DEVNULL)
            stats = {}
            lines = vm_stat.splitlines()
            if lines and "page size of" in lines[0]:
                m_pg = re.search(r"page size of (\d+) bytes", lines[0])
                if m_pg:
                    page_size = int(m_pg.group(1))

            for line in lines:
                if ":" in line:
                    parts = line.split(":")
                    val = parts[1].strip().rstrip(".")
                    if val.isdigit():
                        stats[parts[0].strip()] = int(val) * page_size

            free = stats.get("Pages free", 0) + stats.get("Pages speculative", 0)
            active = stats.get("Pages active", 0)
            wired = stats.get("Pages wired down", 0)
            compressed = stats.get("Pages occupied by compressor", 0)
            total = free + active + stats.get("Pages inactive", 0) + wired + compressed
            if total > 0:
                pressure = round(((active + wired + compressed) / total) * 100.0, 1)
            else:
                pressure = float(vm.percent)

            audit["memory"]["pressure_percent"] = pressure
            audit["memory"]["compressed_gb"] = round(compressed / (1024**3), 2)
            audit["memory"]["wired_gb"] = round(wired / (1024**3), 2)
        except Exception:
            pass

        # --- C. Storage & APFS Snapshots ---
        try:
            usage = psutil.disk_usage('/')
            audit["storage"]["total_bytes"] = usage.total
            audit["storage"]["used_bytes"] = usage.used
            audit["storage"]["free_bytes"] = usage.free
            audit["storage"]["percent"] = float(usage.percent)
        except Exception:
            pass

        try:
            tm_raw = subprocess.check_output(["tmutil", "listlocalsnapshots", "/"], text=True, stderr=subprocess.DEVNULL)
            snaps = [s.strip() for s in tm_raw.splitlines() if "com.apple.TimeMachine" in s]
            audit["storage"]["local_snapshots"] = snaps
            audit["storage"]["local_snapshots_count"] = len(snaps)
        except Exception:
            pass

        # --- D. Thermal & CPU Throttling ---
        try:
            therm_raw = subprocess.check_output(["pmset", "-g", "therm"], text=True, stderr=subprocess.DEVNULL)
            if "CPU_Scheduler_Limit" in therm_raw:
                m_lim = re.search(r"CPU_Scheduler_Limit\s*=\s*(\d+)", therm_raw)
                if m_lim:
                    limit_val = int(m_lim.group(1))
                    audit["thermal"]["scheduler_limit"] = limit_val
                    if limit_val < 100:
                        audit["thermal"]["throttled"] = True
                        audit["thermal"]["status"] = f"Kısıtlama Aktif (Limit: %{limit_val})"
            elif "Warning" in therm_raw:
                audit["thermal"]["status"] = "Termal Uyarı Kaydı Var"
        except Exception:
            pass

        # --- E. System Stability & Crash Reports (Last 7 Days) ---
        now = time.time()
        seven_days_sec = 7 * 86400
        crash_counts_by_app: Dict[str, int] = {}
        total_crashes = 0
        for report_dir in [os.path.expanduser("~/Library/Logs/DiagnosticReports"), "/Library/Logs/DiagnosticReports"]:
            if os.path.exists(report_dir):
                try:
                    for entry in os.listdir(report_dir):
                        if entry.endswith((".ips", ".crash", ".panic")):
                            fp = os.path.join(report_dir, entry)
                            if os.path.isfile(fp):
                                try:
                                    mtime = os.path.getmtime(fp)
                                    if (now - mtime) <= seven_days_sec:
                                        total_crashes += 1
                                        app_name = entry.split("-")[0].split("_")[0].replace(".ips", "").replace(".crash", "")
                                        crash_counts_by_app[app_name] = crash_counts_by_app.get(app_name, 0) + 1
                                except OSError:
                                    continue
                except OSError:
                    continue

        audit["stability"]["recent_crash_count"] = total_crashes
        sorted_crashes = sorted(crash_counts_by_app.items(), key=lambda x: x[1], reverse=True)
        audit["stability"]["top_crashing_apps"] = sorted_crashes[:3]

        # --- F. Startup Items & Background LaunchAgents ---
        agents_found = 0
        orphan_agents = []
        for base_dir in [os.path.expanduser("~/Library/LaunchAgents"), "/Library/LaunchAgents", "/Library/LaunchDaemons"]:
            if os.path.exists(base_dir):
                try:
                    for fname in os.listdir(base_dir):
                        if fname.endswith(".plist"):
                            agents_found += 1
                            fpath = os.path.join(base_dir, fname)
                            try:
                                with open(fpath, "rb") as pl_file:
                                    data = plistlib.load(pl_file)
                                    prog = data.get("Program")
                                    if not prog and data.get("ProgramArguments"):
                                        args = data.get("ProgramArguments")
                                        if isinstance(args, list) and len(args) > 0:
                                            prog = args[0]
                                    if prog and isinstance(prog, str) and prog.startswith("/") and not os.path.exists(prog):
                                        orphan_agents.append({
                                            "file": fname,
                                            "path": fpath,
                                            "label": data.get("Label", fname),
                                            "missing_target": prog
                                        })
                            except Exception:
                                continue
                except OSError:
                    continue

        audit["startup"]["total_agents"] = agents_found
        audit["startup"]["orphan_agents_count"] = len(orphan_agents)
        audit["startup"]["orphan_agents"] = orphan_agents

        # --- G. Health Score & Recommendations Calculation ---
        score = 100
        recs = []

        # 1. Memory deductions
        press = audit["memory"]["pressure_percent"]
        if press >= 80:
            score -= 15
            recs.append(f"🧠 Bellek baskısı yüksek (%{press:.1f}). RAM Purge ve gereksiz uygulamaların kapatılması önerilir.")
        elif press >= 65:
            score -= 8
            recs.append(f"🧠 Bellek baskısı orta seviyede (%{press:.1f}). RAM senkronizasyonu önerilir.")

        swap_used_mb = audit["memory"]["swap_used_bytes"] / (1024 * 1024)
        if swap_used_mb > 2048:
            score -= 10
            recs.append(f"💾 Swap kullanımı yüksek ({format_bytes(audit['memory']['swap_used_bytes'])}). Yeniden başlatma veya RAM optimizasyonu faydalı olur.")
        elif swap_used_mb > 500:
            score -= 5

        # 2. Storage deductions
        disk_pct = audit["storage"]["percent"]
        if disk_pct >= 90:
            score -= 20
            recs.append(f"⚠️ Disk doluluk oranı kritik seviyede (%{disk_pct:.1f}). Sistem ve geliştirici çöplerini temizleyin.")
        elif disk_pct >= 80:
            score -= 10
            recs.append(f"💾 Disk doluluk oranı yüksek (%{disk_pct:.1f}). Alan boşaltılması performansı artırır.")

        if audit["storage"]["local_snapshots_count"] > 3:
            score -= 5
            recs.append(f"💾 {audit['storage']['local_snapshots_count']} adet Time Machine yerel APFS snapshot birikmiş. Seyreltme (Thinning) önerilir.")

        # 3. Battery deductions
        if audit["battery"]["condition"].lower() not in ["normal", "bilinmiyor"]:
            score -= 20
            recs.append(f"🔋 Pil kondisyonu '{audit['battery']['condition']}'. Apple Yetkili Servisi kontrolü gerekebilir.")
        elif audit["battery"]["health_percent"] < 80.0 and audit["battery"]["health_percent"] > 0:
            score -= 10
            recs.append(f"🔋 Pil sağlığı maksimum kapasitesi %{audit['battery']['health_percent']} seviyesine düşmüş.")

        if audit["battery"]["cycle_count"] > 1000:
            score -= 10
            recs.append(f"🔋 Pil döngü sayısı yüksek ({audit['battery']['cycle_count']} döngü).")

        # 4. Thermal deductions
        if audit["thermal"]["throttled"]:
            score -= 15
            recs.append("🌡️ Termal kısıtlama (Thermal Throttling) devrede! Fan deliklerini kontrol edin veya CPU yükünü azaltın.")

        # 5. Stability deductions
        if total_crashes > 25:
            score -= 15
            recs.append(f"⚠️ Son 7 günde {total_crashes} adet sistem/uygulama çökme kaydı var. Sorunlu uygulamaları inceleyin.")
        elif total_crashes > 5:
            score -= 5

        # 6. Orphan Startup Agents
        if len(orphan_agents) > 0:
            score -= min(10, len(orphan_agents) * 3)
            recs.append(f"🚀 {len(orphan_agents)} adet hedef dosyası silinmiş yetim LaunchAgent arka planda döngüde kalıyor.")

        # General tune-up recommendation
        if not recs:
            recs.append("✨ Tebrikler! Sisteminiz harika durumda. Periyodik olarak 1-Tıkla İyileştirme yapabilirsiniz.")

        score = max(10, min(100, score))
        audit["score"] = score

        if score >= 90:
            audit["status_label"] = "🌟 MÜKEMMEL (A+) - Zirve Performans"
            audit["status_color"] = C_EMERALD
        elif score >= 75:
            audit["status_label"] = "🟢 SAĞLIKLI (B) - Stabil Durum"
            audit["status_color"] = C_GREEN
        elif score >= 60:
            audit["status_label"] = "🟡 DİKKAT (C) - Bakım Tavsiye Edilir"
            audit["status_color"] = C_AMBER
        else:
            audit["status_label"] = "🔴 KRİTİK (D) - Kapsamlı Bakım Gerekli"
            audit["status_color"] = C_RED

        audit["recommendations"] = recs
        return audit

    # -------------------------------------------------------------------------
    # 2. Visual Health Audit Dashboard Render
    # -------------------------------------------------------------------------
    def render_health_audit(self):
        """Render the rich MacBook Health Audit and Diagnostics dashboard."""
        with create_spinner("MacBook donanım, termal, bellek ve kararlılık teşhisi yapılıyor..."):
            audit = self.get_health_audit()

        console.print(create_header("MACBOOK SAĞLIK & DERİN TEŞHİS RAPORU", "Donanım, Termal, Bellek, Pil, APFS & Kararlılık Skoru", "🩺", tier="safe"))

        # --- Top Health Score Card ---
        score = audit["score"]
        score_color = audit["status_color"]
        score_gauge = create_gauge(score, width=28)

        score_text = Text()
        score_text.append("\n  MacBook Genel Sağlık Puanı: ", style="bold white")
        score_text.append(f" {score} / 100  ", style=f"bold white on {score_color}")
        score_text.append(f"   {score_gauge}\n", style="bold")
        score_text.append(f"  Durum: [{score_color}]{audit['status_label']}[/{score_color}]\n", style="bold")

        score_panel = Panel(
            score_text,
            box=box.ROUNDED,
            border_style=score_color,
            title="[bold white] GENEL SAĞLIK & PERFORMANS ENDEKSİ [/]",
            style=f"on {C_DARK}",
            padding=(0, 1)
        )
        console.print(score_panel)
        console.print()

        # --- 6 Dimension Telemetry Grid ---
        table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style=f"bold {C_CYAN}", expand=True)
        table.add_column("Bileşen & Alan", style="bold white", width=22)
        table.add_column("Canlı Telemetri & Metrikler", style=C_BLUE)
        table.add_column("Durum & Gösterge", style="bold")

        # 1. Battery
        batt = audit["battery"]
        batt_details = f"Kapasite: {batt['health_percent']}% | {batt['cycle_count']} Döngü\nŞarj: %{batt['percent']} ({batt['state']})"
        batt_cond = f"[{C_EMERALD}]✓ {batt['condition']}[/]" if batt['condition'].lower() in ['normal', 'bilinmiyor'] else f"[{C_RED}]✖ {batt['condition']}[/]"
        table.add_row("🔋 Pil & Güç", batt_details, batt_cond)

        # 2. Memory
        mem = audit["memory"]
        mem_details = f"Baskı: %{mem['pressure_percent']} | Sıkıştırılmış: {mem['compressed_gb']} GB\nWired: {mem['wired_gb']} GB | Swap: {format_bytes(mem['swap_used_bytes'])}"
        table.add_row("🧠 RAM / Bellek", mem_details, create_gauge(mem["pressure_percent"], width=16))

        # 3. Storage & APFS
        stor = audit["storage"]
        stor_details = f"Boş Alan: {format_bytes(stor['free_bytes'])} / {format_bytes(stor['total_bytes'])}\nAPFS Snapshots: {stor['local_snapshots_count']} Yerel Yedek"
        table.add_row("💾 Disk & APFS", stor_details, create_gauge(stor["percent"], width=16))

        # 4. Thermal & CPU
        therm = audit["thermal"]
        therm_details = f"{therm['status']}\nCPU Zamanlayıcı Limiti: %{therm['scheduler_limit']}"
        therm_badge = f"[{C_EMERALD}]✓ Normal[/]" if not therm["throttled"] else f"[{C_RED}]⚠️ Kısıtlandı[/]"
        table.add_row("🌡️ Termal & Isı", therm_details, therm_badge)

        # 5. Stability & Crashes
        stab = audit["stability"]
        if stab["recent_crash_count"] == 0:
            stab_details = "Son 7 günde sıfır çökme/hata kaydı."
            stab_badge = f"[{C_EMERALD}]✓ Kusursuz[/]"
        else:
            top_apps = ", ".join([f"{k} ({v})" for k, v in stab["top_crashing_apps"]])
            stab_details = f"Son 7 günde {stab['recent_crash_count']} rapor\nSık çökenler: {top_apps}"
            stab_badge = f"[{C_AMBER}]⚠️ {stab['recent_crash_count']} Çökme[/]"
        table.add_row("⚠️ Kararlılık (Log)", stab_details, stab_badge)

        # 6. Startup & LaunchAgents
        start = audit["startup"]
        start_details = f"Aktif Ajan: {start['total_agents']} Servis\nYetim (Silinmiş Uygulama): {start['orphan_agents_count']} Adet"
        start_badge = f"[{C_EMERALD}]✓ Temiz[/]" if start["orphan_agents_count"] == 0 else f"[{C_RED}]⚠️ {start['orphan_agents_count']} Yetim Ajan[/]"
        table.add_row("🚀 Başlangıç Yükü", start_details, start_badge)

        console.print(table)
        console.print()

        # --- Recommendations Panel ---
        rec_text = Text()
        for idx, rec in enumerate(audit["recommendations"], 1):
            rec_text.append(f"  {idx}. {rec}\n", style="white")

        console.print(Panel(
            rec_text,
            box=box.ROUNDED,
            border_style=C_CYAN,
            title="[bold #00f0ff] 🎯 AKILLI SAĞLIK REÇETESİ & ÖNERİLER [/]",
            style=f"on {C_DARK}",
            padding=(0, 1)
        ))

    # -------------------------------------------------------------------------
    # 3. 1-Click Full MacBook Tune-Up & Deep Optimization
    # -------------------------------------------------------------------------
    def run_full_optimization(self):
        """Execute a comprehensive, 1-click safe MacBook optimization sequence."""
        console.print(create_header("1-TIKLA TAM MACBOOK İYİLEŞTİRME & CANLANDIRMA", "RAM, DNS, QuickLook, LaunchServices, Font, Audio & APFS", "⚡", tier="caution"))

        if not confirm_menu(
            "MacBook'un tüm sistem önbellekleri, DNS, QuickLook, LaunchServices, "
            "Font kayıtları ve RAM senkronizasyonu sırayla optimize edilecek. Devam edilsin mi?",
            default=True
        ):
            return

        console.print(f"\n[bold {C_CYAN}]⚡ Tam MacBook Canlandırma Operasyonu Başlatılıyor...[/]\n")

        steps = [
            ("🧠 1. RAM / Bellek Baskısı Tahliyesi", self.purge_ram),
            ("🌐 2. DNS & Ağ Alt Sistemi Yenileme", self.flush_dns),
            ("🔍 3. QuickLook & Thumbnail Daemon Sıfırlama", self.reset_quicklook),
            ("📁 4. LaunchServices 'Birlikte Aç' Menüsü Onarımı", self.rebuild_launchservices),
            ("🔤 5. Font & FontRegistry Önbelleği Sıfırlama", self.repair_font_cache),
            ("🎧 6. CoreAudio Ses Alt Sistemini Yeniden Başlatma", self.restart_audio),
            ("🔎 7. Spotlight Arama Servislerini Tazeleme", self.refresh_spotlight),
            ("💾 8. APFS Time Machine Yerel Snapshot Seyreltme", self.clean_local_snapshots),
            ("🧹 9. Kullanıcı Geçici IPC/Socket/Lock Temizliği", self.clean_stale_ipc)
        ]

        for label, func in steps:
            console.print(f"[bold white]{label}...[/]")
            func()
            console.print()

        console.print(f"[{C_EMERALD}]✨ MacBook cihazınızın tüm sistem servisleri ve önbellekleri başarıyla optimize edildi![/]\n")

    # -------------------------------------------------------------------------
    # 4. Individual Modular Optimization Actions
    # -------------------------------------------------------------------------
    def flush_dns(self):
        """Flush DNS cache and restart mDNSResponder."""
        try:
            subprocess.run(["dscacheutil", "-flushcache"], check=False)
            subprocess.run(["killall", "-HUP", "mDNSResponder"], check=False)
            console.print(f"[{C_EMERALD}]✓ DNS önbelleği başarıyla temizlendi ve mDNSResponder yenilendi.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def reset_quicklook(self):
        """Reset QuickLook daemon and purge icon/thumbnail caches."""
        try:
            subprocess.run(["qlmanage", "-r"], check=False)
            subprocess.run(["qlmanage", "-r", "cache"], check=False)
            console.print(f"[{C_EMERALD}]✓ QuickLook önbellek ve servisleri başarıyla sıfırlandı.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def rebuild_launchservices(self):
        """Rebuild LaunchServices database and refresh Finder."""
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

    def repair_font_cache(self):
        """Repair corrupted macOS font registry caches to fix UI glitches."""
        try:
            font_cache = os.path.expanduser("~/Library/Caches/com.apple.FontRegistry")
            if os.path.exists(font_cache):
                shutil.rmtree(font_cache, ignore_errors=True)

            if shutil.which("atsutil"):
                subprocess.run(["atsutil", "databases", "-removeUser"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            console.print(f"[{C_EMERALD}]✓ macOS Font ve FontRegistry önbellekleri başarıyla sıfırlandı.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def restart_audio(self):
        """Restart CoreAudio daemon to resolve sound crackling and bluetooth sync issues."""
        try:
            subprocess.run(["killall", "coreaudiod"], check=False)
            console.print(f"[{C_EMERALD}]✓ CoreAudio alt sistemi yeniden başlatıldı.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def purge_ram(self):
        """Purge inactive memory pages and relieve system memory pressure."""
        try:
            res = subprocess.run(["purge"], check=False, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if res.returncode == 0:
                console.print(f"[{C_EMERALD}]✓ Bellek ve disk önbellekleri başarıyla tahliye edildi.[/]")
            else:
                console.print(f"[{C_AMBER}]Bellek purge işlemi root izni gerektirebilir: 'sudo purge' komutunu çalıştırabilirsiniz.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def refresh_spotlight(self):
        """Refresh and unstick Spotlight indexing processes."""
        try:
            subprocess.run(["killall", "mdworker"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["killall", "mdworker_shared"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            res = subprocess.run(["mdutil", "-s", "/"], capture_output=True, text=True, check=False)
            status_out = res.stdout.strip() if res.stdout else "İndeksleme aktif"
            console.print(f"[{C_EMERALD}]✓ Spotlight arama servisleri tazelendi. ({status_out})[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def clean_local_snapshots(self):
        """Thin out local APFS Time Machine snapshots to recover gigabytes of hidden space."""
        try:
            res = subprocess.run(["tmutil", "listlocalsnapshots", "/"], capture_output=True, text=True, check=False)
            snaps = [s.strip() for s in (res.stdout or "").splitlines() if "com.apple.TimeMachine" in s]
            if not snaps:
                console.print(f"[{C_EMERALD}]✓ Diskte temizlenecek yerel Time Machine snapshot bulunamadı.[/]")
                return

            console.print(f"[{C_CYAN}]ℹ {len(snaps)} adet yerel APFS snapshot bulundu, seyreltiliyor...[/]")
            subprocess.run(["tmutil", "thinlocalsnapshots", "/", "99999999999", "4"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print(f"[{C_EMERALD}]✓ Yerel APFS Time Machine snapshotları başarıyla seyreltildi ve boş alan kazanıldı.[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def clean_stale_ipc(self):
        """Clean stale user IPC socket / lock files left by crashed apps."""
        try:
            temp_items = os.path.expanduser("~/Library/Caches/TemporaryItems")
            cleaned = 0
            if os.path.exists(temp_items):
                for item in os.listdir(temp_items):
                    ipath = os.path.join(temp_items, item)
                    try:
                        if os.path.islink(ipath) or os.path.isfile(ipath):
                            os.unlink(ipath)
                            cleaned += 1
                        elif os.path.isdir(ipath):
                            shutil.rmtree(ipath, ignore_errors=True)
                            cleaned += 1
                    except OSError:
                        continue
            console.print(f"[{C_EMERALD}]✓ Askıda kalan geçici soket ve kilit dosyaları temizlendi ({cleaned} öğe).[/]")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    def inspect_launch_agents(self):
        """Inspect and audit user & system LaunchAgents, detect broken/orphaned background items."""
        console.print(create_header("BAŞLANGIÇ VE ARKA PLAN AJANLARI DENETİMİ", "LaunchAgents, LaunchDaemons & Yetim Süreç Avcısı", "🚀", tier="safe"))

        agents = []
        paths = [
            (os.path.expanduser("~/Library/LaunchAgents"), "Kullanıcı"),
            ("/Library/LaunchAgents", "Sistem (Kullanıcı)"),
            ("/Library/LaunchDaemons", "Sistem (Daemon)")
        ]

        for base_dir, scope in paths:
            if not os.path.exists(base_dir):
                continue
            for fname in os.listdir(base_dir):
                if not fname.endswith(".plist"):
                    continue
                fpath = os.path.join(base_dir, fname)
                item = {
                    "filename": fname,
                    "path": fpath,
                    "scope": scope,
                    "label": fname,
                    "program": "-",
                    "exists": True
                }
                try:
                    with open(fpath, "rb") as f:
                        data = plistlib.load(f)
                        item["label"] = data.get("Label", fname)
                        prog = data.get("Program")
                        if not prog and data.get("ProgramArguments"):
                            args = data.get("ProgramArguments")
                            if isinstance(args, list) and len(args) > 0:
                                prog = args[0]
                        if prog and isinstance(prog, str):
                            item["program"] = prog
                            if prog.startswith("/"):
                                item["exists"] = os.path.exists(prog)
                except Exception as e:
                    item["error"] = str(e)
                agents.append(item)

        if not agents:
            console.print(f"[{C_EMERALD}]✓ Sistemde incelenecek LaunchAgent bulunamadı.[/]")
            return

        table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style=f"bold {C_CYAN}", expand=True)
        table.add_column("Servis / Ajan Adı (Label)", style="bold white", width=36)
        table.add_column("Kapsam", style=C_MUTED, width=16)
        table.add_column("Hedef Program Dosyası", style=C_BLUE)
        table.add_column("Durum", style="bold", width=16)

        orphans = []
        for a in agents:
            if not a["exists"]:
                status = f"[{C_RED}]✖ Yetim (Yok)[/]"
                orphans.append(a)
            else:
                status = f"[{C_EMERALD}]✓ Aktif[/]"
            table.add_row(a["label"][:36], a["scope"], a["program"][:45], status)

        console.print(table)
        console.print(f"\n[bold white]Toplam {len(agents)} başlangıç ajanı bulundu.[/] (Yetim/Bozuk: [{C_RED if orphans else C_EMERALD}]{len(orphans)}[/{C_RED if orphans else C_EMERALD}])\n")

        if orphans:
            if confirm_menu(f"{len(orphans)} adet silinmiş uygulamaya ait yetim .plist dosyasını kaldırmak ister misiniz?", default=False, danger=True):
                for orp in orphans:
                    try:
                        os.remove(orp["path"])
                        console.print(f"[{C_EMERALD}]✓ Kaldırıldı:[/] {orp['filename']}")
                    except Exception as e:
                        console.print(f"[{C_RED}]✖ Kaldırılamadı:[/] {orp['filename']} ({e})")
                console.print()

    def homebrew_maintenance(self):
        """Run `brew cleanup` and `brew autoremove`."""
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
        """Configure Touch ID for sudo command authentication in terminal."""
        pam_sudo = "/etc/pam.d/sudo"
        pam_local = "/etc/pam.d/sudo_local"
        pam_template = "/etc/pam.d/sudo_local.template"
        try:
            active = False
            for path in [pam_local, pam_sudo]:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        for line in f:
                            if "pam_tid.so" in line and not line.strip().startswith("#"):
                                active = True
                                break
                if active:
                    break

            if active:
                console.print(f"[{C_EMERALD}]✓ Touch ID sudo yetkilendirmesi sisteminizde zaten aktif ve çalışıyor![/]")
            else:
                console.print(f"[{C_AMBER}]Touch ID'yi sudo için sistem güncellemelerinde sıfırlanmayacak şekilde kalıcı etkinleştirmek için:[/]")
                if os.path.exists(pam_template):
                    console.print(f"[bold white]sudo cp /etc/pam.d/sudo_local.template /etc/pam.d/sudo_local && sudo sed -i '' 's/#auth/auth/' /etc/pam.d/sudo_local[/]\n")
                else:
                    console.print(f"[bold white]sudo sed -i '' '1s;^;auth       sufficient     pam_tid.so\\n;' /etc/pam.d/sudo[/]\n")
        except Exception as e:
            console.print(f"[{C_RED}]Hata: {e}[/]")

    # -------------------------------------------------------------------------
    # 5. Interactive Menu Render
    # -------------------------------------------------------------------------
    def render(self):
        """Render MacBook Health and Optimization module menu."""
        while True:
            os.system("clear")
            console.print(create_header("MACBOOK SAĞLIK & DERİN OPTİMİZASYON MERKEZİ", "Sağlık Skoru, RAM, Termal, DNS, QuickLook, Font & APFS", "🩺", tier="caution"))

            choices = [
                Choice("audit", "🩺  1. MacBook Sağlık Raporu & Detaylı Teşhis (Health Audit)"),
                Choice("all", "⚡  2. 1-Tıkla Tam MacBook İyileştirme & Canlandırma (Tüm Servisler)"),
                Separator("--- 🎯 Hedefli Sistem Optimizasyonları ---"),
                Choice("ram", "🧠  3. RAM / Bellek Baskısı Tahliyesi (Purge Memory)"),
                Choice("dns", "🌐  4. DNS Önbelleğini Temizle & Yenile (Flush DNS)"),
                Choice("quicklook", "🔍  5. QuickLook & Finder Simge/Önizleme Daemon Sıfırla"),
                Choice("launchservices", "📁  6. LaunchServices 'Birlikte Aç' Menüsünü Onar"),
                Choice("font", "🔤  7. Font (Yazı Tipi) Önbelleğini Sıfırla & Onar"),
                Choice("spotlight", "🔎  8. Spotlight İndeksleme ve Arama Hızlandırma"),
                Choice("snapshots", "💾  9. Time Machine Yerel APFS Snapshot Temizliği"),
                Choice("agents", "🚀 10. Başlangıç & Arka Plan Ajanları (LaunchAgents) Denetimi"),
                Choice("audio", "🎧 11. CoreAudio Ses Alt Sistemini Yeniden Başlat"),
                Choice("brew", "🍺 12. Homebrew Bakımı (cleanup & autoremove)"),
                Choice("touchid", "🔐 13. Terminal Sudo için Touch ID Yapılandırması"),
                Separator("────────────────────────────────────────────────────────────────────────────"),
                Choice("back", "⬅️  Ana Menüye Dön")
            ]

            action = select_menu("Çalıştırmak istediğiniz sağlık / optimizasyon işlemini seçin:", choices)

            if not action or action == "back":
                break
            elif action == "audit":
                os.system("clear")
                self.render_health_audit()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "all":
                os.system("clear")
                self.run_full_optimization()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "ram":
                os.system("clear")
                self.purge_ram()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "dns":
                os.system("clear")
                self.flush_dns()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "quicklook":
                os.system("clear")
                self.reset_quicklook()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "launchservices":
                os.system("clear")
                self.rebuild_launchservices()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "font":
                os.system("clear")
                self.repair_font_cache()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "spotlight":
                os.system("clear")
                self.refresh_spotlight()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "snapshots":
                os.system("clear")
                self.clean_local_snapshots()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "agents":
                os.system("clear")
                self.inspect_launch_agents()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "audio":
                os.system("clear")
                self.restart_audio()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "brew":
                os.system("clear")
                self.homebrew_maintenance()
                input("\nDevam etmek için Enter'a basın...")
            elif action == "touchid":
                os.system("clear")
                self.setup_touchid()
                input("\nDevam etmek için Enter'a basın...")

