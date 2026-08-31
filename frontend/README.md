# AI-FORGE Frontend

Phase 3 connects the investigation workspace to the case and evidence
registry. It preserves upload metadata and displays server-calculated hashes;
it contains no forensic processing, AI models, OCR, or fabricated records.

## Development

```bash
npm install
npm run dev
```

The API base URL is configured with `VITE_API_BASE_URL`. When unset, the
frontend uses the relative `/api/v1` path and Vite proxies `/api` to the
backend development server. Set `VITE_BACKEND_URL` when the backend is not
running at the local proxy default.

## Quality checks

```bash
npm run build
npm run lint
npm run test
```
