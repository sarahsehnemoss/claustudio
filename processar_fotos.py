"""Processa as fotos das peças: remove fundo, centraliza o objeto em quadrado limpo.
- Backup dos originais vai pra C:\\CLAUSTUDIO\\_originals_backup\\
- Sobre-escreve as fotos em Fotos.site/ com a versão processada (1200x1200, fundo #F4F4F4)
Uso: python processar_fotos.py
"""
import shutil
from pathlib import Path
from PIL import Image, ImageOps

BASE = Path(__file__).parent
FOTOS = BASE / "Fotos.site"
BACKUP = BASE / "_originals_backup"
EXTS = {".jpg", ".jpeg", ".png", ".webp"}
BG = (244, 244, 244)  # #F4F4F4 — mesmo tom do card no site
SIZE = 1200

def tem_rembg():
    try:
        from rembg import remove  # noqa
        return True
    except Exception:
        return False

def main():
    if not FOTOS.exists():
        print("Pasta Fotos.site nao encontrada"); return

    usa_rembg = tem_rembg()
    print(f"rembg: {'sim' if usa_rembg else 'nao — so center-crop + auto-level'}")

    # 1. backup dos originais (so se ainda nao existir)
    if not BACKUP.exists():
        print(f"Backup dos originais -> {BACKUP}")
        shutil.copytree(FOTOS, BACKUP)
    else:
        print("Backup ja existe, pulando (originais preservados)")

    n = 0
    for img_path in sorted(FOTOS.rglob("*")):
        if not img_path.is_file() or img_path.suffix.lower() not in EXTS:
            continue
        try:
            im = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"  [skip] {img_path.name}: {e}"); continue

        if usa_rembg:
            from rembg import remove
            rmb = remove(im)  # RGBA
            # recorta pro bounding box do objeto (alpha)
            bbox = rmb.getbbox()
            if bbox:
                rmb = rmb.crop(bbox)
            # centraliza em quadrado
            lado = max(rmb.size)
            canvas = Image.new("RGBA", (lado, lado), BG + (255,))
            x = (lado - rmb.size[0]) // 2
            y = (lado - rmb.size[1]) // 2
            canvas.alpha_composite(rmb, (x, y))
            out = canvas.convert("RGB")
        else:
            # fallback: center-crop quadrado + auto-contraste
            out = ImageOps.fit(im, (min(im.size), min(im.size)), method=Image.LANCZOS)
            out = ImageOps.autocontrast(out)

        out = out.resize((SIZE, SIZE), Image.LANCZOS)
        out.save(img_path, "JPEG", quality=92, optimize=True)
        n += 1
        print(f"  [ok] {img_path.relative_to(FOTOS)}")

    print(f"\n{n} fotos processadas.")
    if usa_rembg:
        print("Fundo removido e objetos centralizados em fundo #F4F4F4.")
    print(f"Originais preservados em {BACKUP}")

if __name__ == "__main__":
    main()
