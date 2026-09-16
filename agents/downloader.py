import os
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class DownloaderAgent:
    """
    Agent 2 : Téléchargement et stockage cloud.
    Télécharge les vidéos depuis les APIs et les stocke localement
    ou sur Google Drive.
    """

    def __init__(self, config: dict):
        self.config = config
        self.storage_config = config.get("cloud_storage", {})
        self.temp_dir = self.storage_config.get("local_path", "./temp")
        self.output_dir = self.storage_config.get("local_path", "./output")
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_filename(self, video_info: dict) -> str:
        vid_id = video_info.get("id", "unknown")
        safe_id = hashlib.md5(vid_id.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"raw_{safe_id}_{timestamp}.mp4"

    def _check_storage_space(self) -> bool:
        max_mb = self.storage_config.get("max_storage_mb", 5000)
        total_size = 0
        for dirpath in [self.temp_dir, self.output_dir]:
            for dirpath, _, filenames in os.walk(dirpath):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
        total_mb = total_size / (1024 * 1024)
        logger.info(f"Storage used: {total_mb:.1f}MB / {max_mb}MB")
        return total_mb < max_mb

    def _cleanup_old_files(self):
        if not self.storage_config.get("cleanup_after_post", True):
            return
        max_mb = self.storage_config.get("max_storage_mb", 5000)
        total_size = 0
        files = []
        for dirpath, _, filenames in os.walk(self.temp_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                size = os.path.getsize(fp)
                total_size += size
                files.append((fp, size, os.path.getmtime(fp)))
        files.sort(key=lambda x: x[2])
        total_mb = total_size / (1024 * 1024)
        while total_mb > max_mb * 0.8 and files:
            fp, size, _ = files.pop(0)
            os.remove(fp)
            total_mb -= size / (1024 * 1024)
            logger.info(f"Cleaned up: {fp}")

    def _upload_to_google_drive(self, filepath: str) -> bool:
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            creds_path = self.storage_config.get("google_drive_credentials", "")
            if not creds_path or not os.path.exists(creds_path):
                logger.warning("Google Drive credentials not found")
                return False

            creds = Credentials.from_authorized_user_file(creds_path)
            service = build("drive", "v3", credentials=creds)

            file_metadata = {
                "name": os.path.basename(filepath),
                "mimeType": "video/mp4",
            }
            media = MediaFileUpload(filepath, mimetype="video/mp4", resumable=True)
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            logger.info(f"Uploaded to Google Drive: {file.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Google Drive upload failed: {e}")
            return False

    def download_video(self, video_info: dict) -> str:
        """
        Télécharge la vidéo depuis l'URL fournie.
        Retourne le chemin local du fichier téléchargé.
        """
        import requests

        if not self._check_storage_space():
            self._cleanup_old_files()

        url = video_info.get("url")
        if not url:
            raise ValueError("No download URL provided in video_info")

        filename = self._get_filename(video_info)
        filepath = os.path.join(self.temp_dir, filename)

        logger.info(f"Downloading: {url}")
        try:
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"Downloaded: {filepath} ({file_size:.1f}MB)")

            video_info["local_path"] = filepath
            video_info["file_size_mb"] = file_size

            provider = self.storage_config.get("provider", "local")
            if provider == "google_drive" or self.storage_config.get(
                "google_drive_enabled", False
            ):
                self._upload_to_google_drive(filepath)

            return filepath

        except Exception as e:
            logger.error(f"Download failed: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
            raise

    def get_editable_path(self, video_info: dict) -> str:
        return video_info.get("local_path", "")

    def get_output_path(self, video_info: dict, suffix: str = "edited") -> str:
        vid_id = video_info.get("id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{suffix}_{vid_id}_{timestamp}.mp4"
        return os.path.join(self.output_dir, filename)


def download(video_info: dict, config: dict) -> str:
    agent = DownloaderAgent(config)
    return agent.download_video(video_info)
