#!/bin/bash
set -euo pipefail

echo "=== Testing stage2-python ==="
apptainer exec stage2-python.sif python3 -c 'import numpy; print("numpy", numpy.__version__)'
apptainer exec stage2-python.sif sh -c 'python3 -m pip --version >/dev/null'
echo "=== stage2-python PASSED ==="
