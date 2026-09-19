"""Sonde : un GPU Modal est-il utilisable sans moyen de paiement ? (GPU choisi via PROBE_GPU)"""
import os

import modal

GPU = os.environ.get("PROBE_GPU", "T4")
app = modal.App("factvibes-probe")


@app.function(image=modal.Image.debian_slim(python_version="3.11"), gpu=GPU, timeout=120)
def probe():
    import subprocess
    return subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                          capture_output=True, text=True).stdout.strip()


@app.local_entrypoint()
def main():
    print("RESULTAT", GPU, "->", probe.remote())
