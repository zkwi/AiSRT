from __future__ import annotations


def friendly_error_message(exc: BaseException) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    lower = message.lower()

    if "输出已存在" in message:
        return message

    if "ffmpeg" in lower and ("not found" in lower or "未找到" in message or "提取音频失败" in message):
        return (
            "没有找到或无法使用 FFmpeg。请先安装 FFmpeg，并确认 ffmpeg 和 ffprobe "
            "可以在命令行中直接运行。"
        )

    if "ffprobe" in lower and ("not found" in lower or "未找到" in message):
        return "没有找到 ffprobe。请检查 FFmpeg 是否完整安装，并确认它在 PATH 中。"

    if (
        "未检测到 cuda" in lower
        or "cuda is not available" in lower
        or "no nvidia driver" in lower
        or "found no nvidia driver" in lower
    ):
        return "没有检测到 CUDA。可以改用 CPU 慢速模式，或安装 CUDA 版 PyTorch 后重试。"

    if "out of memory" in lower or "cuda error: out of memory" in lower:
        return "显存不足。建议使用“低显存”运行模式，或切换到 0.6B 模型后重试。"

    if "local_files_only" in lower or "cannot find the requested files" in lower:
        return "本地没有找到模型文件。请取消“只使用本地模型缓存”，或先把模型下载到本地。"

    if (
        "connection error" in lower
        or "read timed out" in lower
        or "connection timed out" in lower
        or "couldn't connect" in lower
        or "could not connect" in lower
        or "failed to establish a new connection" in lower
        or "name resolution" in lower
        or "temporary failure in name resolution" in lower
    ):
        return "模型下载失败。请检查网络或 Hugging Face 访问是否可用；也可以提前下载模型后勾选“只使用本地模型缓存”。"

    if (
        "401" in lower
        or "403" in lower
        or "gated repo" in lower
        or "private repository" in lower
        or "repository not found" in lower
        or "requires authentication" in lower
    ):
        return "模型访问受限。请确认模型 ID 正确、已同意模型协议，或已登录 Hugging Face。"

    if "permission denied" in lower or "winerror 5" in lower or "access is denied" in lower:
        return "没有写入权限。请换一个输出目录，或确认当前目录允许写入。"

    if "no space left" in lower or "disk full" in lower:
        return "磁盘空间不足。请清理空间后重试，模型缓存和临时音频都会占用较多空间。"

    return message
