import os
import sys
import time
import json
import shutil
import datetime
from typing import List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

from nexus.ui_helpers import (
    console, format_bytes,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.effects import celebrate_freed_space


def _get_path_size(path: str) -> int:
    """Return the on-disk size of a file or directory without following symlinks."""
    if os.path.islink(path) or os.path.isfile(path):
        return os.lstat(path).st_size

    total_size = 0
    for directory, _, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(directory, filename)
            try:
                if not os.path.islink(file_path):
                    total_size += os.path.getsize(file_path)
            except OSError:
                continue
    return total_size


DELETION_LOG_PATH = os.path.join(
    os.path.expanduser("~"), "Library", "Application Support", "Nexus", "deletion_log.jsonl"
)

# Process-wide dry-run toggle, set once from main.py via --dry-run before any
# module renders. Every deletion in the session funnels through
# execute_deletion_with_live_report, so a single module-level flag here is
# enough to make the whole run a simulation — no per-caller plumbing needed.
DRY_RUN = False


def set_dry_run(enabled: bool) -> None:
    global DRY_RUN
    DRY_RUN = enabled


def _write_deletion_log(operation_title: str, results: List[Dict[str, Any]]) -> None:
    """Append a JSONL audit record for every deletion attempt (success or not).

    This is an audit trail, not an undo mechanism — Nexus deletes for real
    (moving to Trash would defeat the tool's purpose of freeing disk space
    immediately). If something important was removed by mistake, this log
    at least tells the user exactly what/when/from-where, so they can
    reach for Time Machine or another real backup with an accurate path.
    Logging failures never interrupt the deletion flow itself."""
    try:
        os.makedirs(os.path.dirname(DELETION_LOG_PATH), exist_ok=True)
        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        with open(DELETION_LOG_PATH, "a", encoding="utf-8") as f:
            for res in results:
                f.write(json.dumps({
                    "timestamp": timestamp,
                    "operation": operation_title,
                    "name": res["name"],
                    "category": res["category"],
                    "path": res["path"],
                    "size": res["size"],
                    "status": res["status"],
                    "error": res["error"],
                }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _preserve_directory(path: str) -> bool:
    """Keep shared macOS root folders while removing their selected contents."""
    home = os.path.expanduser("~")
    preserved_roots = {
        os.path.join(home, "Library", "Caches"),
        os.path.join(home, "Library", "Logs"),
        os.path.join(home, ".Trash"),
    }
    return os.path.normpath(path) in preserved_roots


def execute_deletion_with_live_report(
    items_to_delete: List[Dict[str, Any]],
    operation_title: str = "Temizlik İşlemi"
) -> Dict[str, Any]:
    """
    Execute deletion with live real-time visual progress and a comprehensive post-deletion report.
    """
    if not items_to_delete:
        return {"total_freed": 0, "results": []}

    total_bytes = sum(it.get('size', 0) for it in items_to_delete)
    results = []
    total_freed = 0
    start_time = time.time()

    dry_run = DRY_RUN
    mode_note = " [bold #f59e0b](SİMÜLASYON — hiçbir şey silinmeyecek)[/]" if dry_run else ""
    console.print(f"\n[bold {C_CYAN}]⚡ {operation_title} Başlatılıyor...[/]{mode_note} [{C_MUTED}]({len(items_to_delete)} öğe, {format_bytes(total_bytes)})[/]\n")

    with Progress(
        SpinnerColumn(spinner_name="dots12", style=f"bold {C_CYAN}"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=25, style="#1e293b", complete_style=C_EMERALD, finished_style=C_CYAN),
        TextColumn(f"[{C_AMBER}]{{task.percentage:>3.0f}}%"),
        TextColumn(f"[{C_MUTED}]• {{task.fields[current_info]}}"),
        TimeElapsedColumn(),
        console=console,
        transient=False
    ) as progress:
        task = progress.add_task(
            description="Temizleniyor...",
            total=len(items_to_delete),
            current_info="Başlatılıyor"
        )

        for i, item in enumerate(items_to_delete, 1):
            name = item.get('name', 'Bilinmeyen Öğe')
            cat = item.get('category', 'Genel')
            path = item.get('path', '')
            sz = item.get('size', 0)
            item_type = item.get('type', 'dir')

            rel_path = path.replace(os.path.expanduser("~"), "~")
            progress.update(
                task,
                description=f"[{i}/{len(items_to_delete)}] {name[:24]}",
                current_info=f"[{C_PURPLE}]{rel_path[:32]}[/] [{C_AMBER}]({format_bytes(sz)})[/]"
            )

            # Small visual pause for smooth rendering
            time.sleep(0.08)

            success = False
            error_msg = ""
            freed_for_item = 0

            try:
                if not path:
                    error_msg = "Geçerli bir dosya veya dizin yolu belirtilmedi."
                elif os.path.lexists(path):
                    size_before = _get_path_size(path)
                    if dry_run:
                        # Simulate only: report the size that would be freed
                        # without touching the filesystem at all.
                        success = True
                        freed_for_item = size_before
                    elif item_type == "file" or os.path.isfile(path) or os.path.islink(path):
                        os.remove(path)
                        success = True
                        freed_for_item = size_before
                    elif os.path.isdir(path):
                        # Keep only the explicitly selected shared macOS roots.
                        if _preserve_directory(path):
                            child_errors = []
                            for child in os.listdir(path):
                                cp = os.path.join(path, child)
                                try:
                                    if os.path.isfile(cp) or os.path.islink(cp):
                                        os.remove(cp)
                                    elif os.path.isdir(cp):
                                        shutil.rmtree(cp)
                                except OSError as exc:
                                    child_errors.append(f"{child}: {exc}")
                            size_after = _get_path_size(path)
                            freed_for_item = max(size_before - size_after, 0)
                            success = not child_errors
                            if child_errors:
                                error_msg = "; ".join(child_errors[:3])
                        else:
                            shutil.rmtree(path)
                            success = True
                            freed_for_item = size_before
                else:
                    error_msg = "Öğe artık bulunamadı; silme işlemi uygulanmadı."
            except OSError as e:
                success = False
                error_msg = str(e)

            if success:
                total_freed += freed_for_item
                results.append({
                    "name": name,
                    "category": cat,
                    "path": rel_path,
                    "size": freed_for_item,
                    "status": "Simülasyon" if dry_run else "Başarılı",
                    "error": ""
                })
            else:
                status = "Kısmen tamamlandı" if freed_for_item else "Başarısız"
                total_freed += freed_for_item
                results.append({
                    "name": name,
                    "category": cat,
                    "path": rel_path,
                    "size": freed_for_item,
                    "status": status,
                    "error": error_msg
                })

            progress.advance(task, 1)

    elapsed = time.time() - start_time
    if not dry_run:
        # A dry-run never touched the disk, so logging it as a real
        # deletion would pollute the audit trail this log exists for.
        _write_deletion_log(operation_title, results)

    # -------------------------------------------------------------
    # Post-Deletion Detailed Summary Report
    # -------------------------------------------------------------
    report_title = "📋 SİMÜLASYON RAPORU (HİÇBİR ŞEY SİLİNMEDİ)" if dry_run else "📋 SİLİNEN ÖĞELER VE DETAYLI TEMİZLİK RAPORU"
    console.print(f"\n[bold {C_CYAN}]{report_title}[/]\n")

    report_table = Table(
        box=box.ROUNDED,
        border_style=C_INDIGO,
        header_style=f"bold {C_CYAN}",
        expand=True,
        show_header=True
    )
    report_table.add_column("#", style=C_MUTED, width=4, no_wrap=True)
    report_table.add_column("Kategori", style=f"bold {C_PURPLE}", width=16, no_wrap=True)
    report_table.add_column("Silinen Öğe", style="bold white", width=25, no_wrap=True)
    report_table.add_column("Dizin / Dosya Konumu", style=C_MUTED, no_wrap=True, overflow="ellipsis")
    report_table.add_column("Kazanılan Alan", style=f"bold {C_AMBER}", justify="right", width=14, no_wrap=True)
    report_table.add_column("Durum", justify="center", width=12, no_wrap=True)

    for i, res in enumerate(results, 1):
        if res['status'] == "Simülasyon":
            status_style = f"[#f59e0b]◌ Simülasyon[/#f59e0b]"
        elif res['status'] == "Başarılı":
            status_style = f"[{C_EMERALD}]✔ Başarılı[/{C_EMERALD}]"
        elif res['status'] == "Kısmen tamamlandı":
            status_style = f"[{C_AMBER}]▲ Kısmi[/{C_AMBER}]"
        else:
            status_style = f"[{C_RED}]✖ Hata[/{C_RED}]"
        report_table.add_row(
            str(i),
            res['category'],
            res['name'],
            res['path'],
            format_bytes(res['size']),
            status_style
        )

    console.print(report_table)

    # Summary Panel
    t_summary = Text()
    t_summary.append(f"  Toplam {'Simüle Edilen' if dry_run else 'Silinen'} Öğe: ", style=C_MUTED)
    t_summary.append(f"{len(results)} Adet  •  ", style="bold white")
    t_summary.append("İşlem Süresi: ", style=C_MUTED)
    t_summary.append(f"{elapsed:.2f} saniye  •  ", style="bold white")
    t_summary.append(f"{'Tahmini Kazanılacak' if dry_run else 'Geri Kazanılan'} Alan: ", style=C_MUTED)
    t_summary.append(f"+ {format_bytes(total_freed)}\n", style="bold #10b981")

    p_summary = Panel(
        t_summary,
        box=box.ROUNDED,
        border_style="#f59e0b" if dry_run else C_EMERALD,
        style=f"on {C_DARK}",
        padding=(0, 2)
    )
    console.print(p_summary)
    if dry_run:
        console.print(f"[#f59e0b]Bu bir simülasyondu — hiçbir dosya silinmedi. Gerçek temizlik için --dry-run olmadan çalıştırın.[/]\n")
    else:
        console.print(f"[{C_MUTED}]Denetim günlüğü: ~/Library/Application Support/Nexus/deletion_log.jsonl[/]\n")

    # Audio chime and celebration card (skip in dry-run — nothing to celebrate yet)
    if not dry_run:
        celebrate_freed_space(total_freed)

    return {
        "total_freed": total_freed,
        "results": results,
        "elapsed": elapsed
    }
