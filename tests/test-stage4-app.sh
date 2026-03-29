#!/bin/bash
set -euo pipefail

echo "=== Testing stage4-app ==="
apptainer exec stage4-app.sif sh -c 'test -x /usr/local/bin/lichtfeld-studio'
apptainer exec stage4-app.sif sh -c 'ldd /usr/local/bin/lichtfeld-studio >/dev/null'
echo "=== stage4-app PASSED ==="
