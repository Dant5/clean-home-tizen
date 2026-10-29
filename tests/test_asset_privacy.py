"""Published pictures must not carry camera, owner, location or comment metadata."""
from pathlib import Path
import sys
from PIL import Image, ExifTags
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from privacy_rules import content_findings

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_TAGS = {'GPSInfo', 'MakerNote', 'CameraOwnerName', 'BodySerialNumber', 'SerialNumber', 'LensSerialNumber', 'ImageUniqueID', 'UserComment'}


def test_image_metadata_does_not_identify_an_owner_or_location():
    for folder in [ROOT / 'app/assets', ROOT / 'docs/images']:
        for path in folder.rglob('*'):
            if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
                continue
            with Image.open(path) as image:
                exif = image.getexif()
                fields = dict(exif)
                if 34665 in exif:
                    fields.update(exif.get_ifd(34665))
                assert not any(ExifTags.TAGS.get(key) in PRIVATE_TAGS and value for key, value in fields.items()), str(path.relative_to(ROOT))
                # Copyright/colour/resolution metadata is not personal owner data.
                for value in getattr(image, 'text', {}).values():
                    assert not content_findings(path.relative_to(ROOT).as_posix(), str(value)), str(path.relative_to(ROOT))
