#!/bin/bash
set -euo pipefail

STAGES=("stage1-base" "stage2-python" "stage3-ml-libs" "stage4-app")

for stage in "${STAGES[@]}"; do
    def="containers/${stage}.def"
    sif="${stage}.sif"
    sha_file="${stage}.def.sha256"
    current_sha=$(sha256sum "$def" | awk '{print $1}')

    if [ -f "$sha_file" ] && [ -f "$sif" ] && [ "$(cat "$sha_file")" = "$current_sha" ]; then
        echo "SKIP: $stage (unchanged)"
        continue
    fi

    echo "BUILD: $stage"
    apptainer build --fakeroot "$sif" "$def"
    echo "$current_sha" > "$sha_file"

done
