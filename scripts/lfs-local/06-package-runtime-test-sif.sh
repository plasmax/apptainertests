#!/usr/bin/env bash

set -euo pipefail

APPTAINER_SANDBOX="${APPTAINER_SANDBOX:-/mnt/scratch/mlast/apptainertests/lichtfeld-studio-base-cuda128}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mnt/scratch/mlast}"
LFS_SRC_TREE="${LFS_SRC_TREE:-${SCRATCH_ROOT}/lichtfeld-build/LichtFeld-Studio}"
OUT_SIF="${OUT_SIF:-${SCRATCH_ROOT}/lichtfeld_studio_runtime_test.sif}"

if [[ ! -d "${APPTAINER_SANDBOX}" ]]; then
    echo "ERROR: sandbox not found at ${APPTAINER_SANDBOX}" >&2
    exit 1
fi

if [[ ! -x "${LFS_SRC_TREE}/build/LichtFeld-Studio" ]]; then
    echo "ERROR: built executable not found at ${LFS_SRC_TREE}/build/LichtFeld-Studio" >&2
    exit 1
fi

mkdir -p "${APPTAINER_SANDBOX}/opt" "${APPTAINER_SANDBOX}/usr/local/bin"
rm -rf "${APPTAINER_SANDBOX}/opt/LichtFeld-Studio"
cp -a "${LFS_SRC_TREE}" "${APPTAINER_SANDBOX}/opt/LichtFeld-Studio"

# The runtime looks under build/resources first, but the generated RmlUI files
# currently land under build/src/visualizer/resources. Merge them into the
# runtime-visible tree so the packaged SIF is self-contained.
if [[ -d "${APPTAINER_SANDBOX}/opt/LichtFeld-Studio/build/src/visualizer/resources" ]]; then
    mkdir -p "${APPTAINER_SANDBOX}/opt/LichtFeld-Studio/build/resources"
    cp -a \
      "${APPTAINER_SANDBOX}/opt/LichtFeld-Studio/build/src/visualizer/resources/." \
      "${APPTAINER_SANDBOX}/opt/LichtFeld-Studio/build/resources/"
fi

ln -sf /opt/LichtFeld-Studio/build/LichtFeld-Studio "${APPTAINER_SANDBOX}/usr/local/bin/lichtfeld-studio"

echo "Packaging ${OUT_SIF} from ${APPTAINER_SANDBOX}"
apptainer build --fakeroot "${OUT_SIF}" "${APPTAINER_SANDBOX}"
