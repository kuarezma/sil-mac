import os
import tempfile
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from nexus.ai_radar import AIRadar

class AIRadarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.radar = AIRadar()
        self.radar.home = str(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_scans_huggingface_hub_models(self):
        hf_dir = self.home / ".cache" / "huggingface" / "hub" / "models--meta-llama--Llama-3-8B"
        hf_dir.mkdir(parents=True)
        (hf_dir / "model.safetensors").write_bytes(b"x" * 1024)

        items = self.radar.scan()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category"], "Hugging Face")
        self.assertEqual(items[0]["name"], "meta-llama/Llama-3-8B")
        self.assertEqual(items[0]["size"], 1024)

    def test_scans_ollama_models_and_dangling_blobs(self):
        ollama_models = self.home / ".ollama" / "models"
        manifests = ollama_models / "manifests" / "registry.ollama.ai" / "library" / "llama3"
        manifests.mkdir(parents=True)
        blobs = ollama_models / "blobs"
        blobs.mkdir(parents=True)

        # Valid referenced blob
        (blobs / "sha256-valid123").write_bytes(b"v" * 2048)
        # Dangling orphan blob
        (blobs / "sha256-orphan999").write_bytes(b"o" * 4096)

        manifest_data = {
            "config": {"digest": "sha256:valid123"},
            "layers": [{"digest": "sha256:valid123"}]
        }
        (manifests / "latest").write_text(json.dumps(manifest_data))

        items = self.radar.scan()
        names = {it["name"]: it for it in items}
        self.assertIn("llama3/latest", names)
        self.assertEqual(names["llama3/latest"]["category"], "Ollama")
        self.assertEqual(names["llama3/latest"]["size"], 2048)

        # Check dangling blob found
        orphan_items = [it for it in items if "Yetim" in it["category"]]
        self.assertEqual(len(orphan_items), 1)
        self.assertEqual(orphan_items[0]["size"], 4096)

    def test_scans_loose_models(self):
        downloads = self.home / "Downloads"
        downloads.mkdir(parents=True)
        model_file = downloads / "qwen2.5-7b-instruct.Q4_K_M.gguf"
        # 60MB file
        with open(model_file, "wb") as f:
            f.truncate(60 * 1024 * 1024)

        with patch("nexus.config.get") as mock_get:
            def config_side_effect(key, default=None):
                if key == "ai_radar.loose_model_threshold_mb":
                    return 50
                if key == "ai_radar.loose_model_scan_dirs":
                    return [str(downloads)]
                if key == "ai_radar.cache_threshold_mb":
                    return 1
                return default
            mock_get.side_effect = config_side_effect

            items = self.radar.scan()
            loose = [it for it in items if it["category"] == "Serbest GGUF/Safetensors"]
            self.assertEqual(len(loose), 1)
            self.assertEqual(loose[0]["name"], "qwen2.5-7b-instruct.Q4_K_M.gguf")

if __name__ == "__main__":
    unittest.main()
