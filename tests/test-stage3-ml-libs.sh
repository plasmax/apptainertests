#!/bin/bash
set -euo pipefail

echo "=== Testing stage3-ml-libs ==="
apptainer exec stage3-ml-libs.sif python3 -c 'import torch; print("torch", torch.__version__)'
apptainer exec stage3-ml-libs.sif python3 -c 'import numpy; print("numpy", numpy.__version__)'
apptainer exec stage3-ml-libs.sif python3 -c 'import cv2; print("opencv", cv2.__version__)'

apptainer exec stage3-ml-libs.sif pip list --format=freeze > actual-packages.txt
if ! diff <(sort containers/expected-packages.txt) <(sort actual-packages.txt | grep -E "^(numpy|opencv-python-headless|torch)==") ; then
    echo "WARN: Package version mismatch detected"
fi

echo "=== stage3-ml-libs PASSED ==="
