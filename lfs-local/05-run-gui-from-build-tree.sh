#!/usr/bin/env bash

set -euo pipefail

APPTAINER_SANDBOX="${APPTAINER_SANDBOX:-/mnt/scratch/mlast/apptainertests/lichtfeld-studio-base-cuda128}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mnt/scratch/mlast}"
LFS_BUILD_ROOT="${LFS_BUILD_ROOT:-${SCRATCH_ROOT}/lichtfeld-build/LichtFeld-Studio/build}"

if [[ -z "${DISPLAY:-}" ]]; then
    echo "ERROR: DISPLAY is not set." >&2
    exit 1
fi

if [[ ! -e "${HOME}/.Xauthority" ]]; then
    echo "ERROR: ${HOME}/.Xauthority not found." >&2
    exit 1
fi

if [[ ! -x "${LFS_BUILD_ROOT}/LichtFeld-Studio" ]]; then
    echo "ERROR: built executable not found at ${LFS_BUILD_ROOT}/LichtFeld-Studio" >&2
    exit 1
fi

uid="$(id -u)"

apptainer exec --cleanenv --nv \
  --bind /tmp/.X11-unix:/tmp/.X11-unix \
  --bind "${HOME}/.Xauthority:${HOME}/.Xauthority" \
  --bind "${SCRATCH_ROOT}:${SCRATCH_ROOT}" \
  --bind "/run/user/${uid}:/run/user/${uid}" \
  --env DISPLAY="${DISPLAY}" \
  --env XAUTHORITY="${HOME}/.Xauthority" \
  --env XDG_RUNTIME_DIR="/run/user/${uid}" \
  --env DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
  "${APPTAINER_SANDBOX}" \
  "${LFS_BUILD_ROOT}/LichtFeld-Studio" "$@"
