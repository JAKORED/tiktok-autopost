import os
import logging
import subprocess
import shutil
from typing import Optional

logger = logging.getLogger(__name__)


class VideoEditorAgent:
    """
    Agent 3 : Édition automatique des vidéos.
    Utilise FFmpeg pour ajouter texte, musique, sous-titres,
    transitions et effets sur chaque vidéo avant publication.
    """

    def __init__(self, config: dict):
        self.config = config
        self.edit_config = config.get("video_editing", {})
        self.ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg
        for path in [
            "ffmpeg",
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
        ]:
            if os.path.exists(path):
                return path
        logger.warning(
            "FFmpeg not found. Video editing will be limited. "
            "Install FFmpeg: https://ffmpeg.org/download.html"
        )
        return "ffmpeg"

    def _check_ffmpeg(self) -> bool:
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _crop_to_vertical(self, input_path: str, output_path: str) -> str:
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-vf", (
                "crop=ih*9/16:ih,"
                "scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
            ),
            "-c:v", self.edit_config.get("codec", "libx264"),
            "-c:a", self.edit_config.get("audio_codec", "aac"),
            "-preset", "fast",
            "-crf", "23",
            output_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg crop error: {e}")
            return input_path

    def _add_text_overlay(
        self, input_path: str, output_path: str, text: str
    ) -> str:
        style = self.edit_config.get("subtitle_style", {})
        font = style.get("font", "Arial")
        fontsize = style.get("fontsize", 48)
        fontcolor = style.get("fontcolor", "white")
        outline_color = style.get("outline_color", "black")
        outline_width = style.get("outline_width", 3)

        escaped_text = text.replace("'", "'\\''").replace(":", "\\:")

        drawtext = (
            f"drawtext=text='{escaped_text}'"
            f":fontfile='':fontsize={fontsize}"
            f":fontcolor={fontcolor}"
            f":borderw={outline_width}:bordercolor={outline_color}"
            f":x=(w-text_w)/2:y=100"
            f":enable='between(t,0,5)'"
        )

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-vf", drawtext,
            "-c:v", self.edit_config.get("codec", "libx264"),
            "-c:a", "copy",
            "-preset", "fast",
            output_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg text overlay error: {e}")
            return input_path

    def _add_background_music(
        self, input_path: str, output_path: str, music_path: Optional[str] = None
    ) -> str:
        if music_path and os.path.exists(music_path):
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-i", music_path,
                "-filter_complex",
                (
                    "[0:a]volume=1.0[a1];"
                    "[1:a]volume=0.3[a2];"
                    "[a1][a2]amix=inputs=2:duration=first[aout]"
                ),
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", self.edit_config.get("audio_codec", "aac"),
                "-preset", "fast",
                output_path,
            ]
        else:
            logger.info("No music file provided, skipping music overlay")
            return input_path

        try:
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg music overlay error: {e}")
            return input_path

    def _add_slow_motion_intro(
        self, input_path: str, output_path: str, duration: float = 0.5
    ) -> str:
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-vf",
            f"setpts=2.0*PTS,fade=in:0:15,fade=out:st=13:d=2",
            "-af",
            f"atempo=0.5,afade=in:0:15,afade=out:st=13:d=2",
            "-c:v", self.edit_config.get("codec", "libx264"),
            "-c:a", self.edit_config.get("audio_codec", "aac"),
            "-preset", "fast",
            "-t", "30",
            output_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg intro effect error: {e}")
            return input_path

    def edit_video(
        self,
        input_path: str,
        output_path: str,
        hook_text: str = "",
        music_path: Optional[str] = None,
        skip_editing: bool = False,
    ) -> str:
        """
        Pipeline d'édition complet :
        1. Recadrage vertical (9:16)
        2. Ajout du texte accrocheur
        3. Ajout musique de fond
        4. Effet slow-motion intro
        """
        if skip_editing or not self._check_ffmpeg():
            logger.warning(
                "FFmpeg not available, copying video as-is"
            )
            shutil.copy2(input_path, output_path)
            return output_path

        current = input_path
        temp_files = []

        logger.info("Step 1: Cropping to vertical 9:16...")
        cropped = output_path.replace(".mp4", "_cropped.mp4")
        result = self._crop_to_vertical(current, cropped)
        if result != current:
            temp_files.append(cropped)
            current = cropped

        if hook_text and self.edit_config.get("add_text_overlay", True):
            logger.info(f"Step 2: Adding text overlay: '{hook_text}'...")
            with_text = output_path.replace(".mp4", "_text.mp4")
            result = self._add_text_overlay(current, with_text, hook_text)
            if result != current:
                temp_files.append(with_text)
                current = with_text

        if self.edit_config.get("add_music", True) and music_path:
            logger.info("Step 3: Adding background music...")
            with_music = output_path.replace(".mp4", "_music.mp4")
            result = self._add_background_music(current, with_music, music_path)
            if result != current:
                temp_files.append(with_music)
                current = with_music

        logger.info("Step 4: Final encoding...")
        final_cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", current,
            "-c:v", self.edit_config.get("codec", "libx264"),
            "-c:a", self.edit_config.get("audio_codec", "aac"),
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            output_path,
        ]
        try:
            subprocess.run(final_cmd, capture_output=True, timeout=120, check=True)
        except subprocess.CalledProcessError:
            shutil.copy2(current, output_path)

        for tf in temp_files:
            if os.path.exists(tf) and tf != output_path:
                try:
                    os.remove(tf)
                except Exception:
                    pass

        final_size = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Edited video saved: {output_path} ({final_size:.1f}MB)")
        return output_path


def edit(
    input_path: str,
    output_path: str,
    hook_text: str = "",
    music_path: Optional[str] = None,
    config: dict = None,
) -> str:
    if config is None:
        config = {}
    agent = VideoEditorAgent(config)
    return agent.edit_video(input_path, output_path, hook_text, music_path)
