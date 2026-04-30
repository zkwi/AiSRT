from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRS = {
    ".git",
    ".hf_cache",
    ".idea",
    ".pytest_cache",
    ".venv",
    "aisrt.egg-info",
    "models",
    "screenshots",
    "video",
}
TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".example",
    ".ini",
    ".md",
    ".ps1",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
SELF = Path(__file__).resolve()
OLD_PROJECT_NAMES = {
    "ja_movie_sub",
    "ja-movie-sub",
    "qwen_asr_sub",
    "qwen-asr-sub",
    "ai_subtitle_assistant",
    "ai-subtitle-assistant",
}
REQUIRED_GITIGNORE_PATTERNS = {
    ".cache/",
    ".env",
    ".venv/",
    ".hf_cache/",
    ".idea/",
    "models/",
    "video/",
    "screenshots/",
    "*.srt",
    "*.raw.srt",
    "*.mp4",
    "*.log",
    "*.bak",
    "*.orig",
    "*.rej",
    "*.egg-info/",
    "!requirements.txt",
    "!.env.example",
}
REQUIRED_PROJECT_FILES = {
    "AGENTS.md",
    "README.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "docs/README.md",
    "docs/engineering.md",
    "docs/release-checklist.md",
}
REQUIRED_PYPROJECT_SNIPPETS = {
    'name = "aisrt"',
    'license = { text = "MIT" }',
    'license-files = ["LICENSE"]',
    "classifiers = [",
    "keywords = [",
    'ai-sub = "aisrt.cli:main"',
    'ai-sub-gui = "aisrt.gui:main"',
}
SENSITIVE_PATTERNS = [
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"/Users/[^/\s]+", re.IGNORECASE),
    re.compile(r"/home/[^/\s]+", re.IGNORECASE),
    re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


def iter_project_paths() -> list[Path]:
    paths: list[Path] = []
    for path in PROJECT_ROOT.rglob("*"):
        relative_parts = path.relative_to(PROJECT_ROOT).parts
        if any(part in IGNORED_DIRS for part in relative_parts):
            continue
        paths.append(path)
    return paths


def test_project_paths_do_not_use_old_project_names():
    offenders = []
    for path in iter_project_paths():
        relative = path.relative_to(PROJECT_ROOT).as_posix().lower()
        if any(old_name in relative for old_name in OLD_PROJECT_NAMES):
            offenders.append(relative)

    assert offenders == []


def test_standard_open_source_files_exist():
    missing = sorted(path for path in REQUIRED_PROJECT_FILES if not (PROJECT_ROOT / path).exists())

    assert missing == []


def test_text_files_do_not_contain_obvious_private_data_or_old_project_names():
    offenders = []
    for path in iter_project_paths():
        if not path.is_file() or path.resolve() == SELF:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".gitignore", ".gitattributes"}:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        lowered = text.lower()
        for old_name in OLD_PROJECT_NAMES:
            if old_name in lowered:
                offenders.append(f"{relative}: old name {old_name}")
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                offenders.append(f"{relative}: {pattern.pattern}")

    assert offenders == []


def test_gitignore_covers_local_runtime_and_privacy_artifacts():
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    missing = sorted(pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in gitignore)

    assert missing == []


def test_pyproject_has_basic_package_metadata():
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    missing = sorted(snippet for snippet in REQUIRED_PYPROJECT_SNIPPETS if snippet not in pyproject)

    assert missing == []
