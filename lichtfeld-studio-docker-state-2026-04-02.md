# LichtFeld Docker Apptainer State - 2026-04-02

## Current status

- GitHub Actions `lichtfeld-studio-docker.def` build succeeded for the first time.
- Reported GitHub Actions SIF size is about `10G`.
- Known-good local runtime-test SIF is `6.4G`:
  - `/mnt/scratch/mlast/lichtfeld_studio_runtime_test.sif`
  - `/net/code/workspaces/mlast/lichtfeld_studio_runtime_test.sif`
- Local workstation runtime test succeeded after fixing:
  - inherited Docker entrypoint
  - `LD_LIBRARY_PATH` for build-tree libs
  - RmlUI resource layout (`training.rml`)

## Known-good local flow

- Build Docker base image from `lichtfeld-studio-docker/Dockerfile` with CUDA `12.8.0`.
- Build Apptainer sandbox from `docker://plasmax7/lichtfeld-studio:latest`.
- Build LichtFeld-Studio on `/mnt/scratch/mlast`.
- Package a runtime-test SIF by copying the built tree into the sandbox and rebuilding the SIF.
- Launch on the GUI workstation with:
  - `apptainer exec --cleanenv --nv`
  - X11 binds
  - `.Xauthority` bind
  - `/run/user/$UID` bind
  - `/mnt/scratch/mlast` bind
  - `LD_LIBRARY_PATH` pointing at `/opt/LichtFeld-Studio/build`, `build/vcpkg_installed/x64-linux/lib`, and `build/src/python`

Relevant helper scripts:

- [lfs-local/00-rebuild-apptainer-from-docker.sh](/mnt/scratch/mlast/apptainertests/lfs-local/00-rebuild-apptainer-from-docker.sh)
- [lfs-local/01-verify-toolchain.sh](/mnt/scratch/mlast/apptainertests/lfs-local/01-verify-toolchain.sh)
- [lfs-local/03-configure.sh](/mnt/scratch/mlast/apptainertests/lfs-local/03-configure.sh)
- [lfs-local/04-build.sh](/mnt/scratch/mlast/apptainertests/lfs-local/04-build.sh)
- [lfs-local/06-package-runtime-test-sif.sh](/mnt/scratch/mlast/apptainertests/lfs-local/06-package-runtime-test-sif.sh)
- [lfs-local/07-run-runtime-test-sif.sh](/mnt/scratch/mlast/apptainertests/lfs-local/07-run-runtime-test-sif.sh)

## Important fixes already rolled into the repo

- `lichtfeld-studio-docker/Dockerfile`
  - default CUDA is now `12.8.0`
- `lichtfeld-studio-docker/run_docker.sh`
  - removed host CUDA autodetect
  - refuses versions below `12.8.0`
- `lichtfeld-studio-docker.def`
  - builds against `/home/ubuntu/vcpkg`
  - uses default `gcc/g++`
  - launches `/usr/local/bin/lichtfeld-studio`
  - merges generated visualizer resources into `build/resources`
  - sets runtime X11/DBus/XDG env
- `.github/workflows/build-lichtfeld-studio-docker-apptainer.yml`
  - smoke test checks the binary, `ldd`, `training.rml`, and `python3`

## Size references from the working local setup

- Local runtime-test SIF: `6.4G`
- Writable sandbox: `18G`
- Sandbox breakdown:
  - `lichtfeld-studio-base-cuda128/usr/local/cuda-12.8`: `6.6G`
  - `lichtfeld-studio-base-cuda128/opt/LichtFeld-Studio`: `4.4G`
  - `lichtfeld-studio-base-cuda128/home/ubuntu/vcpkg`: `3.5G`
- Scratch build tree:
  - `/mnt/scratch/mlast/lichtfeld-build/LichtFeld-Studio`: `4.4G`
  - `/mnt/scratch/mlast/lichtfeld-build/LichtFeld-Studio/build`: `4.3G`
  - `/mnt/scratch/mlast/lichtfeld-build/LichtFeld-Studio/build/vcpkg_installed`: `3.3G`

## Likely reasons the GitHub Actions image is larger

- The definition builds and keeps the full source tree under `/opt/LichtFeld-Studio`.
- The definition keeps the full build tree, not just the final binary and runtime assets.
- `build/vcpkg_installed` is large on its own.
- CUDA `12.8` is already a large base payload before LichtFeld-Studio is added.

The most likely cleanup target is not CUDA itself but the kept build/source content:

- object files and intermediate artifacts in `build/`
- source checkout in `/opt/LichtFeld-Studio`
- any unnecessary libraries or duplicate runtime assets

## First checks for next week

Run these against the GitHub-built SIF and compare with the local `6.4G` runtime-test SIF:

```bash
apptainer exec lichtfeld_studio_docker.sif du -sh /opt/LichtFeld-Studio
apptainer exec lichtfeld_studio_docker.sif du -sh /opt/LichtFeld-Studio/build
apptainer exec lichtfeld_studio_docker.sif du -sh /opt/LichtFeld-Studio/build/vcpkg_installed
apptainer exec lichtfeld_studio_docker.sif du -sh /home/ubuntu/vcpkg
apptainer exec lichtfeld_studio_docker.sif find /opt/LichtFeld-Studio/build -name '*.o' | head
apptainer exec lichtfeld_studio_docker.sif find /opt/LichtFeld-Studio/build -path '*/debug/*' | head
```

If the goal is a smaller distribution image, the likely next step is a two-stage packaging approach:

- build in one location
- copy only runtime outputs, resources, and required shared libs into a smaller final image

## Local environment notes

- `/mnt/scratch/mlast` is local `ext4` and should stay the build location.
- `/net/code/workspaces/mlast` is `nfs` and is fine for copied artifacts, not for heavy builds.
- GUI runtime tests must happen on the workstation, not from the SSH-only server shell.

## Repo state at shutdown

Last relevant commits:

- `08d360d` `Finalize LichtFeld Docker Apptainer workflow`
- `0d95389` `Update LichtFeld Docker build to CUDA 12.8`

Untracked local directories intentionally left in place:

- `lfs/`
- `lfs_build.sh`
- `lichtfeld-studio-base/`
- `lichtfeld-studio-base-cuda128/`
