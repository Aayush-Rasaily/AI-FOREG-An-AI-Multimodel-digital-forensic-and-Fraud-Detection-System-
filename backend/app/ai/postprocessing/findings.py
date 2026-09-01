"""Convert raw model outputs into normalized structures."""

from __future__ import annotations

from typing import Any

from backend.app.ai.postprocessing.normalization import (
    NormalizedInferenceOutput,
    NormalizedOutputItem,
)


def normalize_raw_output(
    *,
    model_name: str,
    model_version: str,
    framework: str,
    task: str,
    raw_output: Any,
) -> NormalizedInferenceOutput:
    """Map arbitrary model output into the AI-FORGE standard envelope."""

    items: list[NormalizedOutputItem] = []
    metadata: dict[str, Any] = {}
    if isinstance(raw_output, dict):
        metadata = {
            key: value
            for key, value in raw_output.items()
            if key not in {"items", "outputs", "predictions"}
        }
        nested = raw_output.get("items") or raw_output.get("outputs")
        if isinstance(nested, list):
            for index, entry in enumerate(nested):
                if isinstance(entry, dict):
                    items.append(
                        NormalizedOutputItem(
                            name=str(entry.get("name", f"item_{index}")),
                            value=_coerce_value(entry.get("value")),
                            confidence=_coerce_confidence(entry.get("confidence")),
                            metadata={
                                key: value
                                for key, value in entry.items()
                                if key not in {"name", "value", "confidence"}
                            },
                        )
                    )
        for key, value in raw_output.items():
            if key in {"items", "outputs", "predictions"}:
                continue
            if isinstance(value, (str, int, float, bool)):
                items.append(
                    NormalizedOutputItem(
                        name=key,
                        value=value,
                        confidence=None,
                    )
                )
    elif isinstance(raw_output, (str, int, float, bool)):
        items.append(NormalizedOutputItem(name="result", value=raw_output))
    else:
        items.append(
            NormalizedOutputItem(
                name="result",
                value=str(raw_output),
                metadata={"type": type(raw_output).__name__},
            )
        )
    return NormalizedInferenceOutput(
        model_name=model_name,
        model_version=model_version,
        framework=framework,
        task=task,
        items=tuple(items),
        metadata=metadata,
    )


def _coerce_value(value: Any) -> str | float | int | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _coerce_confidence(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None
