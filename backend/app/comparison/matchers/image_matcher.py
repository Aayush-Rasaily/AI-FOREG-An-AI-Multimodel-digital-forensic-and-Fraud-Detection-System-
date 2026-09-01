"""Image comparison matcher using SSIM, ORB, and AKAZE."""

import asyncio

import cv2
import numpy as np

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.comparison.models import (
    ComparisonContext,
    DifferenceItem,
    DifferenceSeverity,
    DifferenceType,
    MatcherResult,
    RegionBox,
)
from backend.app.comparison.utils import (
    compute_ssim,
    difference_mask,
    encode_png,
    load_image_from_storage,
)
from backend.app.domain.processing import ArtifactType, EvidenceClassification


class ImageMatcher:
    """Compare images with alignment, SSIM, ORB, AKAZE, and difference masks."""

    name = "image"
    version = "1.0"

    def can_compare(self, context: ComparisonContext) -> bool:
        return (
            context.questioned_classification == EvidenceClassification.IMAGE
            and context.reference_classification == EvidenceClassification.IMAGE
        )

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        ref_rgb, ref_w, ref_h = await load_image_from_storage(
            context.storage,
            context.reference_storage_key,
            max_bytes=max_bytes,
        )
        q_rgb, q_w, q_h = await load_image_from_storage(
            context.storage,
            context.questioned_storage_key,
            max_bytes=max_bytes,
        )
        result = await asyncio.to_thread(
            _compare_images,
            ref_rgb,
            q_rgb,
            ref_w,
            ref_h,
            q_w,
            q_h,
        )
        differences, mask, overlay, metadata = result
        artifacts: tuple[DerivedArtifactPayload, ...] = ()
        if mask is not None:
            artifacts = (
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.COMPARISON_MASK,
                    mime_type="image/png",
                    content=encode_png(mask),
                    metadata={"matcher": self.name},
                ),
            )
        if overlay is not None:
            artifacts = (
                *artifacts,
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.COMPARISON_OVERLAY,
                    mime_type="image/png",
                    content=encode_png(overlay),
                    metadata={"matcher": self.name},
                ),
            )
        return MatcherResult(
            matcher=self.name,
            version=self.version,
            differences=tuple(differences),
            artifacts=artifacts,
            metadata=metadata,
        )


def _compare_images(
    ref_rgb: np.ndarray,
    q_rgb: np.ndarray,
    ref_w: int,
    ref_h: int,
    q_w: int,
    q_h: int,
) -> tuple[
    list[DifferenceItem],
    np.ndarray | None,
    np.ndarray | None,
    dict[str, float],
]:
    ref_gray = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2GRAY)
    q_gray = cv2.cvtColor(q_rgb, cv2.COLOR_RGB2GRAY)
    aligned_q = _align_orb(ref_gray, q_gray)
    ssim_score = compute_ssim(ref_gray, aligned_q)
    mask = difference_mask(ref_rgb, cv2.cvtColor(aligned_q, cv2.COLOR_GRAY2RGB))
    overlay = ref_rgb.copy()
    overlay[mask > 0] = (255, 64, 64)
    differences: list[DifferenceItem] = []
    metadata: dict[str, float] = {"ssim": round(ssim_score, 4)}
    if ssim_score < 0.98:
        severity = (
            DifferenceSeverity.HIGH if ssim_score < 0.85 else DifferenceSeverity.MEDIUM
        )
        differences.append(
            DifferenceItem(
                matcher="image",
                difference_type=DifferenceType.IMAGE_CHANGED,
                severity=severity,
                confidence=min(0.95, 1.0 - ssim_score + 0.15),
                description="Image structural similarity differs from reference.",
                explanation=f"SSIM score {ssim_score:.3f} indicates visual changes.",
                metadata={"ssim": round(ssim_score, 4)},
                regions=_mask_regions(mask, ref_w, ref_h),
            )
        )
    orb_detector = cv2.ORB_create(500)  # type: ignore[attr-defined]
    orb_matches = _feature_match_count(ref_gray, aligned_q, orb_detector)
    akaze_detector = _akaze_detector()
    akaze_matches = (
        _feature_match_count(ref_gray, aligned_q, akaze_detector)
        if akaze_detector is not None
        else orb_matches
    )
    metadata["orb_matches"] = float(orb_matches)
    metadata["akaze_matches"] = float(akaze_matches)
    if orb_matches < 20 and ssim_score < 0.95:
        differences.append(
            DifferenceItem(
                matcher="image",
                difference_type=DifferenceType.LOGO_CHANGED,
                severity=DifferenceSeverity.MEDIUM,
                confidence=0.8,
                description=(
                    "Feature correspondence suggests logo or region replacement."
                ),
                explanation=(
                    f"ORB matches={orb_matches}, AKAZE matches={akaze_matches} "
                    "after alignment."
                ),
                metadata={"orb_matches": orb_matches, "akaze_matches": akaze_matches},
                regions=_mask_regions(mask, ref_w, ref_h)[:3],
            )
        )
    return differences, mask, overlay, metadata


def _akaze_detector() -> cv2.Feature2D | None:
    """Return AKAZE when the OpenCV build exposes it."""

    if hasattr(cv2, "AKAZE_create"):
        return cv2.AKAZE_create()
    akaze_type = getattr(cv2, "AKAZE", None)
    if akaze_type is not None and hasattr(akaze_type, "create"):
        return akaze_type.create()
    return None


def _align_orb(reference: np.ndarray, questioned: np.ndarray) -> np.ndarray:
    orb = cv2.ORB_create(500)  # type: ignore[attr-defined]
    kp1, des1 = orb.detectAndCompute(reference, None)
    kp2, des2 = orb.detectAndCompute(questioned, None)
    if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
        height = min(reference.shape[0], questioned.shape[0])
        width = min(reference.shape[1], questioned.shape[1])
        resized = cv2.resize(questioned, (width, height))
        canvas = np.zeros_like(reference)
        canvas[:height, :width] = resized
        return canvas
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    if len(matches) < 4:
        return questioned
    src_points = [kp1[m.queryIdx].pt for m in matches[:20]]
    dst_points = [kp2[m.trainIdx].pt for m in matches[:20]]
    src = np.array(src_points, dtype=np.float32).reshape(-1, 1, 2)
    dst = np.array(dst_points, dtype=np.float32).reshape(-1, 1, 2)
    matrix, _ = cv2.findHomography(dst, src, cv2.RANSAC, 5.0)
    if matrix is None:
        return questioned
    return cv2.warpPerspective(
        questioned,
        matrix,
        (reference.shape[1], reference.shape[0]),
    )


def _feature_match_count(
    reference: np.ndarray,
    questioned: np.ndarray,
    detector: cv2.Feature2D,
) -> int:
    kp1, des1 = detector.detectAndCompute(reference, None)
    kp2, des2 = detector.detectAndCompute(questioned, None)
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    return len(bf.match(des1, des2))


def _mask_regions(
    mask: np.ndarray,
    width: int,
    height: int,
) -> tuple[RegionBox, ...]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return ()
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return (
        RegionBox(
            x=float(x0),
            y=float(y0),
            width=float(x1 - x0 + 1),
            height=float(y1 - y0 + 1),
            normalized=RegionBox(
                x=x0 / width,
                y=y0 / height,
                width=(x1 - x0 + 1) / width,
                height=(y1 - y0 + 1) / height,
            ),
        ),
    )
