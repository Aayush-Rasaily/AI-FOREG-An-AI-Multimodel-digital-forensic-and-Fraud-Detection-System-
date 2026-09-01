"""Optional Tesseract OCR provider with explicit capability reporting."""

import asyncio
import shutil
from typing import Any

import pytesseract
from pytesseract import Output

from backend.app.extraction.exceptions import ExtractionCapabilityUnavailableError


class TesseractOCRProvider:
    """Use an explicitly installed Tesseract executable when enabled."""

    def __init__(self, enabled: bool, command: str = "tesseract") -> None:
        self._enabled = enabled
        self._command = command
        if command:
            pytesseract.pytesseract.tesseract_cmd = command

    @property
    def enabled(self) -> bool:
        """Return whether OCR was explicitly enabled in configuration."""

        return self._enabled

    @property
    def available(self) -> bool:
        """Return whether the configured executable is discoverable."""

        return bool(self._enabled and shutil.which(self._command))

    async def extract_text(self, image: object) -> str:
        """Extract raw OCR text without normalization."""

        self._ensure_available()
        try:
            return await asyncio.to_thread(pytesseract.image_to_string, image)
        except Exception as exc:
            raise ExtractionCapabilityUnavailableError(
                "OCR_FAILED",
                "The configured OCR provider could not process the image.",
            ) from exc

    async def extract_words(self, image: object) -> list[dict[str, object]]:
        """Extract OCR words with source-image pixel boxes."""

        data = await self._extract_data(image)
        words: list[dict[str, object]] = []
        for index, text in enumerate(data.get("text", [])):
            value = str(text).strip()
            if not value:
                continue
            confidence = self._confidence(data, index)
            words.append(
                {
                    "text": value,
                    "confidence": confidence,
                    "x": self._number(data, "left", index),
                    "y": self._number(data, "top", index),
                    "width": self._number(data, "width", index),
                    "height": self._number(data, "height", index),
                }
            )
        return words

    async def extract_lines(self, image: object) -> list[dict[str, object]]:
        """Extract line boxes by grouping Tesseract word output."""

        data = await self._extract_data(image)
        grouped: dict[tuple[object, ...], dict[str, Any]] = {}
        for index, text in enumerate(data.get("text", [])):
            value = str(text).strip()
            if not value:
                continue
            key = (
                self._value(data, "block_num", index),
                self._value(data, "par_num", index),
                self._value(data, "line_num", index),
            )
            x = self._number(data, "left", index)
            y = self._number(data, "top", index)
            right = x + self._number(data, "width", index)
            bottom = y + self._number(data, "height", index)
            current = grouped.get(key)
            confidence = self._confidence(data, index)
            if current is None:
                grouped[key] = {
                    "text": value,
                    "confidence": confidence,
                    "x": x,
                    "y": y,
                    "right": right,
                    "bottom": bottom,
                    "count": 1,
                }
            else:
                current["text"] = f"{current['text']} {value}"
                current["confidence"] = (float(current["confidence"]) + confidence) / 2
                current["x"] = min(float(current["x"]), x)
                current["y"] = min(float(current["y"]), y)
                current["right"] = max(float(current["right"]), right)
                current["bottom"] = max(float(current["bottom"]), bottom)
                current["count"] = int(current["count"]) + 1

        return [
            {
                "text": str(item["text"]),
                "confidence": float(item["confidence"]),
                "x": float(item["x"]),
                "y": float(item["y"]),
                "width": float(item["right"]) - float(item["x"]),
                "height": float(item["bottom"]) - float(item["y"]),
            }
            for item in grouped.values()
        ]

    async def _extract_data(self, image: object) -> dict[str, list[Any]]:
        """Run bounded provider data extraction in a worker thread."""

        self._ensure_available()
        try:
            return await asyncio.to_thread(
                pytesseract.image_to_data,
                image,
                output_type=Output.DICT,
            )
        except Exception as exc:
            raise ExtractionCapabilityUnavailableError(
                "OCR_FAILED",
                "The configured OCR provider could not process the image.",
            ) from exc

    def _ensure_available(self) -> None:
        if not self.enabled:
            raise ExtractionCapabilityUnavailableError(
                "OCR_DISABLED",
                "OCR is disabled by configuration.",
            )
        if not self.available:
            raise ExtractionCapabilityUnavailableError(
                "OCR_UNAVAILABLE",
                "The configured OCR executable is unavailable.",
            )

    @staticmethod
    def _value(data: dict[str, list[Any]], key: str, index: int) -> object:
        return data.get(key, [None])[index]

    @classmethod
    def _number(cls, data: dict[str, list[Any]], key: str, index: int) -> float:
        value = cls._value(data, key, index)
        try:
            return float(str(value or 0))
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _confidence(cls, data: dict[str, list[Any]], index: int) -> float:
        confidence = cls._number(data, "conf", index)
        return max(0.0, min(1.0, confidence / 100))
