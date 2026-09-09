#!/usr/bin/env bash

set -euo pipefail

SIF_PATH="${SIF_PATH:-/net/code/workspaces/mlast/lichtfeld_studio_runtime_test.sif}"
SCRATCH_ROOT="${SCRATCH_ROOT:-/mnt/scratch/mlast}"
LFS_PREFIX="${LFS_PREFIX:-/opt/LichtFeld-Studio/build}"

if [[ ! -f "${SIF_PATH}" ]]; then
    echo "ERROR: SIF not found at ${SIF_PATH}" >&2
    exit 1
fi

if [[ -z "${DISPLAY:-}" ]]; then
    echo "ERROR: DISPLAY is not set." >&2
    exit 1
fi

if [[ ! -e "${HOME}/.Xauthority" ]]; then
    echo "ERROR: ${HOME}/.Xauthority not found." >&2
    exit 1
fi

uid="$(id -u)"

apptainer exec --cleanenv --nv \
  --bind /tmp/.X11-unix:/tmp/.X11-unix \
  --bind "${HOME}/.Xauthority:${HOME}/.Xauthority" \
  --bind "/run/user/${uid}:/run/user/${uid}" \
  --bind "${SCRATCH_ROOT}:${SCRATCH_ROOT}" \
  --env DISPLAY="${DISPLAY}" \
  --env XAUTHORITY="${HOME}/.Xauthority" \
  --env XDG_RUNTIME_DIR="/run/user/${uid}" \
  --env DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${uid}/bus" \
  --env QT_X11_NO_MITSHM=1 \
  --env SDL_VIDEODRIVER=x11 \
  --env LD_LIBRARY_PATH="${LFS_PREFIX}:${LFS_PREFIX}/vcpkg_installed/x64-linux/lib:${LFS_PREFIX}/src/python:${LD_LIBRARY_PATH:-}" \
  "${SIF_PATH}" /usr/local/bin/lichtfeld-studio "$@"
