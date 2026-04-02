# LichtFeld Local Build Notes

## Current state

- Base Apptainer sandbox created from DockerHub image:
  `/mnt/scratch/mlast/apptainertests/lichtfeld-studio-base`
- Host scratch is bind-mounted into the container at:
  `/mnt/scratch/mlast`
- Local source checkout is at:
  `/mnt/scratch/mlast/lichtfeld-build/LichtFeld-Studio`

## What we verified

- The Docker-based sandbox contains a working `vcpkg` install at:
  `/home/ubuntu/vcpkg`
- `vcpkg version` worked inside the container.
- The Apptainer sandbox needed the bind target created inside the image first:
  `/mnt/scratch/mlast`

## Commands used

Build sandbox from Docker image:

```bash
apptainer build --fakeroot --sandbox lichtfeld-studio-base docker://plasmax7/lichtfeld-studio:latest
```

Enter sandbox with scratch bind:

```bash
apptainer shell --fakeroot --writable --bind /mnt/scratch/mlast:/mnt/scratch/mlast /mnt/scratch/mlast/apptainertests/lichtfeld-studio-base
```

Set up `vcpkg` env inside container:

```bash
export VCPKG_ROOT=/home/ubuntu/vcpkg
export PATH=$VCPKG_ROOT:$PATH
vcpkg version
```

Clone source onto scratch:

```bash
mkdir -p /mnt/scratch/mlast/lichtfeld-build
cd /mnt/scratch/mlast/lichtfeld-build
git clone --recursive --depth 1 --shallow-submodules https://github.com/MrNeRF/LichtFeld-Studio.git
cd LichtFeld-Studio
```

Configure:

```bash
export VCPKG_ROOT=/home/ubuntu/vcpkg
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_TOOLCHAIN_FILE=/home/ubuntu/vcpkg/scripts/buildsystems/vcpkg.cmake \
  -DBUILD_PYTHON_STUBS=OFF
```

## Where we are now

- The first `cmake -S . -B build ...` run failed during CUDA compiler detection.
- Root cause:
  CUDA 12.4 in the base image rejects the default `gcc-14` / `g++-14`.
- Good news:
  the sandbox already contains `gcc-11` / `g++-11`, so this is salvageable
  without rebuilding the whole Apptainer image.

- `cmake -S . -B build ...` is/was running in `tmux`.
- It is safe to detach from `tmux` and reconnect later.
- The next local recovery step is:

```bash
/mnt/scratch/mlast/apptainertests/lfs-local/03-configure.sh
```

- That script writes a log file under:
  `/mnt/scratch/mlast/lichtfeld-build/logs`
- The next command after configure succeeds is:

```bash
/mnt/scratch/mlast/apptainertests/lfs-local/04-build.sh
```

## Helper scripts

- Rebuild sandbox from DockerHub image:
  `/mnt/scratch/mlast/apptainertests/lfs-local/00-rebuild-apptainer-from-docker.sh`
- Verify toolchain:
  `/mnt/scratch/mlast/apptainertests/lfs-local/01-verify-toolchain.sh`
- Clone source:
  `/mnt/scratch/mlast/apptainertests/lfs-local/02-clone-source.sh`
- Reconfigure with logging:
  `/mnt/scratch/mlast/apptainertests/lfs-local/03-configure.sh`
- Build with logging:
  `/mnt/scratch/mlast/apptainertests/lfs-local/04-build.sh`
- Run the GUI directly from the build tree in the sandbox:
  `/mnt/scratch/mlast/apptainertests/lfs-local/05-run-gui-from-build-tree.sh`
- Package a runtime-test SIF from the current sandbox + build tree:
  `/mnt/scratch/mlast/apptainertests/lfs-local/06-package-runtime-test-sif.sh`
- Run a packaged runtime-test SIF on a GUI workstation:
  `/mnt/scratch/mlast/apptainertests/lfs-local/07-run-runtime-test-sif.sh`

## Latest working state

- The rebuilt Docker image with CUDA `12.8` and the default GCC toolchain
  configured and built LichtFeld-Studio successfully.
- The working local build uses the default `gcc` / `g++` in the CUDA 12.8 image,
  not the temporary `gcc-11` workaround.
- GUI runtime testing on the workstation only worked once the packaged runtime
  tree included the generated visualizer resources under:
  `/opt/LichtFeld-Studio/build/resources/assets/rmlui`
- The Docker-based Apptainer recipe now needs to bake in that resource merge so
  GitHub Actions builds reproduce the working runtime layout directly.

## GitHub Actions status

- Simplified Docker-based Apptainer recipe committed and pushed on `main`.
- Commit:
  `21ca306` - `Simplify Docker-based LichtFeld Apptainer build`
