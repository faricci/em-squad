"""
validator.py — C-DAD runtime validator for em-squad agents.

Pre-run:  verifies all context_sources declared in the contract exist on disk.
Post-run: verifies the output shape matches the contract's output_schema keys.

Raises ContractViolationError on hard failures.
"""

import warnings
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent.parent


class ContractViolationError(Exception):
    """Raised when a C-DAD contract constraint is violated at runtime."""


@dataclass
class ValidationResult:
    passed: bool
    errors: list


def validate_lifecycle(contract_path: str) -> None:
    """
    Block execution if lifecycle=draft or retired. Warn if deprecated.
    Raises ContractViolationError on hard failures.
    """
    import sys
    contract = _load_contract(contract_path)
    lifecycle = contract.get("lifecycle", "active")

    if lifecycle == "draft":
        raise ContractViolationError(
            f"[{contract_path}] lifecycle=draft — not ready for production."
        )
    elif lifecycle == "deprecated":
        print(f"Warning: [{contract_path}] is deprecated. Consider upgrading.", file=sys.stderr)
    elif lifecycle == "retired":
        raise ContractViolationError(
            f"[{contract_path}] lifecycle=retired — agent is no longer operational."
        )
    # active: pass through


def validate_pre_run(contract_path: str) -> ValidationResult:
    """
    Verify that all context_sources declared in the contract exist on disk.
    Raises ContractViolationError if any source is missing.
    """
    contract = _load_contract(contract_path)
    sources = contract.get("context_sources", [])

    errors = []
    for source in sources:
        # Strip inline comments (e.g. "context/file.md  # description")
        clean = source.split("#")[0].strip()
        if not clean:
            continue
        if not (ROOT / clean).exists():
            errors.append(f"Missing context source: {clean}")

    if errors:
        raise ContractViolationError(
            f"Contract pre-run validation failed for '{contract_path}':\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    return ValidationResult(passed=True, errors=[])


def validate_post_run(contract_path: str, output: dict) -> ValidationResult:
    """
    Verify that the output contains the keys declared in output_schema.
    Logs warnings for missing fields — no hard fail in Phase 2.
    """
    contract = _load_contract(contract_path)
    schema_keys = set(contract.get("output_schema", {}).keys())
    output_keys = set(output.keys())

    missing = schema_keys - output_keys
    errors = [f"Output missing schema key: {k}" for k in sorted(missing)]

    if errors:
        for e in errors:
            warnings.warn(f"[C-DAD post-run] {e}", stacklevel=3)

    return ValidationResult(passed=not errors, errors=errors)


def _load_contract(contract_path: str) -> dict:
    full_path = ROOT / contract_path
    if not full_path.exists():
        raise ContractViolationError(f"Contract file not found: {contract_path}")
    data = yaml.safe_load(full_path.read_text(encoding="utf-8"))
    return data.get("contract", data)
