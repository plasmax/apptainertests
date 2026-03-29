#!/bin/bash
set -euo pipefail

echo "=== Testing stage1-base ==="
apptainer exec stage1-base.sif sh -c 'command -v python3 >/dev/null'
apptainer exec stage1-base.sif sh -c 'command -v gcc >/dev/null'
apptainer exec stage1-base.sif sh -c 'command -v ninja >/dev/null || command -v ninja-build >/dev/null'
echo "=== stage1-base PASSED ==="
