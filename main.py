import ffmpeg
import os
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Configuration constants
INPUT_DIR = Path("./input")
OUTPUT_DIR = Path("./output")
DEFAULT_IMAGE = Path("./input/cover.jpg")
VIDEO_RESOLUTION = "1920x1080"
VISUALIZER_HEIGHT = 200  # Changed to int
VIDEO_FPS = 30


def sanitize_filename(name: str) -> str:
    # Remove potentially dangerous characters for filesystem
    return "".join(c for c in name if c.isalnum() or c in "._- ")


def build_ffmpeg_command(
    audio_path: Path, image_path: Path, output_path: Path
) -> Tuple[List[str], dict]:
    """
    Строим команду FFmpeg вручную для полного контроля.
    """
    width, height = VIDEO_RESOLUTION.split("x")
    width = int(width)
    height = int(height)

    inputs = [
        "-loop",
        "1",
        "-framerate",
        str(VIDEO_FPS),
        "-i",
        str(image_path),  # [0:v] - изображение
        "-i",
        str(audio_path),  # [1:a] - аудио
    ]

    # ИСПРАВЛЕНИЕ: Правильный синтаксис для pad — отдельные аргументы w и h
    # Было: pad=1920x1080:(ow-iw)/2:(oh-ih)/2:black
    # Стало: pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black
    video_filter = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black[bg]"
    )

    # Визуализатор аудио
    viz_filter = (
        f"[1:a]showwaves=s={width}x{VISUALIZER_HEIGHT}:mode=line:colors=white,"
        f"format=rgba[viz]"
    )

    # Оверлей визуализатора на фон (в самый низ)
    overlay_filter = "[bg][viz]overlay=0:H-h:format=auto[video]"

    filter_complex = f"{video_filter};{viz_filter};{overlay_filter}"

    outputs = [
        "-map",
        "[video]",  # берём видео из filter_complex
        "-map",
        "1:a",  # берём аудио из второго input
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(VIDEO_FPS),
        "-shortest",  # останавливаемся когда закончится аудио
        "-y",  # перезаписывать существующие файлы
        str(output_path),
    ]

    cmd = ["ffmpeg"] + inputs + ["-filter_complex", filter_complex] + outputs

    return cmd, {}


def process_track(audio_path: Path, image_path: Path, output_path: Path) -> bool:
    try:
        if not audio_path.exists() or not image_path.exists():
            print(f"Skip: Missing files for {audio_path.name}")
            return False

        # Удаляем пустой файл если он есть
        if output_path.exists():
            if output_path.stat().st_size == 0:
                output_path.unlink()
                print(f"Removed empty file: {output_path.name}")
            else:
                print(f"Skip: {output_path.name} already exists and not empty.")
                return False

        print(f"Processing: {audio_path.name} -> {output_path.name}")

        # Строим команду
        cmd, _ = build_ffmpeg_command(audio_path, image_path, output_path)

        # Для отладки: выводим команду
        print(f"FFmpeg command: {' '.join(cmd)}")

        # Запускаем через subprocess для полного контроля
        import subprocess

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            print(f"FFmpeg error (code {result.returncode}):")
            print(result.stderr)
            # Удаляем битый файл
            if output_path.exists():
                output_path.unlink()
            return False

        # Проверяем что файл создался и не пустой
        if not output_path.exists() or output_path.stat().st_size == 0:
            print(f"Error: Output file is missing or empty")
            return False

        print(f"Success: {output_path.name} ({output_path.stat().st_size} bytes)")
        return True

    except Exception as e:
        print(f"Critical error for {audio_path.name}: {str(e)}")
        import traceback

        traceback.print_exc()
        # Очистка при ошибке
        if output_path.exists():
            try:
                output_path.unlink()
            except:
                pass
        return False


def main():
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not INPUT_DIR.exists():
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        sys.exit(1)

    # Collect audio files
    audio_files = list(INPUT_DIR.glob("*.mp3")) + list(INPUT_DIR.glob("*.wav"))

    if not audio_files:
        print("No audio files found in input directory.")
        sys.exit(0)

    # Проверяем что ffmpeg доступен
    import shutil

    if not shutil.which("ffmpeg"):
        print(
            "Error: ffmpeg not found in PATH. Please install FFmpeg and add it to PATH."
        )
        sys.exit(1)

    success_count = 0
    fail_count = 0

    for audio_path in audio_files:
        stem = audio_path.stem

        # Look for matching image
        image_path = None
        for ext in [".jpg", ".jpeg", ".png"]:
            potential_img = INPUT_DIR / f"{stem}{ext}"
            if potential_img.exists():
                image_path = potential_img
                break

        # Fallback to default image
        if not image_path:
            if DEFAULT_IMAGE.exists():
                image_path = DEFAULT_IMAGE
                print(f"Warning: No image for {stem}, using default.")
            else:
                print(f"Error: No image for {stem} and no default found.")
                fail_count += 1
                continue

        # Construct output path
        safe_name = sanitize_filename(stem)
        output_path = OUTPUT_DIR / f"{safe_name}.mp4"

        if process_track(audio_path, image_path, output_path):
            success_count += 1
        else:
            fail_count += 1

    print(f"\nBatch finished. Success: {success_count}, Failed: {fail_count}")


if __name__ == "__main__":
    main()
