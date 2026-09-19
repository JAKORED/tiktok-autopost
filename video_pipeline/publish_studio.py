"""Publication via TikTok Studio (navigateur déjà connecté par QR — voir tiktok_login_qr.py).

Pilote le Chrome visible ouvert avec le profil config/chrome_tiktok_profile (port 9222 ; lancé
automatiquement s'il n'est pas ouvert). Envoie le mp4, saisit la légende des métadonnées, clique
« Publier », puis lit la liste « Contenu » de TikTok Studio : l'état de la file n'est mis à
PUBLISHED que si la vidéo y apparaît réellement avec le début de sa légende.

Usage : python video_pipeline/publish_studio.py <video_id> --confirm
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
PROFILE = ROOT / "config" / "chrome_tiktok_profile"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload"
CONTENT_URL = "https://www.tiktok.com/tiktokstudio/content"


def ensure_chrome():
    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=3)
    except Exception:
        subprocess.Popen([CHROME, "--remote-debugging-port=9222", f"--user-data-dir={PROFILE}",
                          "--window-size=1200,950", UPLOAD_URL])
        time.sleep(8)
    o = Options()
    o.debugger_address = "127.0.0.1:9222"
    return webdriver.Chrome(options=o)


def click_button(d, text):
    for b in d.find_elements(By.CSS_SELECTOR, "button"):
        if b.text.strip() == text and b.is_displayed():
            d.execute_script("arguments[0].click()", b)
            time.sleep(1)
            return True
    return False


def ensure_caption(d, caption, tries=4):
    probe = caption[:25].strip()
    for _ in range(tries):
        ed = d.find_element(By.CSS_SELECTOR, ".public-DraftEditor-content")
        if probe in ed.text:
            return True
        ed.click()
        time.sleep(0.5)
        ed.send_keys(Keys.CONTROL, "a")
        ed.send_keys(Keys.DELETE)
        time.sleep(0.5)
        ed.send_keys(caption + " ")
        time.sleep(3)
        ed.send_keys(Keys.ESCAPE)
        time.sleep(2)
    return probe in d.find_element(By.CSS_SELECTOR, ".public-DraftEditor-content").text


def set_state(video_id, state, **fields):
    qf = VIDEOS / "queue.json"
    q = json.loads(qf.read_text(encoding="utf-8")) if qf.exists() else []
    e = next((x for x in q if x["video_id"] == video_id), None)
    if e is None:
        e = {"video_id": video_id, "file": f"ready/{video_id}.mp4"}
        q.append(e)
    e.update(state=state, **fields)
    qf.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def publish(video_id):
    meta = json.loads((VIDEOS / "metadata" / f"{video_id}.json").read_text(encoding="utf-8"))
    mp4 = VIDEOS / "ready" / f"{video_id}.mp4"
    caption = meta["caption"]
    d = ensure_chrome()
    d.get(UPLOAD_URL)
    time.sleep(5)
    d.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(str(mp4.resolve()))

    for _ in range(60):  # attend la fin de l'import (max ~5 min)
        time.sleep(5)
        body = d.find_element(By.TAG_NAME, "body").text
        if "Importé" in body or "Uploaded" in body:
            break
    else:
        set_state(video_id, "FAILED", error="import TikTok Studio non terminé")
        sys.exit("import non terminé")

    for _ in range(3):  # ferme les fenêtres d'info éventuelles (la plus haute d'abord)
        if not (click_button(d, "Annuler") or click_button(d, "J'ai compris")):
            break

    # TikTok réécrit la description (nom du fichier) tant que la couverture charge :
    # on attend la fin du chargement, puis on saisit et on revérifie (jusqu'à 4 essais).
    for _ in range(24):
        if "Chargement" not in d.find_element(By.TAG_NAME, "body").text:
            break
        time.sleep(2.5)
    if not ensure_caption(d, caption):
        set_state(video_id, "FAILED", error="légende non saisie (écrasée par TikTok)")
        sys.exit("légende non saisie")

    if not ensure_caption(d, caption, tries=2):  # dernière vérification avant l'envoi
        set_state(video_id, "FAILED", error="légende perdue juste avant Publier")
        sys.exit("légende perdue avant Publier")
    btn = d.find_element(By.CSS_SELECTOR, '[data-e2e="post_video_button"]')
    d.execute_script("arguments[0].scrollIntoView({block:'center'})", btn)
    time.sleep(1)
    btn.click()
    time.sleep(4)
    # Confirmation éventuelle après « Publier » (ex. vérification de contenu / droits d'auteur)
    for label in ("Publier maintenant", "Publier quand même", "Continuer", "Publier"):
        if "tiktokstudio/content" in d.current_url:
            break
        if click_button(d, label):
            print(f"fenêtre de confirmation validée : {label}")
            time.sleep(3)

    # Preuve réelle : la vidéo doit figurer dans la liste Contenu de TikTok Studio
    time.sleep(6)
    if "tiktokstudio/content" not in d.current_url:
        d.get(CONTENT_URL)
        time.sleep(5)
    body = d.find_element(By.TAG_NAME, "body").text
    if caption[:25] in body:
        set_state(video_id, "PUBLISHED", error=None,
                  published_at_utc=datetime.now(timezone.utc).isoformat(),
                  published_evidence={"method": "tiktok studio (navigateur, connexion QR)",
                                      "confirmation": "vidéo présente dans Contenu de TikTok Studio",
                                      "en_examen": "examen" in body.lower()})
        (VIDEOS / "published").mkdir(exist_ok=True)
        shutil.copy2(mp4, VIDEOS / "published" / mp4.name)
        print(f"{video_id} PUBLISHED (présente dans Contenu ; en examen={'examen' in body.lower()})")
    else:
        shot = VIDEOS / "failed" / f"{video_id}_studio.png"
        shot.parent.mkdir(exist_ok=True)
        d.save_screenshot(str(shot))
        set_state(video_id, "FAILED", error=f"vidéo absente de Contenu après clic sur Publier (capture : {shot.name})")
        sys.exit(f"aucune preuve de publication — voir {shot}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] != "--confirm":
        sys.exit(__doc__)
    publish(sys.argv[1])
