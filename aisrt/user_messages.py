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

    if "未检测到 cuda" in lower or "cuda is not available" in lower:
        return "没有检测到 CUDA。可以改用 CPU 慢速模式，或安装 CUDA 版 PyTorch 后重试。"

    if "out of memory" in lower or "cuda error: out of memory" in lower:
        return "显存不足。建议使用“低显存”运行模式，或切换到 0.6B 模型后重试。"

    if "local_files_only" in lower or "cannot find the requested files" in lower:
        return "本地没有找到模型文件。请取消“只使用本地模型缓存”，或先把模型下载到本地。"

    if "permission denied" in lower or "winerror 5" in lower or "access is denied" in lower:
        return "没有写入权限。请换一个输出目录，或确认当前目录允许写入。"

    if "no space left" in lower or "disk full" in lower:
        return "磁盘空间不足。请清理空间后重试，模型缓存和临时音频都会占用较多空间。"

    return message
