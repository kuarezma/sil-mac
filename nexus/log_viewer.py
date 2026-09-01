import os
import json
from typing import List, Dict, Any
from rich.panel import Panel
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, render_scan_table,
    C_CYAN, C_PURPLE, C_AMBER, C_EMERALD, C_RED, C_MUTED
)
from nexus.deletion_engine import DELETION_LOG_PATH

_STATUS_STYLE = {
    "Başarılı": f"[{C_EMERALD}]✔ Başarılı[/{C_EMERALD}]",
    "Kısmen tamamlandı": f"[{C_AMBER}]▲ Kısmi[/{C_AMBER}]",
    "Simülasyon": "[#f59e0b]◌ Simülasyon[/#f59e0b]",
}


def _read_log_entries() -> List[Dict[str, Any]]:
    if not os.path.exists(DELETION_LOG_PATH):
        return []
    entries = []
    try:
        with open(DELETION_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return entries


def render_deletion_log(limit: int = 30):
    """Show the most recent entries from the JSONL deletion audit log
    (nexus.deletion_engine.DELETION_LOG_PATH) — the record of what Nexus
    actually deleted (or tried to), so a mistaken deletion can be traced
    by exact original path/time for manual recovery (e.g. Time Machine)."""
    console.print(create_header(
        "SİLME DENETİM GÜNLÜĞÜ",
        f"Son {limit} işlem — zaman, konum, boyut ve durum",
        "🗒️",
        tier="safe"
    ))

    entries = _read_log_entries()
    if not entries:
        console.print(Panel(
            f"[{C_EMERALD}]✓ Henüz kayıtlı bir silme işlemi yok.[/]",
            border_style=C_EMERALD,
            box=box.ROUNDED
        ))
        return

    total_entries = len(entries)
    recent = list(reversed(entries))[:limit]

    for e in recent:
        e["status_display"] = _STATUS_STYLE.get(e.get("status", ""), f"[{C_RED}]✖ Hata[/{C_RED}]")

    table = render_scan_table(recent, [
        {"header": "Zaman", "key": "timestamp", "style": C_MUTED, "width": 19},
        {"header": "İşlem", "key": "operation", "style": f"bold {C_PURPLE}", "width": 22},
        {"header": "Öğe", "key": "name", "style": "bold white", "width": 22},
        {"header": "Konum", "key": "path", "style": C_MUTED, "overflow": "ellipsis"},
        {"header": "Boyut", "key": "size", "style": f"bold {C_AMBER}", "justify": "right", "width": 12, "format": "bytes"},
        {"header": "Durum", "key": "status_display", "justify": "center", "width": 14},
    ])
    console.print(table)

    total_deleted = sum(e.get("size", 0) for e in entries if e.get("status") == "Başarılı")
    console.print(
        f"\n[{C_MUTED}]Günlükteki toplam kayıt: {total_entries}  •  "
        f"Kalıcı olarak geri kazanılan toplam alan: [/][bold {C_EMERALD}]{format_bytes(total_deleted)}[/]"
    )
    console.print(f"[{C_MUTED}]Dosya: ~/Library/Application Support/Nexus/deletion_log.jsonl[/]\n")
