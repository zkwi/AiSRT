from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import shutil


@dataclass
class CheckResult:
    name: str
    status: str
    message: str


def check_executable(name: str, label: str) -> CheckResult:
    path = shutil.which(name)
    if path:
        return CheckResult(name, "ok", f"{label} 可用: {path}")
    return CheckResult(name, "error", f"没有找到 {label}，请先安装 FFmpeg 并确认 {name} 在 PATH 中。")


def check_torch_cuda() -> CheckResult:
    try:
        import torch
    except Exception as exc:
        return CheckResult("torch", "error", f"PyTorch 无法导入: {exc}")

    version = getattr(torch, "__version__", "unknown")
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        return CheckResult("cuda", "ok", f"PyTorch {version}，CUDA 可用: {device_name}")
    return CheckResult("cuda", "warn", f"PyTorch {version}，没有检测到 CUDA；可以运行 CPU 模式，但会很慢。")


def check_output_dir(output_dir: Path | None, project_dir: Path) -> CheckResult:
    target = output_dir or project_dir
    target = target.expanduser()
    check_dir = target if target.exists() else target.parent

    if not check_dir.exists():
        return CheckResult("output", "error", f"输出目录的上级目录不存在: {check_dir}")
    if not check_dir.is_dir():
        return CheckResult("output", "error", f"输出目录的上级路径不是目录: {check_dir}")
    if not os.access(check_dir, os.W_OK):
        return CheckResult("output", "error", f"输出目录不可写: {check_dir}")
    return CheckResult("output", "ok", f"输出目录可写: {target}")


def check_cache_dir(project_dir: Path) -> CheckResult:
    cache_dir = Path(os.environ.get("HF_HOME") or project_dir / ".hf_cache").expanduser()
    if cache_dir.exists():
        return CheckResult("cache", "ok", f"模型缓存目录: {cache_dir}")
    return CheckResult("cache", "warn", f"模型缓存目录尚不存在，首次运行会创建并下载模型: {cache_dir}")


def run_diagnostics(project_dir: Path, output_dir: Path | None = None) -> list[CheckResult]:
    project_dir = project_dir.expanduser().resolve()
    return [
        check_executable("ffmpeg", "FFmpeg"),
        check_executable("ffprobe", "ffprobe"),
        check_torch_cuda(),
        check_output_dir(output_dir, project_dir),
        check_cache_dir(project_dir),
    ]


def blocking_messages(results: list[CheckResult]) -> list[str]:
    return [result.message for result in results if result.status == "error"]


def format_diagnostics(results: list[CheckResult]) -> str:
    labels = {
        "ok": "OK",
        "warn": "WARN",
        "error": "ERROR",
        "info": "INFO",
    }
    return "\n".join(f"[{labels.get(result.status, result.status.upper())}] {result.message}" for result in results)
