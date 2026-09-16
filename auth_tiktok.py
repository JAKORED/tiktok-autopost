#!/usr/bin/env python3
"""
Autorisation OAuth TikTok.
Guides l'utilisateur pour :
1. Autoriser son compte au système
2. Récupérer le code d'autorisation
3. Échanger le code contre les tokens (access + refresh)
4. Sauvegarder les tokens dans .env
"""

import os
import sys
import json
import time
import base64
import hashlib
import secrets
import webbrowser
import urllib.parse
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

# TikTok exige un Redirect URI en https:// pour l'app en Production (le
# http://localhost:8080/callback d'origine ne fonctionne qu'en Sandbox).
# On utilise donc une page statique GitHub Pages qui affiche le code recu
# pour un copier-coller manuel dans ce script (cf. docs/callback.html).
REDIRECT_URI = os.getenv(
    "TIKTOK_REDIRECT_URI", "https://jakored.github.io/tiktok-autopost/callback.html"
)
CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")

AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.upload,video.publish"

# TikTok exige désormais le flux OAuth PKCE (RFC 7636).
CODE_VERIFIER = secrets.token_urlsafe(64)
CODE_CHALLENGE = (
    base64.urlsafe_b64encode(hashlib.sha256(CODE_VERIFIER.encode()).digest())
    .rstrip(b"=")
    .decode()
)


def get_auth_url() -> str:
    params = {
        "client_key": CLIENT_KEY,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": "autopost_state_123",
        "code_challenge": CODE_CHALLENGE,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(auth_code: str):
    import requests

    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")

    try:
        resp = requests.post(
            TOKEN_URL,
            data={
                "client_key": CLIENT_KEY,
                "client_secret": client_secret,
                "code": auth_code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code_verifier": CODE_VERIFIER,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        print(f"Response status: {resp.status_code}")
        print(f"Response body: {resp.text[:500]}")
        resp.raise_for_status()

        data = resp.json().get("data", {})
        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token", "")
        expires_in = data.get("expires_in", 0)

        if not access_token:
            print("ERROR: No access token in response. TikTok might require")
            print("is_visible_display for the app. Check developers.tiktok.com.")
            return False

        _save_tokens_to_env(access_token, refresh_token)
        print(f"\n✅ Tokens sauvegardés!")
        print(f"   Access token expire dans {expires_in}s")
        columns = os.get_terminal_size().columns if os.name != "nt" else 80
        return True

    except Exception as e:
        print(f"\n❌ Erreur échange du code: {e}")
        return False


def _save_tokens_to_env(access_token: str, refresh_token: str):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "r") as f:
        content = f.read()

    content = content.replace(
        "TIKTOK_ACCESS_TOKEN=", f"TIKTOK_ACCESS_TOKEN={access_token}"
    )
    content = content.replace(
        "TIKTOK_REFRESH_TOKEN=", f"TIKTOK_REFRESH_TOKEN={refresh_token}"
    )

    with open(env_path, "w") as f:
        f.write(content)
    print(f"   Fichier .env mis à jour: {env_path}")


def main():
    print("=" * 60)
    print("  Autorisation TikTok")
    print("=" * 60)

    if not CLIENT_KEY:
        print("ERREUR: TIKTOK_CLIENT_KEY non configuré dans .env")
        print("Modifie ton fichier .env et réessaie.")
        return

    print(f"\n   Client Key configurée: {CLIENT_KEY[:8]}...")
    print(f"   Redirect URI: {REDIRECT_URI}")
    print(f"   Scopes demandés: {SCOPES}")
    print(f"   PKCE: code_challenge_method=S256 (obligatoire TikTok)")
    print()

    print("ÉTAPE 1: Le navigateur va s'ouvrir...")
    print("  → Connecte-toi avec ton compte TikTok")
    print("  → Clique sur 'Autoriser' pour donner accès au système")
    print()

    auth_url = get_auth_url()
    print(f"  Si le navigateur ne s'ouvre pas, copie ce lien:\n  {auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    print("  Une fois autorisé, TikTok te redirige vers une page FactVibes")
    print("  qui affiche un code — copie-le et colle-le ci-dessous.\n")

    try:
        auth_code = input("  Code d'autorisation : ").strip()
    except KeyboardInterrupt:
        print("\n  Annulé.")
        return

    if not auth_code:
        print("\n❌ Pas de code fourni. Tu as peut-être refusé l'accès.")
        return

    print(f"\nÉTAPE 2: Code reçu! Échange contre les tokens...")

    if exchange_code_for_tokens(auth_code):
        print("=" * 60)
        print("  Autorisation terminée!")
        print("=" * 60)
        print("\nTeste maintenant:")
        print("  python main.py run")


if __name__ == "__main__":
    main()