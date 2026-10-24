# CorridorKey 2.0 Apptainer

Self-contained Linux x86_64 runtime: source, vendored MoGe code, Python 3.11,
PyTorch 2.9.1 / torchvision 0.24.1 (CUDA 12.8), all upstream Python requirements,
FFmpeg, and OpenCV EXR support. **No model weights are included in the SIF.**

Source is pinned to [485f5e9](https://github.com/nikopueringer/CorridorKey2.0/tree/485f5e9ab759ead6138cc990776184b59d6ea971).
The upstream license and third-party notices remain in `/opt/CorridorKey`.
Python dependencies follow upstream ranges except NumPy 1.26.4 and OpenCV
4.11.0.86, pinned to avoid the NumPy 2 requirement in newer OpenCV wheels.
Each build exports its actual installed package versions alongside the image.

## Build / download the image

Run **Actions → CorridorKey 2.0 (GPU) → Run workflow**. Download and extract the
`corridorkey2-sif` artifact. It contains the image, SHA-256 checksum, and installed
package manifest. Builds are manual, consistent with the other recipes here.

Or build locally, from this repository's root:

```sh
sudo apptainer build corridorkey2.sif definitions/corridorkey2.def
```

## Download all models once

On an internet-connected Linux machine with Apptainer (no GPU required):

```sh
mkdir -p models
apptainer exec --cleanenv --bind "$PWD/models:/models" corridorkey2.sif \
    corridorkey-download-models
```

This uses the bundled [upstream downloader](https://github.com/nikopueringer/CorridorKey2.0/blob/485f5e9ab759ead6138cc990776184b59d6ea971/scripts/download_weights.py)
to fetch CorridorKey's weights and foundation statistics, plus the complete
C-RADIO snapshot, MoGe checkpoint, and RVM checkpoint (about 5 GB total).
Foundation model revisions and the RVM checksum follow upstream pins.
Downloads can be rerun after interruption. Use `--revision <HF-commit-SHA>` to
pin the CorridorKey model revision as well; otherwise it uses the current HF main.
Keep the entire directory, including C-RADIO's Python/configuration files.

You can specify another writable destination as a positional argument, provided
that host directory is visible inside the container. `/models` is simplest.
The helper temporarily enables online mode only in the downloader subprocess.
Normal inference always sets Hugging Face and Transformers to offline mode.

## Run offline

Copy **both** `corridorkey2.sif` and the whole `models/` directory to the offline
Linux workstation. No pip install, Git checkout, or HF cache is needed there.
Check the files without network access:

```sh
apptainer exec --cleanenv --bind "$PWD/models:/models:ro" corridorkey2.sif \
    corridorkey-download-models --check
```

This is a presence/nonempty check, not a complete model integrity or GPU load test.

Then run inference from the directory containing your plate:

```sh
apptainer run --cleanenv --nv --bind "$PWD/models:/models:ro" corridorkey2.sif \
    --input shot.mp4 --output_dir output
```

All upstream `infer.py` options pass through, including hints and linear EXRs:

```sh
apptainer run --cleanenv --nv --bind "$PWD/models:/models:ro" corridorkey2.sif \
    --input frames --frame_dir_fps 24 --frame_dir_linear \
    --output_dir output --output_format exr --outputs alpha fg cutout
```

The wrapper preserves your working directory. Apptainer normally binds it and
your home automatically; bind other input/output storage explicitly, e.g.
`--bind /mnt/plates:/mnt/plates`. Use a writable `--temp_dir` with enough disk
space for long clips. The SIF and models may remain read-only.

An NVIDIA GPU with bfloat16 support and a host driver compatible with the CUDA
12.8 PyTorch wheels is required. Upstream targets RTX 30-series or newer;
the workstation Ampere RTX A6000 is also suitable. The GTX 1050 Ti is unsuitable.
For low memory, add `--low_vram`; upstream documents 4 GB for up to 1440p and
6 GB for 4K with reduced temporal windows. Native resolution is preserved.

## Verification

The workflow runs helper tests, `pip check`, imports of the runtime and vendored
MoGe, an HDR EXR read/write round-trip, CLI help, and an expected missing-model
failure. Smoke-test imports block socket connections and run without models or
a pre-existing HF cache. Hosted runners have no GPU: real model loading and
inference must be verified on your NVIDIA workstation after downloading assets.

For an optional full model-load check (requires GPU and enough RAM/VRAM):

```sh
apptainer exec --cleanenv --nv --bind "$PWD/models:/models:ro" corridorkey2.sif \
    python /opt/CorridorKey/scripts/smoke_test_runtime.py --load_model
```
