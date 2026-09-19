"""File d'attente de publication : READY -> SCHEDULED -> PUBLISHED | FAILED.

Règles :
- SCHEDULED = planifiée OU envoyée à TikTok (publish_id présent) mais pas encore confirmée.
- PUBLISHED n'est posé QUE si l'API TikTok (post/publish/status/fetch) répond PUBLISH_COMPLETE.
  Un upload réussi ne suffit pas : TikTok traite la vidéo en asynchrone.
- `publish` envoie réellement une vidéo sur le compte connecté : il exige --confirm.

Usage :
  python video_pipeline/publish_queue.py status
  python video_pipeline/publish_queue.py schedule <video_id> <ISO-UTC>
  python video_pipeline/publish_queue.py publish <video_id> --confirm
  python video_pipeline/publish_queue.py verify [<video_id>]
"""
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
QUEUE = VIDEOS / "queue.json"
STATES = ("READY", "SCHEDULED", "PUBLISHED", "FAILED")


def now():
    return datetime.now(timezone.utc).isoformat()


def load():
    return json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else []


def save(queue):
    QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")


def find(queue, video_id):
    return next((e for e in queue if e["video_id"] == video_id), None)


def sync():
    """Ajoute à la file toute vidéo dont le mp4 ET les métadonnées existent."""
    queue = load()
    for meta_path in sorted((VIDEOS / "metadata").glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        vid = meta["video_id"]
        if find(queue, vid) or not (VIDEOS / "ready" / f"{vid}.mp4").exists():
            continue
        queue.append({
            "video_id": vid, "state": "READY", "file": f"ready/{vid}.mp4",
            "caption": meta.get("caption", ""), "hashtags": meta.get("hashtags", []),
            "created_utc": now(), "scheduled_for_utc": None, "publish_id": None,
            "published_at_utc": None, "published_evidence": None, "error": None,
        })
    save(queue)
    return queue


def status():
    for e in sync():
        print(f"{e['video_id']:10} {e['state']:10} sched={e['scheduled_for_utc']} "
              f"publish_id={e['publish_id']} err={e['error']}")


def schedule(video_id, when_utc):
    queue = sync()
    e = find(queue, video_id)
    if not e:
        sys.exit(f"{video_id} introuvable")
    if e["state"] not in ("READY", "FAILED"):
        sys.exit(f"{video_id} est {e['state']}, pas planifiable")
    datetime.fromisoformat(when_utc)  # valide le format
    e.update(state="SCHEDULED", scheduled_for_utc=when_utc, error=None)
    save(queue)
    print(f"{video_id} -> SCHEDULED {when_utc}")


def _agent():
    sys.path.insert(0, str(ROOT))
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    from agents.tiktok_publisher import TikTokPublisherAgent
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    return TikTokPublisherAgent(config)


def publish(video_id):
    """Upload réel vers TikTok. Ne marque JAMAIS PUBLISHED : voir verify()."""
    queue = sync()
    e = find(queue, video_id)
    if not e:
        sys.exit(f"{video_id} introuvable")
    if e["state"] == "PUBLISHED":
        sys.exit(f"{video_id} déjà PUBLISHED")
    path = VIDEOS / e["file"]
    if not path.exists():
        e.update(state="FAILED", error="fichier absent de ready/")
        save(queue)
        sys.exit(e["error"])
    agent = _agent()
    if not agent.access_token:
        e.update(state="FAILED", error="TIKTOK_ACCESS_TOKEN absent : lancer auth_tiktok.py")
        save(queue)
        sys.exit(e["error"])
    publish_id = agent._upload_video_api(str(path))
    if not publish_id:
        e.update(state="FAILED", error="upload API TikTok refusé (voir logs)")
        save(queue)
        sys.exit(e["error"])
    e.update(state="SCHEDULED", publish_id=publish_id, error=None)
    save(queue)
    print(f"{video_id} envoyé à TikTok (publish_id={publish_id}). Lancer `verify` pour confirmer.")


def verify(video_id=None):
    """Interroge TikTok sur le statut réel de chaque envoi en attente."""
    import requests
    queue = load()
    agent = _agent()
    for e in queue:
        if e["state"] != "SCHEDULED" or not e["publish_id"]:
            continue
        if video_id and e["video_id"] != video_id:
            continue
        r = requests.post(
            f"{agent.TIKTOK_API_BASE}/post/publish/status/fetch/",
            headers={"Authorization": f"Bearer {agent.access_token}",
                     "Content-Type": "application/json; charset=UTF-8"},
            json={"publish_id": e["publish_id"]}, timeout=15)
        data = r.json().get("data", {}) if r.ok else {}
        st = data.get("status")
        print(f"{e['video_id']}: HTTP {r.status_code} status={st}")
        if st == "PUBLISH_COMPLETE":
            e.update(state="PUBLISHED", published_at_utc=now(),
                     published_evidence={"status": st, "publish_id": e["publish_id"],
                                         "post_ids": data.get("publicaly_available_post_id")})
            (VIDEOS / "published").mkdir(exist_ok=True)
            shutil.copy2(VIDEOS / e["file"], VIDEOS / "published" / f"{e['video_id']}.mp4")
        elif st == "FAILED":
            e.update(state="FAILED", error=data.get("fail_reason", "FAILED"))
            (VIDEOS / "failed").mkdir(exist_ok=True)
    save(queue)


def main():
    a = sys.argv[1:]
    if not a or a[0] == "status":
        status()
    elif a[0] == "sync":
        sync()
    elif a[0] == "schedule" and len(a) == 3:
        schedule(a[1], a[2])
    elif a[0] == "publish" and len(a) == 3 and "--confirm" in a:
        publish(a[1])
    elif a[0] == "publish":
        sys.exit("publish envoie une vidéo sur ton compte TikTok : ajoute --confirm")
    elif a[0] == "verify":
        verify(a[1] if len(a) > 1 else None)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
