"""Create design assets and inspect only explicitly configured project files."""

import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys


REFERENCES = Path(__file__).resolve().parents[1] / "references"
SKILLS = REFERENCES.parents[1]
COLOR_ROLES = ("primary", "on-primary", "background", "foreground", "card", "muted",
               "muted-foreground", "border", "ring")


def design_tokens(query, platform):
    script = SKILLS / "ui-ux-pro-max/scripts/search.py"
    try:
        run = subprocess.run(
            [sys.executable, "-B", str(script), "--design-system", "--tokens", "dtcg", "--", query],
            capture_output=True, check=True, timeout=10, text=True, encoding="utf-8",
        )
        data = json.loads(run.stdout)
        colors = {role: data["color"][role]["$value"] for role in COLOR_ROLES}
        if not all(isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) for value in colors.values()):
            raise ValueError("Invalid colors")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
        raise ValueError("UI/UX Pro Max did not produce a usable token file. Retry with a focused product query.") from error

    if platform == "web":
        roles = {"primary": "primary", "on-primary": "primary-foreground", "background": "background",
                 "foreground": "foreground", "card": "card", "muted": "muted",
                 "muted-foreground": "muted-foreground", "border": "border", "ring": "ring"}
        values = "\n".join(f"  --cosmos-{role}: {value};" for role, value in colors.items())
        mapping = "\n".join(f"  --{css}: var(--cosmos-{role});" for role, css in roles.items())
        file = {"path": "src/cosmos-tokens.css", "content": f":root {{\n{values}\n{mapping}\n}}\n"}
    else:
        roles = {role: re.sub(r"-([a-z])", lambda m: m[1].upper(), role) for role in colors}
        entries = []
        for role, value in colors.items():
            r, g, b = (int(value[i:i+2], 16) for i in (1, 3, 5))
            entries.append(f"    static let {roles[role]} = Color(red: {r}.0/255, green: {g}.0/255, blue: {b}.0/255)")
        file = {"path": "CosmosTheme.swift", "content": "import SwiftUI\n\nenum CosmosTheme {\n" + "\n".join(entries) + "\n}\n"}
    return {"generator": "ui-ux-pro-max/scripts/search.py", "query": query,
            "colors": colors, "fontSuggestions": data.get("font", {}),
            "file": file, "roles": list(roles.values())}


def component_assets():
    root = REFERENCES / "components"
    component = json.loads((root / "button.json").read_text())
    component["files"] = [
        {"path": component["path"], "content": (root / "button.tsx").read_text()},
        {"path": "src/lib/utils.ts", "content": (root / "utils.ts").read_text()},
    ]
    component["newProjectSetup"] = {
        "config": json.loads((root / "components.json").read_text()),
        "tailwindV4Theme": (root / "neutral-button-theme.css").read_text(),
        "instructions": "For a new neutral React project, adapt aliases and stylesheet paths, merge the theme after the Tailwind import, and configure the same @ alias in the bundler and tsconfig. For an existing configured app preserve its theme unless a neutral appearance was requested. Render actions with Button variants and place layout rules on wrappers.",
    }
    return component


def project_file(name, max_bytes=1_000_000):
    base = os.environ.get("COSMOS_PROJECT_ROOT")
    if not base:
        raise ValueError("Source verification requires COSMOS_PROJECT_ROOT set to your project directory when starting the Cosmos MCP.")
    root = Path(base)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError("COSMOS_PROJECT_ROOT must be an absolute path to a project directory.")
    root = root.resolve()
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Use paths relative to the configured project root.")
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f"Project artifact is missing or outside the project root: {name}")
    with path.open("rb") as file:
        content = file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError(f"Project artifact exceeds the inspection limit: {name}")
    return content


def sha(content):
    return hashlib.sha256(content).hexdigest()


def installed_button(sources, entry):
    # Recognize a named Button import from the matching source, including renamed imports.
    entry_source = sources[entry]
    for match in re.finditer(r"\bimport\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]", entry_source):
        symbols, specifier = match.groups()
        imported = re.search(r"(?:^|,)\s*Button(?:\s+as\s+(\w+))?\s*(?:,|$)", symbols)
        if not imported or not re.search(r"<" + re.escape(imported[1] or "Button") + r"(?=\s|>)", entry_source):
            continue
        if specifier.startswith("@/"):
            stems = [Path("src") / specifier[2:], Path(specifier[2:])]
        elif specifier.startswith("."):
            stems = [Path(os.path.normpath(Path(entry).parent / specifier))]
        else:
            continue
        for stem in stems:
            for path in (stem, stem.with_suffix(".tsx"), stem / "index.tsx"):
                code = sources.get(str(path))
                if code and "buttonVariants" in code and "class-variance-authority" in code and re.search(r"\bexport\b[^\n]*\bButton\b", code):
                    bundled = component_assets()["files"][0]["content"]
                    return {"path": str(path), "sha256": sha(code.encode()),
                            "source": "bundled shadcn registry" if code == bundled else "project Button with shadcn-compatible structure"}
    raise ValueError("No imported shadcn Button usage was found. Include the actual component file and the entry that renders it; plain HTML buttons alone do not satisfy this stack.")


