#!/usr/bin/env bash
set -euo pipefail

# Usage: SIF_PATH=/path/to/lichtfeld_studio_docker.sif ./run-lichtfeld-studio-apptainer.sh [LichtFeld options]
SIF_PATH="${SIF_PATH:-$(dirname "${BASH_SOURCE[0]}")/lichtfeld_studio_docker.sif}"
XAUTHORITY="${XAUTHORITY:-${HOME}/.Xauthority}"

[[ -f "$SIF_PATH" ]] || { echo "SIF not found: $SIF_PATH" >&2; exit 1; }
[[ -n "${DISPLAY:-}" ]] || { echo "DISPLAY is not set" >&2; exit 1; }
[[ -f "$XAUTHORITY" ]] || { echo "Xauthority file not found: $XAUTHORITY" >&2; exit 1; }

icd=""
for candidate in /usr/share/vulkan/icd.d/nvidia_icd*.json /etc/vulkan/icd.d/nvidia_icd*.json; do
    if [[ -f "$candidate" ]]; then icd="$candidate"; break; fi
done
[[ -n "$icd" ]] || { echo "NVIDIA Vulkan ICD manifest not found on host" >&2; exit 1; }

# --nv exposes the host driver at /.singularity.d/libs. Retain the host's API
# version and other manifest settings, changing only the library location.
tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/lichtfeld-vulkan.XXXXXXXX")"
trap 'rm -rf -- "$tmp_dir"' EXIT
sed -E 's@("library_path"[[:space:]]*:[[:space:]]*")[^"]+("[[:space:]]*[,}])@\1/.singularity.d/libs/libGLX_nvidia.so.0\2@' \
    "$icd" > "$tmp_dir/nvidia_icd.json"
if ! grep -q '/.singularity.d/libs/libGLX_nvidia.so.0' "$tmp_dir/nvidia_icd.json"; then
    echo "Could not adapt NVIDIA ICD manifest: $icd" >&2
    exit 1
fi

args=(--cleanenv --nv
    --bind "$tmp_dir/nvidia_icd.json:/tmp/nvidia_icd.json:ro"
    --bind /tmp/.X11-unix:/tmp/.X11-unix
    --bind "$XAUTHORITY:$XAUTHORITY:ro"
    --env VK_DRIVER_FILES=/tmp/nvidia_icd.json
    --env "DISPLAY=$DISPLAY"
    --env "XAUTHORITY=$XAUTHORITY"
    --env SDL_VIDEODRIVER=x11
    --env QT_X11_NO_MITSHM=1)

for path in /mnt /job /net; do
    [[ -d "$path" ]] && args+=(--bind "$path:$path")
done

runtime_dir="/run/user/$(id -u)"
if [[ -d "$runtime_dir" ]]; then
    args+=(--bind "$runtime_dir:$runtime_dir" --env "XDG_RUNTIME_DIR=$runtime_dir")
    if [[ -S "$runtime_dir/bus" ]]; then
        args+=(--env "DBUS_SESSION_BUS_ADDRESS=unix:path=$runtime_dir/bus")
    fi
fi

apptainer exec "${args[@]}" "$SIF_PATH" /usr/local/bin/lichtfeld-studio "$@"
