"""Génération d'image gratuite sans compte via AI Horde (clé anonyme publique 0000000000).

Usage : python cloud/horde_image.py "<prompt>" <sortie.png> [--model "AlbedoBase XL (SDXL)"] [--w 704 --h 1216] [--seed 5]
Priorité la plus basse pour les anonymes : l'attente dépend de la file (typiquement 30-120 s).
"""
import json
import sys
import time
import urllib.request

API = "https://aihorde.net/api/v2"
HEAD = {"apikey": "0000000000", "Content-Type": "application/json", "User-Agent": "factvibes-toons/1.0 (+https://github.com/JAKORED)",
        "Client-Agent": "factvibes-toons:1.0:anonymous"}
NEG = "text, watermark, logo, signature, people, person, blurry, low quality, deformed, dark, muddy"


def call(path, data=None):
    req = urllib.request.Request(API + path, data=json.dumps(data).encode() if data else None, headers=HEAD)
    return json.load(urllib.request.urlopen(req, timeout=60))


def generate(prompt, out, model="AlbedoBase XL (SDXL)", w=704, h=1216, seed=5, steps=28, timeout=600):
    job = call("/generate/async", {
        "prompt": f"{prompt} ### {NEG}", "models": [model], "nsfw": False, "censor_nsfw": True,
        "r2": True, "shared": False,
        "params": {"width": w, "height": h, "steps": steps, "cfg_scale": 6, "seed": str(seed),
                   "sampler_name": "k_euler_a", "n": 1, "karras": True}})
    jid = job["id"]
    print("job", jid, "envoyé", flush=True)
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = call(f"/generate/check/{jid}")
        if st.get("done"):
            break
        if st.get("faulted"):
            raise RuntimeError("job en échec côté Horde")
        print(f"  attente… file={st.get('queue_position')} restant≈{st.get('wait_time')}s", flush=True)
        time.sleep(8)
    res = call(f"/generate/status/{jid}")
    gen = res["generations"][0]
    img = urllib.request.urlopen(urllib.request.Request(gen["img"], headers={"User-Agent": "factvibes-toons/1.0 (+https://github.com/JAKORED)"}), timeout=120).read()
    open(out, "wb").write(img)
    print(f"OK {out} modèle={gen.get('model')} worker={gen.get('worker_name')} en {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    generate(a[0], a[1], model=opt("--model", "AlbedoBase XL (SDXL)"), w=int(opt("--w", 704)),
             h=int(opt("--h", 1216)), seed=int(opt("--seed", 5)))
