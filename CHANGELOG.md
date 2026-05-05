# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog style for now: group user-visible changes under the next unreleased version, then move them under a dated version when publishing a release.

## Unreleased

- Integrated translation into the main GUI processing flow with an enable-translation checkbox and target-language field.
- Improved the GUI translation-enabled processing flow so original ASR subtitles are kept when local translation loading or translation fails.
- Optimized README and docs Wiki copy for GitHub searchability around local AI subtitle generation, SRT translation, GUI, and CLI workflows.
- Improved translation progress and completion messages in the GUI, plus localized target-language suffix handling and package metadata.

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
