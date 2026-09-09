/** Client-side chart export helpers (PNG / SVG). No backend involvement. */

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function serializeSvg(svg: SVGSVGElement): string {
  const clone = svg.cloneNode(true) as SVGSVGElement;
  if (!clone.getAttribute("xmlns")) {
    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
  }
  return new XMLSerializer().serializeToString(clone);
}

export function exportSvgAsSvg(svg: SVGSVGElement, filename: string) {
  const payload = serializeSvg(svg);
  downloadBlob(
    new Blob([payload], { type: "image/svg+xml;charset=utf-8" }),
    filename.endsWith(".svg") ? filename : `${filename}.svg`,
  );
}

export async function exportSvgAsPng(
  svg: SVGSVGElement,
  filename: string,
  scale = 2,
): Promise<void> {
  const payload = serializeSvg(svg);
  const blob = new Blob([payload], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  try {
    const image = await loadImage(url);
    const width = Math.max(1, svg.clientWidth || svg.viewBox.baseVal.width || 640);
    const height = Math.max(
      1,
      svg.clientHeight || svg.viewBox.baseVal.height || 320,
    );
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      throw new Error("Canvas unavailable");
    }
    ctx.fillStyle = getComputedStyle(document.documentElement)
      .getPropertyValue("--color-surface")
      .trim() || "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    await new Promise<void>((resolve, reject) => {
      canvas.toBlob((png) => {
        if (!png) {
          reject(new Error("PNG encode failed"));
          return;
        }
        downloadBlob(
          png,
          filename.endsWith(".png") ? filename : `${filename}.png`,
        );
        resolve();
      }, "image/png");
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Failed to rasterize SVG"));
    image.src = url;
  });
}
