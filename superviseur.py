#!/usr/bin/env python3
"""FactVibes — Superviseur de l'orchestrateur (lance au démarrage de Windows).

Pourquoi
--------
Le 09/10/2026 le compte TikTok est resté muet 6 jours. La cause n'était pas le code :
rien ne démarrait la boucle de publication. Deux options de démarrage :

* **Tâche Windows** (`scripts/installer_taches.ps1`) — exige les droits administrateur,
  et l leanedossier n'était pas utilisé du tout. À installer une fois en admin si on
  veut le watchdog système.
* **Dossier Démarrage** (`scripts/installer_demarrage.ps1`) — aucune élévation
  nécessaire, donc installable immédiatement. C'est ce que fait ce superviseur.

Ce superviseur reste vivant tant que la session Windows est ouverte et relance
`auto_poster.py` s'il tombe. Comme Chrome a besoin d'un bureau pour afficher TikTok
Studio, une session utilisateur ouverte est de toute façon nécessaire.

Usage : python superviseur.py      (lancé par le dossier Démarrage)
       python superviseur.py --once    (un seul contrôle)
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
HEARTBEAT = LOG_DIR / "auto_poster_heartbeat.json"
STOP_FILE = ROOT / "videos" / ".stop_superviseur"

# Au-delà de ce silence du cœur de l'orchestrateur, on le considère mort.
SILENCE_MAX_SEC = 20 * 60


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    try:
        print(line.encode("cp1252", "replace").decode("cp1252"), flush=True)
    except Exception:
        pass          # un journal ne doit jamais tuer le superviseur
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with open(LOG_DIR / f"superviseur_{datetime.now():%Y%m%d}.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _pid_vivant(pid):
    """Le processus existe-t-il encore ?

    On n'utilise surtout PAS `os.kill(pid, 0)` : sous Windows, CPython traduit tout
    signal autre que CTRL_C/CTRL_BREAK par `TerminateProcess` — on tuerait l'orchestrateur
    qu'on veut justement vérifier. On interroge l'API Win32 sans effet de bord.
    """
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return True
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
    if not h:
        return False
    code = wintypes.DWORD()
    ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return bool(ok) and code.value == STILL_ACTIVE


def coeur_frais():
    """L'orchestrateur bat-il encore ?

    Un fichier de cœur RÉCENT ne suffit pas : le 09/10/2026 un passage ponctuel
    (`--once`) avait laissé un cœur daté de 1 minute, et le superviseur en a conclu que
    l'orchestrateur tournait encore alors qu'il était mort depuis le test. On exige
    donc les DEUX : un battement récent ET un PID vivant.
    """
    try:
        brut = HEARTBEAT.read_text(encoding="utf-8")
        dernier = datetime.fromisoformat(
            brut.split('"last_beat":')[1].split(",")[0].strip().strip('"'))
        pid = int(brut.split('"pid":')[1].split(",")[0].strip())
    except Exception:
        return False
    if (datetime.now() - dernier).total_seconds() >= SILENCE_MAX_SEC:
        return False
    return _pid_vivant(pid)


def demarrer_orchestrateur():
    """Lance auto_poster.py en arrière-plan, sans fenêtre.

    `PYTHONIOENCODING=utf-8` est forcé dans l'environnement de l'enfant : sans cela la
    console cp1252 fait planter l'orchestrateur sur le premier caractère accentué ou
    typographique (vu le 09/10/2026 : boucle de crash toutes les 60 s, aucun post parti).
    """
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    return subprocess.Popen(
        [sys.executable, str(ROOT / "auto_poster.py")], cwd=str(ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creationflags)


def main():
    if "--once" in sys.argv:
        print("coeur frais :", coeur_frais())
        return

    log("=== Superviseur FactVibes démarré ===")
    proc = None
    while not STOP_FILE.exists():
        if proc is not None and proc.poll() is not None:
            log(f"orchestrateur arrêté (code {proc.returncode}) -> relance", "WARN")
            proc = None

        if proc is None:
            if coeur_frais():
                log("un orchestrateur bat déjà (cœur frais) -> on ne lance rien")
                time.sleep(120)
                continue
            log("orchestrateur absent ou muet -> démarrage")
            try:
                proc = demarrer_orchestrateur()
                log(f"pid {proc.pid}")
            except Exception as exc:
                log(f"démarrage impossible : {exc}", "ERROR")
                time.sleep(120)
                continue

        time.sleep(60)

    STOP_FILE.unlink(missing_ok=True)
    if proc is not None:
        try:
            proc.terminate()
        except Exception:
            pass
    log("superviseur arrêté (fichier d'arrêt présent)")


if __name__ == "__main__":
    main()