"""Project paths. Everything is resolved from the repository root."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINALS = ROOT / "Al-Oose-content" / "CONTENT" / "BBTB MARKETING"
LIBRARY = ROOT / "library"
DERIVED = LIBRARY / "derived"
CHARACTERS = LIBRARY / "characters"
ASSETS_YAML = LIBRARY / "assets.yaml"
ASSET_NOTES_YAML = LIBRARY / "asset_notes.yaml"
PRODUCTIONS = ROOT / "productions"
ENV_FILE = ROOT / ".env"


def rel(path: Path) -> str:
    """Path relative to the repo root, as stored in YAML files."""
    return str(Path(path).resolve().relative_to(ROOT))
