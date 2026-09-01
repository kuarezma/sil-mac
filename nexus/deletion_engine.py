import os
import sys
import time
import shutil
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

    console.print(f"\n[bold {C_CYAN}]⚡ {operation_title} Başlatılıyor...[/] [{C_MUTED}]({len(items_to_delete)} öğe, {format_bytes(total_bytes)})[/]\n")

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
                if os.path.exists(path):
                    if item_type == "file" or os.path.isfile(path) or os.path.islink(path):
                        os.remove(path)
                        success = True
                        freed_for_item = sz
                    elif os.path.isdir(path):
                        # If system/cache root directory, clean contents to preserve folder
                        if any(sys_root in path for sys_root in ["Library/Caches", "Library/Logs", ".Trash"]):
                            for child in os.listdir(path):
                                cp = os.path.join(path, child)
                                try:
                                    if os.path.isfile(cp) or os.path.islink(cp):
                                        os.remove(cp)
                                    elif os.path.isdir(cp):
                                        shutil.rmtree(cp)
                                except Exception:
                                    pass
                            success = True
                            freed_for_item = sz
                        else:
                            shutil.rmtree(path)
                            success = True
                            freed_for_item = sz
                else:
                    success = True
                    freed_for_item = sz
            except Exception as e:
                success = False
                error_msg = str(e)

            if success:
                total_freed += freed_for_item
                results.append({
                    "name": name,
                    "category": cat,
                    "path": rel_path,
                    "size": sz,
                    "status": "Başarılı",
                    "error": ""
                })
            else:
                results.append({
                    "name": name,
                    "category": cat,
                    "path": rel_path,
                    "size": sz,
                    "status": "Başarısız",
                    "error": error_msg
                })

            progress.advance(task, 1)

    elapsed = time.time() - start_time

    # -------------------------------------------------------------
    # Post-Deletion Detailed Summary Report
    # -------------------------------------------------------------
    console.print(f"\n[bold {C_CYAN}]📋 SİLİNEN ÖĞELER VE DETAYLI TEMİZLİK RAPORU[/]\n")

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
        status_style = f"[{C_EMERALD}]✔ Başarılı[/{C_EMERALD}]" if res['status'] == "Başarılı" else f"[{C_RED}]✖ Hata[/{C_RED}]"
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
    t_summary.append("  Toplam Silinen Öğe: ", style=C_MUTED)
    t_summary.append(f"{len(results)} Adet  •  ", style="bold white")
    t_summary.append("İşlem Süresi: ", style=C_MUTED)
    t_summary.append(f"{elapsed:.2f} saniye  •  ", style="bold white")
    t_summary.append("Geri Kazanılan Alan: ", style=C_MUTED)
    t_summary.append(f"+ {format_bytes(total_freed)}\n", style="bold #10b981")

    p_summary = Panel(
        t_summary,
        box=box.ROUNDED,
        border_style=C_EMERALD,
        style=f"on {C_DARK}",
        padding=(0, 2)
    )
    console.print(p_summary)

    # Audio chime and celebration card
    celebrate_freed_space(total_freed)

    return {
        "total_freed": total_freed,
        "results": results,
        "elapsed": elapsed
    }
