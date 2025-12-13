from __future__ import annotations
from typing import Any, Dict, Optional
from pathlib import Path
import sys
import json
import os

# Ensure project/src is importable
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Provide a small safeguard env var used by app settings
os.environ.setdefault("PEPPER", "openapi-export")

from app.main import create_app  # type: ignore


def export_openapi(output_dir: Optional[Path] = None) -> Path:
    """Load the FastAPI app and export the OpenAPI spec to JSON (and YAML if available).

    Returns the path to the JSON file written.
    """
    if output_dir is None:
        output_dir = HERE.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading FastAPI app...")
    app = create_app()
    print("Generating OpenAPI spec...")
    openapi = app.openapi()

    json_path = output_dir / "openapi.json"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(openapi, fh, indent=2, ensure_ascii=False)

    # Try to write YAML if PyYAML is installed; not required
    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None

    if yaml is not None:
        yaml_path = output_dir / "openapi.yaml"
        try:
            with yaml_path.open("w", encoding="utf-8") as fh:
                yaml.safe_dump(openapi, fh, sort_keys=False)
            print(f"Also wrote YAML: {yaml_path}")
        except Exception:
            print("PyYAML available but writing YAML failed; skipping.")

    print(f"Wrote OpenAPI JSON to: {json_path}")
    return json_path


def main() -> None:
    export_openapi()


if __name__ == "__main__":
    main()

