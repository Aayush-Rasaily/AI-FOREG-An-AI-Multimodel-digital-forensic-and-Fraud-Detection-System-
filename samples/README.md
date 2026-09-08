# Sample investigation assets (synthetic)

These files are **not** real evidence. They exist so a new user can follow
the [user-guide.md](../docs/user-guide.md) without uploading confidential
material.

Do not hash these files as production exhibits.

## Layout

| Path | Purpose |
| --- | --- |
| `case/sample-case.json` | Example case metadata (illustrative only) |
| `evidence/sample-note.txt` | Plain-text companion (not always in the upload allow-list) |
| `evidence/sample-invoice.pdf` | Minimal synthetic PDF for upload practice |
| `api/examples.md` | curl examples against `/api/v1` |
| `workflow.md` | Suggested demo investigation order |

## Checksums

See `SHA256SUMS` in this directory. Regenerate with:

```bash
uv run python -c "import hashlib, pathlib; p=pathlib.Path('samples');
print('\n'.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.as_posix()}' for f in sorted(p.rglob('*')) if f.is_file() and f.name!='SHA256SUMS'))"
```
