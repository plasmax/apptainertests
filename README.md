# apptainertests

Apptainer (`.def`) and Docker build recipes for CV / 3D-reconstruction tooling,
built on GitHub Actions. Every workflow is `workflow_dispatch` only — trigger it
from the Actions tab.

## Layout

| Path | Contents |
| --- | --- |
| `definitions/` | Apptainer definition files (`.def`) |
| `docker/` | Docker build contexts (`lichtfeld-studio/`, `megasam/`) |
| `scripts/corridorkey2/` | CorridorKey model downloader, launcher, and smoke tests |
| `scripts/lfs-local/` | Numbered helper scripts for building LichtFeld Studio on a local host |
| `docs/` | Build notes and state write-ups |
| `.github/workflows/` | CI build workflows |
| `AGENTS.md` | Conventions for adding recipes and workflows |

## Apptainer images

Builds run from the repo root, e.g. `apptainer build gsplat-cuda124.sif definitions/gsplat-cuda124.def`.

| Definition | Base | Workflow |
| --- | --- | --- |
| `colmap-pycolmap-cuda124.def` | `colmap/colmap` | [![Build COLMAP + pycolmap Apptainer](https://github.com/plasmax/apptainertests/actions/workflows/build-colmap-pycolmap.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-colmap-pycolmap.yml) |
| `colmap-pycolmap-tapnet-cuda124.def` | `colmap/colmap` | [![Build COLMAP + pycolmap + tapnet](https://github.com/plasmax/apptainertests/actions/workflows/build-colmap-pycolmap-tapnet.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-colmap-pycolmap-tapnet.yml) |
| `corridorkey2.def` | `python:3.11-slim-bookworm` | [![CorridorKey 2.0 (GPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-corridorkey2.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-corridorkey2.yml) |
| `dynamic-video-depth.def` | `ubuntu:22.04` | [![Dynamic Video Depth (GPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-dynamic-video-depth.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-dynamic-video-depth.yml) |
| `gsplat-cuda124.def` | `ubuntu:22.04` | [![GSPLAT-CUDA124](https://github.com/plasmax/apptainertests/actions/workflows/build-gsplat-cuda124.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-gsplat-cuda124.yml) |
| `helloworld.def` | `alpine` | [![Build Apptainer Image](https://github.com/plasmax/apptainertests/actions/workflows/build-helloworld-apptainer.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-helloworld-apptainer.yml) |
| `lichtfeld-studio-docker.def` | `plasmax7/lichtfeld-studio` | [![Build LichtFeld Studio (Docker-based Apptainer)](https://github.com/plasmax/apptainertests/actions/workflows/build-lichtfeld-studio-docker-apptainer.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-lichtfeld-studio-docker-apptainer.yml) |
| `lichtfeld-studio-el9.def` | `rockylinux:9` | [![Build LichtFeld Studio (EL9)](https://github.com/plasmax/apptainertests/actions/workflows/build-lichtfeld-studio-el9.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-lichtfeld-studio-el9.yml) |
| `marigold2.def` | `ubuntu:22.04` | [![Marigold V2 (GPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-marigold2.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-marigold2.yml) |
| `pixel-perfect-depth.def` | `ubuntu:22.04` | [![Pixel Perfect Depth (GPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-pixel-perfect-depth.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-pixel-perfect-depth.yml) |
| `torch1.def` | `ubuntu:22.04` | [![Build pytorch test apptainer](https://github.com/plasmax/apptainertests/actions/workflows/pytorch1.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/pytorch1.yml) |
| `vda-py-base.def` | `python:3.10-slim` | [![VDA-PY (CPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-vda-py-base.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-vda-py-base.yml) |
| `vda-ubuntu-base-cpu.def` | `ubuntu:22.04` | [![VDA-UBUNTU-PYRIGHT (CPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-vda-ubuntu-base-cpu.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-vda-ubuntu-base-cpu.yml) |
| `pycusfm-cuda12.def` | `nvcr.io/nvidia/tensorrt` | none — needs the PyCuSFM source tree (`pyproject.toml`, `pycusfm/`) in the build context |

## CorridorKey 2.0 quick start

The image includes CorridorKey's source, Python dependencies, CUDA-enabled
PyTorch, FFmpeg, and EXR support. **Models are downloaded separately** into a
portable host directory.

1. Open [CorridorKey 2.0 (GPU)](https://github.com/plasmax/apptainertests/actions/workflows/build-corridorkey2.yml),
   select **Run workflow**, then download and extract the `corridorkey2-sif`
   artifact from the completed run.
2. Download all models once on an internet-connected Linux machine with Apptainer
   (no GPU required):

   ```sh
   mkdir -p models
   apptainer exec --cleanenv --bind "$PWD/models:/models" corridorkey2.sif \
       corridorkey-download-models
   ```

3. Copy the SIF and the **entire** `models/` directory to your offline workstation.
   Check the required files and run inference:

   ```sh
   apptainer exec --cleanenv --bind "$PWD/models:/models:ro" corridorkey2.sif \
       corridorkey-download-models --check

   apptainer run --cleanenv --nv --bind "$PWD/models:/models:ro" corridorkey2.sif \
       --input shot.mp4 --output_dir output
   ```

Inference requires a compatible NVIDIA GPU and host driver for CUDA 12.8.
All upstream inference arguments pass through; add `--low_vram` to reduce memory
use, or `--output_format exr` for EXR sequences. Bind storage outside your working
directory or home explicitly with `--bind /path:/path`.

For local builds, linear EXR input, model revision pinning, and GPU validation,
see [CorridorKey 2.0 instructions](docs/corridorkey2.md).

## Docker images

| Context | Workflow |
| --- | --- |
| `docker/megasam/` | [![Build and Publish MegaSaM](https://github.com/plasmax/apptainertests/actions/workflows/megasam-docker-publish.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/megasam-docker-publish.yml) |
| `docker/lichtfeld-studio/` | [![build-and-push](https://github.com/plasmax/apptainertests/actions/workflows/lichtfeld-studio-docker-build-and-push.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/lichtfeld-studio-docker-build-and-push.yml) |

`docker/lichtfeld-studio/` builds with the **repo root as context** (the Dockerfile
copies `docker/lichtfeld-studio/entrypoint.sh`). Use `docker/lichtfeld-studio/run_docker.sh`
from the repo root to build and enter the dev container.

## Other workflows

[![build-xformers-cu128-cp313](https://github.com/plasmax/apptainertests/actions/workflows/build-xformers-cu128-cp313.yml/badge.svg)](https://github.com/plasmax/apptainertests/actions/workflows/build-xformers-cu128-cp313.yml)
builds an xFormers wheel (CUDA 12.8 / CPython 3.13) directly on the runner — no definition file.

## Docs

- [docs/corridorkey2.md](docs/corridorkey2.md) — model-free CorridorKey 2.0 image, model download, and offline usage
- [docs/lfs-local-build-notes.md](docs/lfs-local-build-notes.md) — running the `scripts/lfs-local/` build chain
- [docs/lichtfeld-studio-el9-notes.md](docs/lichtfeld-studio-el9-notes.md) — EL9 from-source build notes
- [docs/lichtfeld-studio-docker-state-2026-04-02.md](docs/lichtfeld-studio-docker-state-2026-04-02.md) — Docker-based build state snapshot
