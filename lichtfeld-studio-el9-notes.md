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
- The EL9 definition now adds the Rocky/RHEL equivalents before `vcpkg` builds SDL.

## Next rebuild expectations

- The image should launch the build-tree binary by default until upstream install rules place all required runtime libs into the install prefix.
- CI smoke testing should validate:
  - the executable exists
  - `ldd` succeeds
  - the SDL archive contains at least one desktop video backend object (`x11` or `wayland`)

## Separate runtime warning observed

- The offline test host reported `CUDA 12.4 unsupported. Requires 12.8+ (driver 570+)`.
- That is a host driver/runtime issue, not the container build failure, but it may still limit features after the GUI issue is fixed.
