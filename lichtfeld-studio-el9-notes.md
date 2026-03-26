# LichtFeld Studio EL9 Notes

## 2026-03-26 local build findings

- Local Apptainer build completed and produced a SIF, but the first runtime test on an NVIDIA/X11 host still failed.
- What failed:
  - The installed runtime tree was incomplete. `liblfs_rmlui.so` existed in `/opt/LichtFeld-Studio/build` but not under `/opt/lichtfeld`, and the image environment pointed at `/opt/lichtfeld/lib` instead of `/opt/lichtfeld/lib64`.
  - The bundled SDL archive had no GUI backends. `ar t /opt/LichtFeld-Studio/build/vcpkg_installed/x64-linux/lib/libSDL3.a` only showed:
    - `SDL_video.c.o`
    - `SDL_video_unsupported.c.o`
    - `SDL_nullvideo.c.o`
    - `SDL_offscreenvideo.c.o`
  - On the offline test host, forcing `SDL_VIDEODRIVER=x11` still failed with `Failed to initialize SDL: x11 not available`.
- What worked:
  - Running the build-tree executable inside the image got far enough to prove CUDA init, config loading, and app startup were otherwise working:
    `/opt/LichtFeld-Studio/build/LichtFeld-Studio`
  - X11 socket and auth on the host were valid; the failure was inside the image, not host access control.

## Why the SDL backend was missing

- `vcpkg` restored `sdl3[core,ibus,wayland,x11]`, but the resulting static archive still lacked X11/Wayland objects.
- `/opt/vcpkg/ports/sdl3/portfile.cmake` warns that Linux builds need extra system development packages:
  - X11: `libx11-dev`, `libxft-dev`, `libxext-dev`
  - Wayland: `libwayland-dev`, `libxkbcommon-dev`, `libegl1-mesa-dev`
  - IBus: `libibus-1.0-dev`
- SDL's actual configure step on EL9 also hard-failed later on `XTEST`, so the recipe needs the wider desktop header set, not just the three packages mentioned in the port warning.

## 2026-03-26 interactive sandbox repair

- What worked:
  - Converting the last SIF into a writable sandbox with `apptainer build --sandbox` made it possible to repair the image incrementally instead of restarting a full build.
  - `vcpkg remove --classic --recurse sdl3 imgui` followed by a manifest reinstall rebuilt only `sdl3`, `imgui`, and `implot`.
  - After the rebuild, `ar t /opt/LichtFeld-Studio/build/vcpkg_installed/x64-linux/lib/libSDL3.a` showed both `SDL_x11*.o` and `SDL_wayland*.o`, including `SDL_x11xtest.c.o`.
  - `cmake --build` and `cmake --install` both completed successfully once SDL rebuilt cleanly.
- What failed:
  - Deleting `libSDL3.a` and the `sdl3_*.list` files was not enough. `vcpkg install` still said `All requested installations completed successfully`, and CMake later failed because `SDL3Config.cmake` was missing.
  - The first real SDL configure failure was:
    `Couldn't find dependency package for XTEST. Please install the needed packages or configure with -DSDL_X11_XTEST=OFF`
  - A headless runtime probe in the sandbox still stops at:
    `libcuda.so.1: cannot open shared object file: No such file or directory`
    so GUI launch must still be rechecked on a host run with `--nv`.
- What changed to fix it:
  - The EL9 recipe now includes the wider SDL desktop dependency set:
    `libXext-devel`, `libXft-devel`, `libXrender-devel`, `libXrandr-devel`, `libXinerama-devel`, `libXcursor-devel`, `libXi-devel`, `libXfixes-devel`, `libXScrnSaver-devel`, `libXtst-devel`, `wayland-devel`, `libxkbcommon-devel`, `ibus-devel`, `libxcb-devel`, `xcb-util-devel`, `xcb-util-image-devel`, `xcb-util-keysyms-devel`, `xcb-util-renderutil-devel`, `xcb-util-wm-devel`.
  - The recipe now copies `liblfs_rmlui.so` into `/opt/lichtfeld/lib64` after `cmake --install`.
  - The image tests and CI smoke test now explicitly check for the copied `liblfs_rmlui.so` and for desktop SDL backends in `libSDL3.a`.

## 2026-03-26 runtime metadata mismatch

- What worked:
  - Inspecting the repaired interactive SIF immediately explained the loader error without another full launch attempt.
- What failed:
  - The repacked interactive SIF inherited stale metadata from the original SIF-to-sandbox conversion.
  - `apptainer inspect -r` showed the embedded runscript was still:
    `exec /opt/lichtfeld/bin/LichtFeld-Studio "$@"`
  - The embedded environment in `/.singularity.d/env/90-environment.sh` still had:
    `LD_LIBRARY_PATH=${GCC_TOOLSET_ROOT}/lib64:/opt/lichtfeld/lib:/usr/local/cuda/lib64:${LD_LIBRARY_PATH:-}`
    which omitted `/opt/lichtfeld/lib64`, so `liblfs_mcp.so` could not be found.
- What changed to fix it:
  - The recipe now sets an explicit install `RUNPATH` for the installed binary, including `\$ORIGIN/../lib64`, the GCC toolset runtime, the vcpkg runtime tree, and CUDA libs.
  - The runtime environment now includes `/opt/lichtfeld/lib64`.
  - `%test` and CI now run `ldd` on `/opt/lichtfeld/bin/LichtFeld-Studio` under `env -i` so this exact regression fails fast.

## 2026-03-26 missing Python UI bridge

- What worked:
  - The GUI launched once SDL and the runtime loader issues were fixed, which narrowed the remaining problem to the Python/plugin layer.
- What failed:
  - Startup logged:
    `Python module 'lichtfeld' not found. Expected a lichtfeld*.so/.pyd in: /opt/lichtfeld/bin/src/python, /opt/lichtfeld/bin`
  - The image actually installed the module and plugin package under:
    `/opt/lichtfeld/lib64/python/lichtfeld.cpython-312-x86_64-linux-gnu.so`
    `/opt/lichtfeld/lib64/python/lfs_plugins/...`
  - Upstream runtime path resolution only checks `../lib/python` relative to the executable, not `../lib64/python`.
- What changed to fix it:
  - The EL9 recipe now creates `/opt/lichtfeld/lib/python -> ../lib64/python` after install.
  - `%test` and CI now assert that `/opt/lichtfeld/lib/python` exposes both the `lichtfeld*.so` module and the `lfs_plugins` package.

## 2026-03-26 minor desktop integration fix

- What failed:
  - Clicking a URL from the UI hit `sh: line 1: xdg-open: command not found`.
- What changed to fix it:
  - The EL9 recipe now installs `xdg-utils`.
  - `%test` and CI now assert that `xdg-open` is present.

## Next rebuild expectations

- The image should launch the build-tree binary by default until upstream install rules place all required runtime libs into the install prefix.
- CI smoke testing should validate:
  - the executable exists
  - `ldd` succeeds
  - the SDL archive contains at least one desktop video backend object (`x11` or `wayland`)

## Separate runtime warning observed

- The offline test host reported `CUDA 12.4 unsupported. Requires 12.8+ (driver 570+)`.
- That is a host driver/runtime issue, not the container build failure, but it may still limit features after the GUI issue is fixed.
