"""Versioned HeroUI source verification and local theSVG assets."""
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

from design_assets import project_file

PACKAGE = Path(__file__).resolve().parents[2]
LOGO_ARCHIVE = PACKAGE / "thesvg/references/the-svg-4.0.16.zip"
HERO_VERSION = "3.2.8"
HERO_EXPORTS = {"primary-action": "Button", "navigation": "Link", "dialog": "Modal",
                "selection": "Switch", "group": "Card"}


def project_ui():
    try:
        package = json.loads(project_file("package.json"))
    except (ValueError, OSError):
        return {"status": "unavailable"}
    dependencies = {**package.get("devDependencies", {}), **package.get("dependencies", {})}
    lockfiles = []
    for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"):
        root = Path(os.environ["COSMOS_PROJECT_ROOT"]).resolve()
        if (root / name).is_file():
            lockfiles.append(name)
    report = {"status": "detected", "react": dependencies.get("react"), "tailwind": dependencies.get("tailwindcss"),
              "packageManager": package.get("packageManager"), "lockfiles": lockfiles}
    if "@heroui/react" in dependencies:
        report["herouiDeclared"] = dependencies["@heroui/react"]
        try:
            report["herouiInstalled"] = json.loads(project_file("node_modules/@heroui/react/package.json"))["version"]
        except (ValueError, OSError, KeyError):
            pass
    return report


def hero_assets(project):
    if project.get("herouiDeclared"):
        version = project.get("herouiInstalled")
        install = None
        status = "verified-version" if version == HERO_VERSION else "requires-version-specific-review"
    else:
        version, status = HERO_VERSION, "validated-new-project-version"
        install = f"npm install -E @heroui/react@{version} @heroui/styles@{version} @babel/parser" if not (
            project.get("packageManager") and not project["packageManager"].startswith("npm@")
            or set(project.get("lockfiles", [])) - {"package-lock.json"}
        ) else None
    return {"library": "HeroUI", "version": version, "install": install, "status": status,
            "required": "Preserve the declared manager and dependencies. Import Tailwind CSS before HeroUI styles.",
            "docs": "https://heroui.com/en/docs/react",
            "roles": [{"role": role, "module": "@heroui/react", "export": export}
                      for role, export in HERO_EXPORTS.items()] if version == HERO_VERSION else []}


@lru_cache(maxsize=1)
def logo_catalog():
    with zipfile.ZipFile(LOGO_ARCHIVE) as archive:
        return json.load(io.BytesIO(archive.read("catalog.json")))


def find_logos(query):
    term = query.strip().casefold()
    ranked = []
    for slug, metadata in logo_catalog().items():
        names = [slug, metadata.get("title") or "", *(metadata.get("aliases") or [])]
        scores = [0 if term == name.casefold() else 1 if term in name.casefold() else 2 for name in names]
        if min(scores) < 2:
            ranked.append((min(scores), slug))
    return [{"slug":slug, **logo_catalog()[slug]} for _, slug in sorted(ranked)[:12]]


def logo_asset(slug):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,100}", slug):
        raise ValueError("Use a catalogue logo slug such as figma or vercel.")
    try:
        with zipfile.ZipFile(LOGO_ARCHIVE) as archive:
            svg = archive.read(slug + ".svg")
            metadata = logo_catalog()[slug]
    except KeyError as error:
        raise ValueError(f"No bundled theSVG mark for {slug}.") from error
    return {**metadata, "slug": slug, "sha256": hashlib.sha256(svg).hexdigest(),
            "path": f"public/cosmos-logos/{slug}.svg", "urlPath": f"/cosmos-logos/{slug}.svg",
            "svg": svg.decode("utf-8"), "source": "@thesvg/icons@4.0.16"}


def verify_brand_assets(assets):
    result = {}
    for slug, asset in assets.items():
        content = project_file(asset["path"])
        actual = hashlib.sha256(content).hexdigest()
        if actual != asset["sha256"]:
            raise ValueError(f"Use the exact theSVG bytes for {slug}.")
        result[slug] = actual
    return result


def verify_heroui_source(paths, entry):
    if "package.json" not in paths:
        raise ValueError("Register package.json and all rendered component sources when using HeroUI.")
    dependencies = json.loads(project_file("package.json")).get("dependencies", {})
    if any(dependencies.get(name) != HERO_VERSION for name in ("@heroui/react", "@heroui/styles")):
        raise ValueError(f"Pin the validated @heroui/react and @heroui/styles version {HERO_VERSION}.")
    installed = {}
    try:
        for name in ("react", "styles"):
            installed[name] = json.loads(project_file(f"node_modules/@heroui/{name}/package.json"))["version"]
    except (ValueError, KeyError) as error:
        raise ValueError("Install the pinned HeroUI packages in the project before verification.") from error
    if set(installed.values()) != {HERO_VERSION}:
        raise ValueError("Installed HeroUI versions do not match the declared versions.")
    styles = "\n".join(project_file(path).decode() for path in paths if path.endswith(".css"))
    tailwind = re.search(r'@import\s+["\']tailwindcss["\']', styles)
    hero = re.search(r'@import\s+["\']@heroui/styles["\']', styles)
    if not tailwind or not hero or tailwind.start() > hero.start():
        raise ValueError("Import tailwindcss before @heroui/styles in the registered CSS.")
    files = {path: project_file(path).decode() for path in paths
             if Path(path).suffix in {".js", ".jsx", ".ts", ".tsx", ".mjs"}}
    try:
        run = subprocess.run(
            ["node", str(Path(__file__).with_name("verify-heroui.cjs"))],
            cwd=os.environ["COSMOS_PROJECT_ROOT"], input=json.dumps({"entry": entry, "files": files}),
            capture_output=True, text=True, timeout=12, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("Could not run the HeroUI source verifier. Install Node and @babel/parser.") from error
    if run.returncode:
        raise ValueError(f"HeroUI source check failed: {run.stderr.strip()[:450]}")
    return {"version": HERO_VERSION, "components": json.loads(run.stdout)}
