# AGENTS notes for this repo

Keep these guidelines concise and reusable for all build recipes/workflows.

## Apptainer definition files
- In `%post`, assume `/bin/sh` (not bash). Use `set -eu` (avoid `-o pipefail` unless you explicitly run bash).
- Prefer simple, upstream base images when possible; only add minimum packages/tools needed.
- Keep `%test` small but meaningful (basic binary check + critical Python import if applicable).

## GitHub Actions workflows
- Keep the existing disk-space cleanup step; it improves build reliability on hosted runners.
- Add a smoke test step after image build to catch runtime/import issues early.

## Reporting/build-debug info (include this in updates)
- What worked.
- What failed (exact error line/step).
- What changed to fix it.
