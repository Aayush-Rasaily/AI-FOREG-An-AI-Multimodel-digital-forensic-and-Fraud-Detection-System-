# Example investigation workflow (demo)

1. Sign in (`/login`).
2. Create a case using `samples/case/sample-case.json` as a title/description hint.
3. Upload `samples/evidence/sample-invoice.pdf` (synthetic PDF).
4. Process → extract (OCR may be `unavailable` if Tesseract is not installed).
5. Run forensic/document analysis as permitted by your role.
6. Run fusion only after stored findings exist.
7. Generate a report and download it.
8. Export only if you hold `interop.export`.

AI outputs assist investigators; they do not replace professional judgment.
See [forensic-methodology.md](../docs/forensic-methodology.md).
