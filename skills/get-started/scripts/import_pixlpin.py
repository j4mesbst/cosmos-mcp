"""Import the categorized archive supplied with Cosmos. Pillow is needed only for import."""
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import ZipFile

from PIL import Image

root = Path(__file__).resolve().parents[1] / "references"
entries = []
with ZipFile(sys.argv[1]) as archive:
    images = [name for name in archive.namelist() if name.endswith(".webp")]
    rows = list(csv.DictReader(io.StringIO(archive.read("manifest.csv").decode("utf-8-sig"))))
    if len(set(images)) != len(images) or sorted(images) != sorted(row["file"] for row in rows):
        raise ValueError("Manifest and archive images must match uniquely.")
    for row in rows:
        relative = PurePosixPath(row["file"])
        category = row["category"]
        if (len(relative.parts) != 3 or relative.parts[:2] != ("Web", category)
                or not all(re.fullmatch(r"[\w-]+", value) for value in (category, relative.stem))
                or row["platform"] != "Web"):
            raise ValueError(f"Invalid archive path: {relative}")
        payload = archive.read(str(relative))
        digest = hashlib.sha256(payload).hexdigest()
        original = root / "pixlpin" / relative
        preview = original.with_suffix(".jpg").relative_to(root)
        preview = Path("pixlpin-previews", *preview.parts[1:])
        original.parent.mkdir(parents=True, exist_ok=True)
        (root / preview).parent.mkdir(parents=True, exist_ok=True)
        with Image.open(io.BytesIO(payload)) as image:
            size = f"{image.width}x{image.height}"
            image.thumbnail((960, 960))
            image.convert("RGB").save(root / preview, "JPEG", quality=80, optimize=True)
        original.write_bytes(payload)
        entries.append({
            "id": f"pixlpin-{relative.stem}", "title": f'{row["app"]} / {category}',
            "collection": "Pixlpin Web", "app": row["app"], "platform": "web", "kind": "screenshot",
            "category": category, "screenType": category, "structure": row["alt"],
            "classification": row["how_classified"], "classificationReason": row["reason"],
            "file": str(original.relative_to(root)), "preview": str(preview), "size": size,
            "previewSize": [image.width, image.height], "sha256": digest,
            "archiveBytes": len(payload), "originalManifestSha256": row["sha256"],
            "sourceUrl": row["source_url"], "sourceScreenId": row["screen_id"],
            "pageOrder": int(row["page_order"]), "provenance": "User-supplied Pixlpin archive",
            "adapt": "Observe concrete layout and controls before adapting the reference.",
        })
if len({entry["id"] for entry in entries}) != len(entries):
    raise ValueError("Duplicate reference IDs")
(root / "pixlpin-catalog.json").write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + "\n")
print(f"Imported {len(entries)} images in {len({e['category'] for e in entries})} categories")
