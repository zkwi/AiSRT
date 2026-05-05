# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog style for now: group user-visible changes under the next unreleased version, then move them under a dated version when publishing a release.

## Unreleased

- Improved the GUI one-step recognize-and-translate flow so original ASR subtitles are kept when local translation loading or translation fails.

## 0.1.1 - 2026-05-01

- Added GitHub community files, issue and pull request templates, lightweight CI and Dependabot configuration.
- Split the default CUDA PyTorch requirements into a shared requirements file for runtime and development installs.
- Strengthened open-source hygiene checks for required community files, private data patterns and Markdown links.
- Removed the README screenshot reference because runtime screenshots are intentionally ignored before release.
- Added a UTF-8 bilingual release notes template for GitHub Releases.

## 0.1.0 - 2026-04-30

- Renamed the Python package to `aisrt`.
- Added open-source hygiene checks for private paths, stale project names and ignored artifacts.
- Improved GUI layout and moved per-file progress into the queue status column.
- Added lightweight Windows portable packaging tooling, an optional PyInstaller spec and release asset checks.
