from aisrt.user_messages import friendly_error_message


def test_friendly_error_message_explains_cuda_problem():
    message = friendly_error_message(RuntimeError("当前 PyTorch 环境未检测到 CUDA，请改用 --device cpu"))

    assert "没有检测到 CUDA" in message
    assert "CPU" in message


def test_friendly_error_message_explains_out_of_memory():
    message = friendly_error_message(RuntimeError("CUDA out of memory. Tried to allocate 2 GiB"))

    assert "显存不足" in message
    assert "低显存" in message
    assert "0.6B" in message
    assert "批大小" not in message


def test_friendly_error_message_keeps_output_conflict_action():
    message = friendly_error_message(FileExistsError("输出已存在，请加 --overwrite:\n  - movie.srt"))

    assert "输出已存在" in message
    assert "--overwrite" in message