def inspect_implementation(platform, stack, token_asset, paths, entry, copy_sample):
    if entry not in paths:
        raise ValueError("entry must be included in artifacts.")
    contents = {name: project_file(name) for name in paths}
    try:
        files = {name: content.decode("utf-8") for name, content in contents.items()}
    except UnicodeDecodeError as error:
        raise ValueError("Implementation artifacts must be UTF-8 source files.") from error
    expected = token_asset["file"]["content"]
    token_file = next((name for name, content in files.items() if content.strip() == expected.strip()), None)
    if not token_file:
        raise ValueError("Include the generated token file, with its values, in artifacts.")
    code = files[entry]
    body_sources = [content for name, content in files.items()
                    if Path(name).suffix in {".swift", ".jsx", ".tsx", ".js", ".ts", ".html"}]
    if not any(copy_sample.casefold() in " ".join(content.split()).casefold() for content in body_sources):
        raise ValueError("The approved visible copy sample is missing from the implementation source.")
    if platform == "ios":
        if "import SwiftUI" not in code or not re.search(r"CosmosTheme\.", code):
            raise ValueError("The SwiftUI entry must use the generated CosmosTheme.")
    else:
        style_sources = "\n".join(code for name, code in files.items() if name != token_file)
        if not re.search(r"var\(--(?:cosmos-)?(?:background|foreground|primary|muted|card)\b", style_sources):
            raise ValueError("Use the generated semantic tokens in the interface styles.")
        if not re.search(r"cosmos-tokens\.css", style_sources):
            raise ValueError("Link or import cosmos-tokens.css in the submitted page or styles.")
    button = installed_button(files, entry) if stack == "shadcn" else None
    return {"entry": entry, "tokenFile": token_file, "approvedCopyFoundInSource": True, "shadcnButton": button,
            "artifacts": {name: sha(content) for name, content in contents.items()}}


def inspect_render(names):
    images = []
    for name in dict.fromkeys(names):
        data = project_file(name, max_bytes=2_000_000)
        if len(data) < 33 or data[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" or not data.endswith(b"IEND\xaeB\x60\x82"):
            raise ValueError(f"Expected a PNG screenshot file: {name}")
        width, height = struct.unpack(">II", data[16:24])
        if not 100 <= width <= 4096 or not 100 <= height <= 8192:
            raise ValueError(f"Screenshot dimensions are outside the supported range: {name}")
        images.append(({"path": name, "width": width, "height": height, "sha256": sha(data)}, data))
    return images


def inspect_browser_report(path, screenshots, copy_sample, token_colors, registry_buttons=False):
    try:
        report = json.loads(project_file(path))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Browser evidence must be a valid Cosmos browser report.") from error
    if not isinstance(report, dict) or report.get("schema") != "cosmos-browser-1":
        raise ValueError("Browser evidence must be a Cosmos browser report.")
    rows = report.get("viewports")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("Missing viewport checks in browser report.")
    widths = {row.get("width") for row in rows if type(row.get("width")) is int}
    if not {390, 768, 1440} <= widths:
        raise ValueError("Browser evidence must cover 390, 768 and 1440 px.")
    if any(row.get("errors") != 0 or row.get("axeViolations") != 0 or row.get("overflow") is not False
           or row.get("keyboard") is not True or row.get("reducedMotion") is not True
           or row.get("primaryFlow") is not True for row in rows):
        raise ValueError("Browser report contains failures or missing checks.")
    for row in rows:
        probes = row.get("designProbes")
        if (not isinstance(probes, list) or len(probes) != 3 or
            not all(isinstance(p, dict) and isinstance(p.get("actual"), str) and p["actual"].strip()
                    and p["actual"] == p.get("expected") and p.get("selector") for p in probes)
            or {p.get("key") for p in probes} != {"composition", "copy", "token"}):
            raise ValueError("Run render-decisions.cjs for visible composition, copy and a generated token on every viewport.")
        indexed = {p["key"]: p for p in probes}
        words = " ".join(copy_sample.casefold().split())
        if not any(words in " ".join(indexed[key]["actual"].casefold().split()) for key in ("copy", "composition")):
            raise ValueError("One visible content probe must include the approved copy sample.")
        token = indexed["token"]
        role = token.get("token", "")
        if not isinstance(role, str) or not role.startswith("--cosmos-") or role.removeprefix("--cosmos-") not in token_colors:
            raise ValueError("Select a color from this workflow's generated token file.")
        value = token_colors[role.removeprefix("--cosmos-")].lstrip("#")
        rgb = "rgb(" + ", ".join(str(int(value[i:i+2], 16)) for i in (0, 2, 4)) + ")"
        if token["actual"] != rgb:
            raise ValueError("The rendered CSS color differs from the original generated token.")
    if registry_buttons:
        for row in rows:
            buttons = row.get("buttons")
            if not isinstance(buttons, list) or not buttons or not all(
                isinstance(b, dict) and b.get("variant") and b.get("size") and b.get("differences") == []
                for b in buttons
            ):
                raise ValueError("Run the browser audit with shadcnButtons selecting the visible actions. Their computed styles must match the bundled registry.")
    proofs = report.get("screenshots")
    if not isinstance(proofs, dict) or any(proofs.get(item["path"]) != item["sha256"] for item in screenshots):
        raise ValueError("Browser report must identify the opened screenshots by path and SHA-256.")
    for row in rows:
        if "referenceTargets" in row and (
            not isinstance(row["referenceTargets"], list)
            or not all(isinstance(target, str) for target in row["referenceTargets"])
            or not isinstance(row.get("screenshot"), str)
            or row["screenshot"] not in proofs
            or any(shot["path"] == row["screenshot"] and shot["width"] != row["width"] for shot in screenshots)
        ):
            raise ValueError("Invalid browser reference targets or screenshot association.")
    return {"path": path, "widths": sorted(widths), "screenshots": proofs, "viewports": rows}
