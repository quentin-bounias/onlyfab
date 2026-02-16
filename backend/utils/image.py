from PIL import Image
import os
import io

TARGET_WIDTH = 600
TARGET_HEIGHT = 900
MAX_SIZE_BYTES = 200 * 1024  # 0.2 Mo


def process_image(input_path: str, output_path: str) -> None:
    """
    Prend une image source (n'importe quel format/ratio),
    la recadre intelligemment au centre, la redimensionne en 600x900
    et la compresse en JPEG < 0.2Mo.
    """
    with Image.open(input_path) as img:
        # Convertit tout en RGB (gère PNG transparent, WEBP, etc.)
        img = img.convert("RGB")

        src_w, src_h = img.size
        target_ratio = TARGET_WIDTH / TARGET_HEIGHT
        src_ratio = src_w / src_h

        # --- Crop intelligent au centre ---
        if src_ratio > target_ratio:
            # Image trop large → on coupe les côtés
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, src_h))
        elif src_ratio < target_ratio:
            # Image trop haute → on coupe le haut et le bas
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            img = img.crop((0, top, src_w, top + new_h))

        # --- Resize vers 600x900 ---
        img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)

        # --- Compression JPEG progressive ---
        quality = 85
        while quality >= 10:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            if buffer.tell() <= MAX_SIZE_BYTES:
                break
            quality -= 5

        # Sauvegarde finale
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())


def get_media_path(base_dir: str, filename: str) -> str:
    """Retourne le chemin absolu d'un fichier dans /media."""
    return os.path.join(base_dir, "media", filename)
