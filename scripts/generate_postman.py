from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys
import json
import os
import time

# Ensure a PEPPER is available for pydantic Settings() during import.
# If the user has a proper `.env` or environment, this will be a no-op.
os.environ.setdefault("PEPPER", "postman-temp")

from pydantic import BaseModel, Field

# Ensure project/src is on sys.path so we can import the app package
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app.main import create_app  # type: ignore


class Info(BaseModel):
    name: str
    schema: str = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"


class Header(BaseModel):
    key: str
    value: str


class Body(BaseModel):
    mode: str
    raw: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class Url(BaseModel):
    raw: str


class RequestModel(BaseModel):
    method: str
    header: List[Header] = Field(default_factory=list)
    body: Optional[Body] = None
    url: Url


class Item(BaseModel):
    name: str
    request: RequestModel
    response: List[Any] = Field(default_factory=list)


class PostmanCollection(BaseModel):
    info: Info
    item: List[Item] = Field(default_factory=list)


def schema_example_from_schema(schema: Dict[str, Any]) -> Optional[str]:
    """Try to build a small JSON example from an OpenAPI schema object.
    This is intentionally conservative: we only create simple examples for
    object/array/primitive types and prefer explicit examples if provided.
    """
    if not schema:
        return None
    if "example" in schema:
        try:
            return json.dumps(schema["example"], indent=2)
        except Exception:
            return str(schema["example"])
    t = schema.get("type")
    if t == "object":
        props = schema.get("properties", {})
        example = {}
        for k, v in props.items():
            ex = schema_example_from_schema(v)
            if ex is None:
                # provide a reasonable placeholder based on type
                ptype = v.get("type")
                if ptype == "string":
                    example[k] = "string"
                elif ptype == "integer":
                    example[k] = 0
                elif ptype == "number":
                    example[k] = 0.0
                elif ptype == "boolean":
                    example[k] = False
                elif ptype == "array":
                    example[k] = []
                else:
                    example[k] = None
            else:
                try:
                    example[k] = json.loads(ex)
                except Exception:
                    example[k] = ex
        return json.dumps(example, indent=2)
    if t == "array":
        items = schema.get("items", {})
        ex = schema_example_from_schema(items)
        if ex is None:
            return json.dumps([])
        try:
            return json.dumps([json.loads(ex)], indent=2)
        except Exception:
            return json.dumps([ex])
    if t == "string":
        return json.dumps("string")
    if t == "integer":
        return json.dumps(0)
    if t == "number":
        return json.dumps(0.0)
    if t == "boolean":
        return json.dumps(False)
    return None


def openapi_to_postman(openapi: Dict[str, Any], collection_name: str = "Generated API Collection", verbose: bool = True) -> PostmanCollection:
    """Convert OpenAPI spec dict to a PostmanCollection pydantic model.

    If verbose is True, prints progress information while iterating endpoints.
    """
    servers = openapi.get("servers", [])
    base_url = servers[0]["url"] if servers else "http://localhost"

    # Pre-calc total operations for progress reporting
    paths = openapi.get("paths", {})
    total_ops = 0
    for path_item in paths.values():
        for method in path_item.keys():
            if method.lower() in {"get", "post", "put", "delete", "patch", "options", "head"}:
                total_ops += 1

    if verbose:
        print(f"Found {len(paths)} paths and {total_ops} HTTP operations to process.")

    items: List[Item] = []

    start_time = time.time()
    processed = 0

    for path, path_item in paths.items():
        for method, op in path_item.items():
            # skip non-HTTP methods if present
            if method.lower() not in {"get", "post", "put", "delete", "patch", "options", "head"}:
                continue

            processed += 1
            # progress reporting every operation
            if verbose:
                elapsed = time.time() - start_time
                avg = elapsed / processed if processed else 0
                remaining = total_ops - processed
                eta = remaining * avg
                op_name = op.get("operationId") or op.get("summary") or ""
                print(f"Processing {processed}/{total_ops}: {method.upper()} {path} {('- '+op_name) if op_name else ''} — elapsed={elapsed:.1f}s avg={avg:.2f}s ETA={eta:.1f}s", flush=True)

            name = op.get("summary") or op.get("operationId") or f"{method.upper()} {path}"
            url_raw = base_url.rstrip("/") + path

            headers: List[Header] = []
            body_model: Optional[Body] = None

            request_body = op.get("requestBody") or {}
            content = request_body.get("content", {})
            app_json = content.get("application/json")
            if app_json:
                schema = app_json.get("schema") or {}
                example_raw = None
                # prefer explicit example
                if "example" in app_json:
                    try:
                        example_raw = json.dumps(app_json["example"], indent=2)
                    except Exception:
                        example_raw = str(app_json["example"])
                # or look into schema examples
                if not example_raw and schema:
                    example_raw = schema_example_from_schema(schema)
                if example_raw:
                    body_model = Body(mode="raw", raw=example_raw)
                    headers.append(Header(key="Content-Type", value="application/json"))

            request = RequestModel(method=method.upper(), header=headers, body=body_model, url=Url(raw=url_raw))
            items.append(Item(name=name, request=request))

    collection = PostmanCollection(info=Info(name=collection_name), item=items)
    if verbose:
        total_elapsed = time.time() - start_time
        print(f"Completed conversion: {len(items)} items in {total_elapsed:.1f}s")
    return collection


def main(output_path: Optional[Path] = None) -> None:
    """Load the FastAPI app, generate an OpenAPI spec, convert it to Postman
    collection format and write it to a JSON file.
    """
    print("Loading FastAPI app...")
    app = create_app()
    print("Generating OpenAPI spec (this can take a while)...", flush=True)
    openapi = app.openapi()
    print("OpenAPI spec generated.")

    collection = openapi_to_postman(openapi, collection_name=app.title or "API", verbose=True)

    if output_path is None:
        output_path = HERE.parent / "postman_collection.json"

    with output_path.open("w", encoding="utf-8") as fh:
        # Pydantic v2: use model_dump() + json.dump or model_dump_json()
        json.dump(collection.model_dump(), fh, indent=2)

    print(f"Wrote Postman collection to: {output_path}")


if __name__ == "__main__":
    main()
