"""Pre-render the upstream 32px header blur at quarter resolution, off the TV."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
root = Path(__file__).resolve().parents[1] / 'app/assets/wallpapers'
for path in sorted(root.glob('*.jpg')):
    if path.stem.endswith(('-thumb', '-lens')):
        continue
    image = Image.open(path).convert('RGB').resize((480, 270), Image.Resampling.LANCZOS)
    image = ImageEnhance.Color(image.filter(ImageFilter.GaussianBlur(8))).enhance(1.06)
    image = ImageEnhance.Brightness(image).enhance(.9)
    image.save(path.with_stem(path.stem + '-lens'), quality=80, optimize=True)
print('Prepared bundled header glass; no live CSS blur required.')
