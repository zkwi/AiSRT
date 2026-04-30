# Packaging Notes

The default GitHub Release ZIP is a lightweight source package built by `scripts/build_portable.ps1`.
It intentionally does not bundle Python, PyTorch/CUDA runtime libraries, model weights, FFmpeg, caches, media, generated subtitles, screenshots or logs.

`aisrt_portable.spec` is kept only as an optional maintainer experiment for full-runtime PyInstaller builds. It is not used for the default Release asset.
