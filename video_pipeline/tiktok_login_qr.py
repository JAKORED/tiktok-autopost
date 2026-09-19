"""Connexion TikTok par QR code (à faire une fois) pour la publication via navigateur.

Ouvre Chrome VISIBLE sur la page de connexion QR de TikTok. Tu scannes le QR avec l'appli
TikTok (Profil > menu > Mon code QR / Scanner). Dès que la session est détectée (cookie
`sessionid`), les cookies sont enregistrés dans config/tiktok_cookies.json — exactement le
fichier attendu par TikTokPublisherAgent._publish_via_selenium.

Aucun mot de passe n'est saisi ni stocké par ce script.
Usage : python video_pipeline/tiktok_login_qr.py
"""
import json
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parent.parent
COOKIES = ROOT / "config" / "tiktok_cookies.json"
PROFILE = ROOT / "config" / "chrome_tiktok_profile"
TIMEOUT = 300


def main():
    COOKIES.parent.mkdir(exist_ok=True)
    opts = Options()
    opts.add_argument(f"--user-data-dir={PROFILE}")
    opts.add_argument("--window-size=1100,900")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get("https://www.tiktok.com/login/qrcode")
        print("Chrome ouvert : scanne le QR code avec l'appli TikTok. Attente jusqu'à 5 min...",
              flush=True)
        start = time.time()
        while time.time() - start < TIMEOUT:
            names = {c["name"] for c in driver.get_cookies()}
            if "sessionid" in names:
                time.sleep(3)  # laisse finir la mise en place de la session
                COOKIES.write_text(json.dumps(driver.get_cookies(), indent=2), encoding="utf-8")
                print(f"CONNECTÉ : {len(driver.get_cookies())} cookies -> {COOKIES}", flush=True)
                return 0
            time.sleep(2)
        print("TIMEOUT : QR non scanné", flush=True)
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
