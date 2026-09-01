"""Copy-move forgery detector using keypoint matching."""

import asyncio

import cv2
import numpy as np

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    RegionBox,
    Severity,
)
from backend.app.forensics.utils import (
    encode_png,
    load_image_from_storage,
    region_from_pixels,
)


class CopyMoveDetector:
    """Detect duplicated regions via ORB keypoint clustering."""

    name = "copy_move"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        return context.classification == EvidenceClassification.IMAGE

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        rgb, width, height = await load_image_from_storage(
            context.storage,
            context.storage_key,
            max_bytes=max_bytes,
        )
        regions, overlay, match_count = await asyncio.to_thread(
            _detect_copy_move,
            rgb,
            width,
            height,
        )
        findings: tuple[FindingItem, ...] = ()
        artifacts: tuple[DerivedArtifactPayload, ...] = ()
        if match_count >= 1 and regions:
            confidence = min(0.95, 0.5 + match_count / 40.0)
            findings = (
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.COPY_MOVE,
                    severity=Severity.HIGH if match_count >= 8 else Severity.MEDIUM,
                    confidence=confidence,
                    description="Duplicated image regions detected.",
                    explanation=(
                        f"Descriptor matching identified {match_count} "
                        "spatially separated correspondences."
                    ),
                    regions=regions,
                    metadata={"match_count": match_count},
                    recommendation=(
                        "Inspect matched bounding boxes for duplicated content."
                    ),
                ),
            )
            if overlay is not None:
                artifacts = (
                    DerivedArtifactPayload(
                        artifact_type=ArtifactType.FORENSIC_OVERLAY,
                        mime_type="image/png",
                        content=encode_png(overlay),
                        metadata={"detector": self.name, "match_count": match_count},
                    ),
                )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=findings,
            artifacts=artifacts,
            metadata={"match_count": match_count},
        )


def _detect_copy_move(
    rgb: np.ndarray,
    width: int,
    height: int,
) -> tuple[tuple[RegionBox, ...], np.ndarray | None, int]:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    orb_matches, orb_regions, orb_overlay = _orb_copy_move(gray, width, height, rgb)
    if orb_matches >= 8:
        return orb_regions, orb_overlay, orb_matches
    block_matches, block_regions, block_overlay = _block_copy_move(
        gray,
        width,
        height,
        rgb,
    )
    if block_matches >= 1:
        return block_regions, block_overlay, block_matches
    return (), None, 0


def _orb_copy_move(
    gray: np.ndarray,
    width: int,
    height: int,
    rgb: np.ndarray,
) -> tuple[int, tuple[RegionBox, ...], np.ndarray | None]:
    orb = cv2.ORB_create(  # type: ignore[attr-defined]
        nfeatures=1000,
        scoreType=cv2.ORB_HARRIS_SCORE,
    )
    keypoints, descriptors = orb.detectAndCompute(gray, None)
    if descriptors is None or len(keypoints) < 10:
        return 0, (), None
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors, descriptors)
    valid: list[tuple[cv2.KeyPoint, cv2.KeyPoint]] = []
    min_distance = max(width, height) * 0.05
    for match in matches:
        if match.queryIdx == match.trainIdx:
            continue
        kp1 = keypoints[match.queryIdx]
        kp2 = keypoints[match.trainIdx]
        dist = np.hypot(kp1.pt[0] - kp2.pt[0], kp1.pt[1] - kp2.pt[1])
        if dist >= min_distance and match.distance <= 50:
            valid.append((kp1, kp2))
    if len(valid) < 8:
        return len(valid), (), None
    overlay = rgb.copy()
    regions: list[RegionBox] = []
    for kp1, kp2 in valid[:20]:
        for kp in (kp1, kp2):
            size = 24.0
            x = max(0.0, kp.pt[0] - size / 2)
            y = max(0.0, kp.pt[1] - size / 2)
            regions.append(region_from_pixels(x, y, size, size, width, height))
            cv2.rectangle(
                overlay,
                (int(x), int(y)),
                (int(x + size), int(y + size)),
                (255, 64, 64),
                2,
            )
    return len(valid), tuple(regions[:10]), overlay


def _block_copy_move(
    gray: np.ndarray,
    width: int,
    height: int,
    rgb: np.ndarray,
) -> tuple[int, tuple[RegionBox, ...], np.ndarray | None]:
    block = 32
    stride = 16
    h, w = gray.shape
    blocks: list[tuple[int, int, np.ndarray]] = []
    for y in range(0, max(1, h - block), stride):
        for x in range(0, max(1, w - block), stride):
            patch = gray[y : y + block, x : x + block]
            if patch.shape[0] == block and patch.shape[1] == block:
                blocks.append((x, y, patch))
    matches: list[tuple[int, int, int, int]] = []
    for index, (x1, y1, patch1) in enumerate(blocks):
        for x2, y2, patch2 in blocks[index + 1 :]:
            if np.hypot(x1 - x2, y1 - y2) < block * 1.5:
                continue
            if (
                float(
                    np.mean(np.abs(patch1.astype(np.int16) - patch2.astype(np.int16)))
                )
                <= 4.0
            ):
                matches.append((x1, y1, x2, y2))
    if not matches:
        return 0, (), None
    overlay = rgb.copy()
    regions: list[RegionBox] = []
    for x1, y1, x2, y2 in matches[:10]:
        for x, y in ((x1, y1), (x2, y2)):
            regions.append(
                region_from_pixels(
                    float(x), float(y), float(block), float(block), width, height
                )
            )
            cv2.rectangle(
                overlay,
                (x, y),
                (x + block, y + block),
                (255, 64, 64),
                2,
            )
    return len(matches), tuple(regions), overlay
