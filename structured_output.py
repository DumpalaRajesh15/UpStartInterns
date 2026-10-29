"""
Task 02: Structured Output
A small Python script that parses model JSON, validates its schema and types,
and retries through a repair callback when the output is invalid.

Run:
    python structured_output_validator.py

This demo uses simulated model responses, so it runs without an API key or
third-party packages. Replace model_call() with your model/API call when needed.
"""
import json
from typing import Any, Callable, Dict


class OutputValidationError(ValueError):
    """Raised when model output is invalid or does not match the schema."""


def validate_result(data: Any) -> Dict[str, Any]:
    """Validate the required schema and return typed data."""
    if not isinstance(data, dict):
        raise OutputValidationError("Output must be a JSON object.")

    required = {"title", "priority", "completed", "estimated_hours"}
    missing = required - data.keys()
    extra = data.keys() - required
    if missing:
        raise OutputValidationError(f"Missing fields: {sorted(missing)}")
    if extra:
        raise OutputValidationError(f"Unexpected fields: {sorted(extra)}")

    # Exact type checks matter: in Python, bool is a subclass of int.
    if not isinstance(data["title"], str) or not data["title"].strip():
        raise OutputValidationError("'title' must be a non-empty string.")

    if not isinstance(data["priority"], str) or data["priority"] not in {
        "low", "medium", "high"
    }:
        raise OutputValidationError("'priority' must be low, medium, or high.")

    if type(data["completed"]) is not bool:
        raise OutputValidationError("'completed' must be a boolean.")

    if type(data["estimated_hours"]) not in (int, float):
        raise OutputValidationError("'estimated_hours' must be a number.")
    if data["estimated_hours"] < 0 or data["estimated_hours"] > 100:
        raise OutputValidationError("'estimated_hours' must be between 0 and 100.")

    # Return a fresh object with predictable types and field order.
    return {
        "title": data["title"].strip(),
        "priority": data["priority"],
        "completed": data["completed"],
        "estimated_hours": float(data["estimated_hours"]),
    }


def parse_and_validate(raw_text: str) -> Dict[str, Any]:
    """Parse JSON text and validate its structure and values."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise OutputValidationError(f"Invalid JSON: {exc.msg}") from exc
    return validate_result(data)


def get_valid_output(
    model_call: Callable[[], str],
    repair_call: Callable[[str, str], str],
    max_retries: int = 2,
) -> Dict[str, Any]:
    """
    Try the model, validate its response, then ask a repair function to fix it.
    max_retries is the number of repair attempts after the first response.
    """
    raw = model_call()
    for attempt in range(max_retries + 1):
        try:
            return parse_and_validate(raw)
        except OutputValidationError as exc:
            if attempt == max_retries:
                raise OutputValidationError(
                    f"Output remained invalid after {max_retries} repair attempt(s): {exc}"
                ) from exc
            raw = repair_call(raw, str(exc))
    raise OutputValidationError("Unexpected validation failure.")


# ---- Demo callbacks: no API key needed ----
responses = iter([
    '{"title": "Revise CNN", "priority": "urgent", "completed": "no", "estimated_hours": -2}',
    '{"title": "Revise CNN", "priority": "high", "completed": false, "estimated_hours": 2}'
])


def model_call() -> str:
    """Demo model: first returns invalid data, then a corrected response."""
    return next(responses)


def repair_call(bad_output: str, error_message: str) -> str:
    """Demo repair: in a real app, send both items to the model and request JSON only."""
    print("Validation failed:", error_message)
    print("Repairing invalid output...")
    return next(responses)


if __name__ == "__main__":
    try:
        result = get_valid_output(model_call, repair_call, max_retries=2)
        print("\nVALID OUTPUT")
        print(json.dumps(result, indent=2))
        print("\nAll required fields and types passed validation.")
    except OutputValidationError as exc:
        print("ERROR:", exc)
