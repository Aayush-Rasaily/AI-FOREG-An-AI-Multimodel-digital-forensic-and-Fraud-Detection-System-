# GitHub Release — v1.0.0

Publish **after** RC7 certification ([rc7-certification.md](rc7-certification.md)).

## Tag (must match `pyproject.toml`)

```bash
git tag v1.0.0
git push origin v1.0.0
```

Pushing the tag runs `.github/workflows/release.yml`: CI, GitHub Release notes
from CHANGELOG.md, and GHCR images (`ai-forge-api`, `ai-forge-api-worker`,
`ai-forge-frontend`) tagged `1.0.0`, `latest`, and the git SHA.

## Manual `gh` (if the tag already exists)

```bash
gh release create v1.0.0 \
  --title "AI-Forge 1.0.0" \
  --notes-file RELEASE_NOTES.md \
  CHANGELOG.md ROADMAP.md LICENSE
```

## Title

`AI-Forge 1.0.0`

## Notes

Use [RELEASE_NOTES.md](../RELEASE_NOTES.md).
