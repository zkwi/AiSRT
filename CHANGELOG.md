# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple changelog style for now: group user-visible changes under the next unreleased version, then move them under a dated version when publishing a release.

## Unreleased

## 0.1.2 - 2026-05-05

- Integrated translation into the main GUI processing flow with an enable-translation checkbox and target-language field.
- Added a local SRT translation CLI and GUI dialog for translating existing subtitle files.
- Improved the GUI translation-enabled processing flow so original ASR subtitles are kept when local translation loading or translation fails.
- Optimized README and docs Wiki copy for GitHub searchability around local AI subtitle generation, SRT translation, GUI, and CLI workflows.
- Improved translation progress and completion messages in the GUI, plus localized target-language suffix handling and package metadata.
- Clarified GUI language controls as UI language, subtitle source language, and translation language; made translation language selectors dropdown-only and removed the confusing context field from the main window.
- Added estimated remaining time to ASR and translation progress output in `minutes:seconds` format.
- Renamed the translation-enabled primary action to "Recognize + Translate" and tightened common-settings label spacing.
- Expanded UI copy presets to Simplified Chinese, Traditional Chinese, English, Japanese, Korean, and Spanish; the GUI now follows the system language by default unless the user changes it.
- Renamed "technical log" to "detailed log" and improved user-facing error hints for model download, CUDA/GPU, FFmpeg, permissions, and disk-space failures.
- Added bilingual README preview screenshots and refreshed release documentation.

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
