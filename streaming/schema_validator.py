import json
from pathlib import Path


SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
RAW_SCHEMA_PATH = SCHEMA_DIR / "transaction_raw_schema.json"
SCORED_SCHEMA_PATH = SCHEMA_DIR / "transaction_scored_schema.json"


TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "object": dict,
    "array": list,
}


class SchemaValidationError(ValueError):
    pass


def load_schema(path):
    with path.open("r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def validate_value(value, property_schema, path):
    expected_type = property_schema.get("type")

    if expected_type:
        expected_python_type = TYPE_MAP.get(expected_type)
        if expected_python_type and not isinstance(value, expected_python_type):
            raise SchemaValidationError(
                f"{path} expected {expected_type}, got {type(value).__name__}"
            )

    if expected_type == "object":
        validate_event(value, property_schema, path_prefix=path)


def validate_event(event, schema, path_prefix="event"):
    if not isinstance(event, dict):
        raise SchemaValidationError(f"{path_prefix} must be an object")

    missing = [
        field
        for field in schema.get("required", [])
        if field not in event or event[field] is None
    ]
    if missing:
        raise SchemaValidationError(f"{path_prefix} missing required fields: {', '.join(missing)}")

    for field, property_schema in schema.get("properties", {}).items():
        if field in event and event[field] is not None:
            validate_value(event[field], property_schema, f"{path_prefix}.{field}")

    return True


def validate_raw_event(event):
    return validate_event(event, load_schema(RAW_SCHEMA_PATH))


def validate_scored_event(event):
    return validate_event(event, load_schema(SCORED_SCHEMA_PATH))
