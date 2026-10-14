"""R12 Stage 0: fail-closed state reader and allowlisted offline site packaging.

This module performs local validation/copying only. It cannot publish, access
Amazon accounts, or deploy. Release wiring requires separate founder approval.
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = frozenset({
    "index.html", "404.html", "compare.html", "live-picks.html",
    "app.js", "click-telemetry.js", "telemetry.js", "styles.css",
    "robots.txt", "sitemap.xml",
})
PUBLIC_DIRS = frozenset({"articles", "blog", "guides", "legal", "products", "social"})
PUBLIC_EXTENSIONS = frozenset({".html", ".css", ".js", ".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico"})
MAX_FILE_BYTES = 12 * 1024 * 1024


def production_state(config_path):
    """Missing, invalid or unreadable production controls always mean STOPPED."""
    try:
        with Path(config_path).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if type(payload) is not dict:
            return "STOPPED"
        state = payload.get("production_state")
        return state if state in ("ACTIVE", "STOPPED", "PARKED") else "STOPPED"
    except (OSError, UnicodeError, ValueError, TypeError):
        return "STOPPED"


def release_eligible(config_path, *, founder_approved=False, environment_verified=False):
    """Defense in depth only; no deployment is connected to this function."""
    return (production_state(config_path) == "ACTIVE"
            and founder_approved is True and environment_verified is True)


def is_public_path(relative_path):
    rel = Path(relative_path)
    parts = rel.parts
    if not parts or any(part in ("", ".", "..") or part.startswith(".") for part in parts):
        return False
    if len(parts) == 1:
        return parts[0] in PUBLIC_FILES
    return (parts[0] in PUBLIC_DIRS and rel.suffix.lower() in PUBLIC_EXTENSIONS
            and not any(part in (".git", ".github", "__pycache__") for part in parts))


def verify_package(output):
    output = Path(output)
    if output.is_symlink() or not output.is_dir() or not (output / "index.html").is_file():
        raise ValueError("Public output missing/invalid index.html")
    count = 0
    for item in output.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlinks forbidden in public output")
        if item.is_file():
            if not is_public_path(item.relative_to(output)):
                raise ValueError("Non-public file in output: " + str(item.relative_to(output)))
            if item.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("Oversized public file")
            count += 1
    if not count:
        raise ValueError("Empty public output")
    return count


def build_public_site(source, output):
    """Copy explicitly public files only. Never upload an entire repository."""
    source, output = Path(source), Path(output)
    if source.is_symlink() or not source.is_dir() or not (source / "index.html").is_file():
        raise ValueError("Invalid public source")
    src_real, dst_real = source.resolve(), output.resolve()
    if src_real == dst_real or src_real in dst_real.parents or dst_real in src_real.parents:
        raise ValueError("Source/output must not overlap")
    if output.is_symlink() or (output.exists() and any(output.iterdir())):
        raise ValueError("Output must be an empty, non-symlink directory")
    planned = []
    for item in source.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlinks forbidden in public source")
        if item.is_file():
            rel = item.relative_to(source)
            if is_public_path(rel):
                if item.stat().st_size > MAX_FILE_BYTES:
                    raise ValueError("Oversized public file")
                planned.append((item, rel))
    if not any(str(rel) == "index.html" for _, rel in planned):
        raise ValueError("Missing allowlisted index.html")
    output.mkdir(parents=True, exist_ok=True)
    for item, rel in planned:
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)
    return verify_package(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(ROOT / "site"))
    parser.add_argument("--output", default=str(ROOT / "_public"))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    count = verify_package(args.output) if args.verify_only else build_public_site(args.source, args.output)
    print("R12 Stage 0 offline public package validated:", count, "files; NO DEPLOYMENT")
