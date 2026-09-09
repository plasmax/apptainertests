#!/usr/bin/env bash

set -euo pipefail

APPTAINER_SANDBOX="${APPTAINER_SANDBOX:-/mnt/scratch/mlast/apptainertests/lichtfeld-studio-base-cuda128}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mnt/scratch/mlast}"

export APPTAINER_CACHEDIR="${APPTAINER_CACHEDIR:-${SCRATCH_ROOT}/apptainer-cache}"
export APPTAINER_TMPDIR="${APPTAINER_TMPDIR:-${SCRATCH_ROOT}/apptainer-tmp}"
export TMPDIR="${TMPDIR:-${APPTAINER_TMPDIR}}"

mkdir -p "${APPTAINER_CACHEDIR}" "${APPTAINER_TMPDIR}"

echo "APPTAINER_CACHEDIR=${APPTAINER_CACHEDIR}"
echo "APPTAINER_TMPDIR=${APPTAINER_TMPDIR}"
echo "TMPDIR=${TMPDIR}"
echo "APPTAINER_SANDBOX=${APPTAINER_SANDBOX}"

apptainer build --fakeroot --sandbox "${APPTAINER_SANDBOX}" docker://plasmax7/lichtfeld-studio:latest
apptainer exec --fakeroot --writable "${APPTAINER_SANDBOX}" mkdir -p "${SCRATCH_ROOT}"
apptainer shell --fakeroot --writable --bind "${SCRATCH_ROOT}:${SCRATCH_ROOT}" "${APPTAINER_SANDBOX}"
