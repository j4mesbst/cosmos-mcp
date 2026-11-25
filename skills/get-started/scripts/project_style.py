"""Explicit local project memory for reviewed visual decisions."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from design_assets import project_file

STYLE_PATH = ".cosmos-style.json"


def style_root():
    if os.environ.get("COSMOS_ENABLE_STYLE_MEMORY") != "1":
        raise ValueError("Style memory is disabled. Enable it explicitly for this local project.")
    configured = os.environ.get("COSMOS_PROJECT_ROOT")
    if not configured:
        raise ValueError("Style memory requires a configured project root.")
    root = Path(configured)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("Style memory requires an absolute project directory.")
    return root.resolve()


def load_style():
    root = style_root()
    target = root / STYLE_PATH
    if target.is_symlink():
        raise ValueError("Project style must be a regular local file.")
    if not target.exists():
        return None
    try:
        style = json.loads(project_file(STYLE_PATH, 16_000))
    except (ValueError, OSError) as error:
        raise ValueError("Project style file is invalid or unavailable.") from error
    if not isinstance(style, dict) or style.get("schemaVersion") != 1:
        raise ValueError("Unsupported project style version.")
    return style


def save_style(contract, tokens):
    root = style_root()
    style = {"schemaVersion": 1, "direction": contract["direction"],
             "signature": contract["visualSignature"], "stack": contract["target"]["stack"],
             "platform": contract["target"]["platform"], "colors": tokens["colors"]}
    temporary = None
    try:
        with NamedTemporaryFile("w", dir=root, encoding="utf-8", delete=False) as output:
            temporary = Path(output.name)
            json.dump(style, output, ensure_ascii=False, indent=2)
            output.write("\n")
        temporary.replace(root / STYLE_PATH)
    except OSError as error:
        raise ValueError("Could not save local project style.") from error
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return STYLE_PATH
