import os
import json
import shutil
import glob
from typing import List, Dict, Any
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from nexus.ui_helpers import (
    console, format_bytes, create_header, create_spinner,
    C_CYAN, C_BLUE, C_PURPLE, C_GREEN, C_EMERALD,
    C_AMBER, C_RED, C_MUTED, C_INDIGO, C_DARK
)
from nexus.menu_helpers import checkbox_menu, confirm_menu
from nexus.deletion_engine import execute_deletion_with_live_report
from InquirerPy.base.control import Choice

class AIRadar:
    def __init__(self):
        self.home = os.path.expanduser("~")
        self.found_items: List[Dict[str, Any]] = []

    def scan(self) -> List[Dict[str, Any]]:
        """Deep scan for all AI models, weights, and caches."""
        self.found_items = []

        with create_spinner("Yapay zeka modelleri ve ağırlık önbellekleri taranıyor...") as progress:
            task = progress.add_task("scan", total=None)

            # 1. Hugging Face Hub
            hf_hub = os.path.join(self.home, ".cache/huggingface/hub")
            if os.path.exists(hf_hub):
                for item in os.listdir(hf_hub):
                    item_path = os.path.join(hf_hub, item)
                    if item.startswith("models--") and os.path.isdir(item_path):
                        clean_name = item.replace("models--", "").replace("--", "/")
                        size = self._get_dir_size(item_path)
                        self.found_items.append({
                            "type": "Hugging Face (Hub)",
                            "name": clean_name,
                            "path": item_path,
                            "size": size,
                            "category": "Hugging Face"
                        })
                    elif item in ["dealignai", "GGorman", ".locks"] and os.path.isdir(item_path):
                        size = self._get_dir_size(item_path)
                        self.found_items.append({
                            "type": "Hugging Face (Meta)",
                            "name": item,
                            "path": item_path,
                            "size": size,
                            "category": "Hugging Face"
                        })

            # 2. Ollama Models & Blobs
            ollama_dir = os.path.join(self.home, ".ollama/models")
            if os.path.exists(ollama_dir):
                # Manifests
                manifest_dir = os.path.join(ollama_dir, "manifests")
                referenced_digests = set()
                if os.path.exists(manifest_dir):
                    for root, _, files in os.walk(manifest_dir):
                        for file in files:
                            fpath = os.path.join(root, file)
                            try:
                                with open(fpath, 'r') as f:
                                    data = json.load(f)
                                    rel = os.path.relpath(fpath, manifest_dir).replace("registry.ollama.ai/library/", "").replace("registry.ollama.ai/", "")
                                    model_size = 0
                                    if 'config' in data and 'digest' in data['config']:
                                        referenced_digests.add(data['config']['digest'].replace(":", "-"))
                                    if 'layers' in data:
                                        for l in data['layers']:
                                            if 'digest' in l:
                                                d_clean = l['digest'].replace(":", "-")
                                                referenced_digests.add(d_clean)
                                                blob_path = os.path.join(ollama_dir, "blobs", d_clean)
                                                if os.path.exists(blob_path):
                                                    model_size += os.path.getsize(blob_path)
                                    self.found_items.append({
                                        "type": "Ollama Model",
                                        "name": rel,
                                        "path": fpath,
                                        "size": model_size,
                                        "category": "Ollama"
                                    })
                            except Exception:
                                pass

                # Check for dangling blobs
                blob_dir = os.path.join(ollama_dir, "blobs")
                if os.path.exists(blob_dir):
                    for b in os.listdir(blob_dir):
                        if b not in referenced_digests:
                            bpath = os.path.join(blob_dir, b)
                            size = os.path.getsize(bpath)
                            self.found_items.append({
                                "type": "Ollama Orphan Blob",
                                "name": f"Dangling Blob ({b[:16]}...)",
                                "path": bpath,
                                "size": size,
                                "category": "Ollama (Yetim)"
                            })

                # Check for temporary safetensors
                for d in glob.glob(os.path.join(ollama_dir, "ollama-safetensors*")):
                    size = self._get_dir_size(d)
                    self.found_items.append({
                        "type": "Ollama Temp",
                        "name": os.path.basename(d),
                        "path": d,
                        "size": size,
                        "category": "Ollama (Geçici)"
                    })

            # 3. MLX & vMLX Cache
            for mlx_path, label in [
                (os.path.join(self.home, ".cache/mlx"), "MLX Cache"),
                (os.path.join(self.home, ".cache/vmlx-engine"), "vMLX Engine Cache")
            ]:
                if os.path.exists(mlx_path):
                    sz = self._get_dir_size(mlx_path)
                    if sz > 1024 * 1024: # > 1MB
                        self.found_items.append({
                            "type": label,
                            "name": os.path.basename(mlx_path),
                            "path": mlx_path,
                            "size": sz,
                            "category": "MLX"
                        })

            # 4. PyTorch & Whisper Cache
            for torch_path, label, cat in [
                (os.path.join(self.home, ".cache/torch"), "PyTorch Cache", "PyTorch"),
                (os.path.join(self.home, ".cache/whisper"), "Whisper Cache", "Whisper")
            ]:
                if os.path.exists(torch_path):
                    sz = self._get_dir_size(torch_path)
                    if sz > 1024 * 1024:
                        self.found_items.append({
                            "type": label,
                            "name": os.path.basename(torch_path),
                            "path": torch_path,
                            "size": sz,
                            "category": cat
                        })

            # 5. LM Studio & Jan
            for app_models, label, cat in [
                (os.path.join(self.home, ".cache/lm-studio/models"), "LM Studio Models", "LM Studio"),
                (os.path.join(self.home, ".lmstudio/models"), "LM Studio Models", "LM Studio"),
                (os.path.join(self.home, "jan/models"), "Jan.ai Models", "Jan.ai"),
                (os.path.join(self.home, "Library/Application Support/Jan/models"), "Jan.ai Models", "Jan.ai")
            ]:
                if os.path.exists(app_models):
                    sz = self._get_dir_size(app_models)
                    if sz > 1024 * 1024:
                        self.found_items.append({
                            "type": label,
                            "name": os.path.basename(app_models),
                            "path": app_models,
                            "size": sz,
                            "category": cat
                        })

        return self.found_items

    def render(self):
        """Render AI Radar table and interactive arrow-key selection."""
        console.print(create_header("AI & YEREL MODEL RADARI", "Hugging Face, Ollama, MLX, Torch, Whisper & GGUF", "🤖"))
        
        items = self.scan()
        if not items:
            console.print(Panel(
                f"[{C_EMERALD}]✓ Sistemde kayıtlı yerel model veya ağırlık önbelleği bulunamadı. Disk tertemiz![/]",
                border_style=C_EMERALD,
                box=box.ROUNDED
            ))
            return

        table = Table(box=box.ROUNDED, border_style=C_INDIGO, header_style=f"bold {C_CYAN}", expand=True)
        table.add_column("#", style=C_MUTED, width=4)
        table.add_column("Tür / Sağlayıcı", style=f"bold {C_BLUE}", width=22)
        table.add_column("Model / Önbellek Adı", style="bold white")
        table.add_column("Boyut", style=f"bold {C_AMBER}", justify="right", width=12)

        total_size = 0
        for i, it in enumerate(items, 1):
            total_size += it['size']
            table.add_row(str(i), it['type'], it['name'], format_bytes(it['size']))

        console.print(table)
        console.print(f"[{C_PURPLE}]Toplam Yerel AI Boyutu:[/] [bold {C_CYAN}]{format_bytes(total_size)}[/]\n")

        choices = [
            Choice(it, f"{it['type']:<22} │  {it['name']:<35} ({format_bytes(it['size'])})")
            for it in items
        ]

        selected_items = checkbox_menu(
            "Silmek istediğiniz AI modellerini/önbelleklerini seçin (Space: İşaretle, Enter: Onayla):",
            choices
        )

        if selected_items:
            sel_sz = sum(x['size'] for x in selected_items)
            if confirm_menu(f"Seçilen {len(selected_items)} modeli/önbelleği ({format_bytes(sel_sz)}) kalıcı olarak silmek istiyor musunuz?", default=False):
                execute_deletion_with_live_report(selected_items, "AI & Yerel Model Temizliği")
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
