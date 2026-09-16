#!/usr/bin/env python3
"""
Script de configuration initiale.
Guide l'utilisateur pour configurer les APIs et les tokens.
"""

import os
import json
import shutil

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
ENV_EXAMPLE = os.path.join(os.path.dirname(__file__), ".env.example")


def setup():
    print("=" * 60)
    print("  TikTok AutoPost - Configuration Initiale")
    print("=" * 60)

    if os.path.exists(ENV_PATH):
        resp = input("\n.env file already exists. Overwrite? (y/N): ")
        if resp.lower() != "y":
            print("Keeping existing .env")
            return

    print("\n1. PEXELS API (gratuit)")
    print("   → Va sur https://www.pexels.com/api/")
    print("   → Crée un compte gratuit")
    print("   → Copie ta clé API")
    pexels_key = input("   Pexels API Key: ").strip()

    print("\n2. PIXABAY API (gratuit)")
    print("   → Va sur https://pixabay.com/api/docs/")
    print("   → Crée un compte gratuit")
    print("   → Copie ta clé API")
    pixabay_key = input("   Pixabay API Key: ").strip()

    print("\n3. TIKTOK API (optionnel mais recommandé)")
    print("   → Va sur https://developers.tiktok.com/")
    print("   → Crée une app développeur")
    print("   → Active le Content Posting API")
    print("   → Si tu n'as pas encore l'approbation, passe cette étape")
    tiktok_key = input("   TikTok Client Key (ou Entrée pour ignorer): ").strip()
    tiktok_secret = input("   TikTok Client Secret (ou Entrée pour ignorer): ").strip()
    tiktok_access = input("   TikTok Access Token (ou Entrée pour ignorer): ").strip()
    tiktok_refresh = input("   TikTok Refresh Token (ou Entrée pour ignorer): ").strip()

    env_content = f"""# TikTok AutoPost Configuration
# Généré le {__import__('datetime').datetime.now().isoformat()}

# Pexels API (gratuit)
PEXELS_API_KEY={pexels_key}

# Pixabay API (gratuit)
PIXABAY_API_KEY={pixabay_key}

# TikTok API (optionnel)
TIKTOK_CLIENT_KEY={tiktok_key}
TIKTOK_CLIENT_SECRET={tiktok_secret}
TIKTOK_ACCESS_TOKEN={tiktok_access}
TIKTOK_REFRESH_TOKEN={tiktok_refresh}
"""

    with open(ENV_PATH, "w") as f:
        f.write(env_content)
    print(f"\n✅ Configuration saved to {ENV_PATH}")

    print("\n4. Vérification de FFmpeg...")
    if shutil.which("ffmpeg"):
        print("   ✅ FFmpeg trouvé!")
    else:
        print("   ⚠️  FFmpeg non trouvé!")
        print("   → Télécharge FFmpeg: https://ffmpeg.org/download.html")
        print("   → Ajoute-le au PATH système")

    print("\n5. Installation des dépendances...")
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        os.system(f"pip install -r {req_path}")
        print("   ✅ Dépendances installées!")

    print("\n" + "=" * 60)
    print("  Configuration terminée!")
    print("=" * 60)
    print("\nProchaines étapes:")
    print("  1. Vérifie ton fichier .env avec les bonnes clés")
    print("  2. Lance le test: python main.py test")
    print("  3. Lance le bot: python main.py run")
    print("  4. Ou lance le scheduler 24/7: python main.py")
    print()


if __name__ == "__main__":
    setup()
