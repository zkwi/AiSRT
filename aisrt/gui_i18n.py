from __future__ import annotations

import re


DEFAULT_UI_LANGUAGE = "zh-Hans"
UI_LANGUAGE_OPTIONS = [
    ("zh-Hans", "简体中文"),
    ("zh-Hant", "繁體中文"),
    ("en", "English"),
]

TEXT: dict[str, dict[str, str]] = {
    "zh-Hans": {
        "product_name": "AI 大模型字幕助手",
        "product_subtitle": "大模型 ASR 驱动 · 多语言识别 · 精准时间对齐",
        "ui_language_tooltip": "切换界面语言",
        "add_files": "添加文件",
        "translate_srt": "翻译字幕",
        "translate_srt_tooltip": "打开本地 SRT 翻译工具，支持多目标语言",
        "start": "开始处理",
        "start_translate": "识别并翻译",
        "start_translate_tooltip": "识别字幕后翻译为输出语言，同时保留原始字幕",
        "stop": "停止",
        "open_output_folder": "打开输出文件夹",
        "clear_queue": "清空队列",
        "remove_selected": "移除选中",
        "clear_completed": "清除已完成",
        "retry_failed": "重试失败",
        "queue_title": "文件队列",
        "empty_title": "还没有添加文件",
        "empty_hint": "点击“添加文件”选择多个媒体文件，或直接把文件拖入窗口。",
        "table_file": "文件",
        "table_status": "状态",
        "table_subtitle_dir": "字幕目录",
        "settings_title": "常用设置",
        "advanced_settings": "高级设置",
        "advanced_tooltip": "设备、音频分块等不常改的选项",
        "context_label": "上下文",
        "context_placeholder": "可选：片名、角色名、人名、地名；不确定时留空",
        "context_tooltip": "提供片名或角色名可帮助模型识别专有名词，不确定时留空",
        "recognition_language": "识别语言",
        "recognition_language_tooltip": "默认自动识别；明确知道音频语言时可手动指定",
        "output_language": "输出语言",
        "output_language_tooltip": "点击“识别并翻译”时生成的目标字幕语言",
        "profile_label": "运行模式",
        "profile_tooltip": "推荐适合大多数情况，低显存会使用更保守的参数",
        "model_size": "模型尺寸",
        "model_size_tooltip": "1.7B 质量更好；0.6B 更省显存、速度更快",
        "profile_recommended": "推荐",
        "profile_low_vram": "低显存",
        "profile_cpu_slow": "CPU 慢速",
        "advanced_hint": "设备、音频分块和字幕样式属于低频选项，通常保持默认即可。",
        "device": "设备",
        "device_auto": "自动",
        "device_gpu": "优先 GPU",
        "device_cpu": "CPU",
        "device_tooltip": "一般保持自动；只有排查问题时再手动指定设备",
        "audio_chunk": "音频分块",
        "chunk_safe": "稳妥（30 秒）",
        "chunk_recommended": "推荐（45 秒）",
        "chunk_long": "长分块（60 秒）",
        "chunk_tooltip": "只提供常用预设，避免无意义的秒级微调",
        "caption_style": "字幕样式",
        "caption_short": "短句",
        "caption_recommended": "推荐",
        "caption_long": "较长",
        "caption_tooltip": "控制字幕换行倾向；推荐适合大多数电影对白",
        "overwrite": "覆盖已有输出",
        "overwrite_tooltip": "未勾选时如字幕已存在，会在开始处理前询问是否覆盖",
        "local_only": "只使用本地模型缓存",
        "local_only_tooltip": "勾选后不会下载缺失模型",
        "close": "关闭",
        "status_ready": "准备就绪",
        "status_add_files": "请先添加文件",
        "status_ready_with_files": "已添加 {count} 个文件，可以开始处理",
        "status_kept_failed": "已保留 {count} 个失败文件，可重新开始处理",
        "status_processing": "处理中",
        "status_loading_model": "正在加载模型，首次运行可能需要下载模型",
        "status_cancelled": "已取消",
        "status_summary": "完成 {success} 个，失败 {failed} 个，取消 {cancelled} 个",
        "status_done_with_failed": "处理完成，有失败",
        "status_failed_detail": "{failed} 个文件失败，详情见运行日志",
        "status_done": "处理完成",
        "status_open_output": "可以打开输出文件夹查看字幕",
        "status_stopping": "正在停止，当前步骤结束后会退出",
        "log_title": "运行日志",
        "show_technical_log": "显示技术日志",
        "show_technical_log_tooltip": "默认只显示普通提示，勾选后查看完整技术日志",
        "clear_log": "清空日志",
        "clear_log_tooltip": "清空当前运行日志",
        "log_placeholder": "处理日志会显示在这里。",
        "select_media_files": "选择媒体文件",
        "media_files_filter": "媒体文件 ({extensions});;所有文件 (*)",
        "msg_no_media_title": "没有可处理文件",
        "msg_no_media_body": "没有找到支持的视频或音频文件。",
        "msg_no_failed_title": "没有失败文件",
        "msg_no_failed_body": "当前队列里没有失败文件。",
        "msg_no_files_title": "没有文件",
        "msg_no_files_body": "请先添加要处理的媒体文件。",
        "msg_diagnostics_failed": "环境检查未通过",
        "msg_output_exists": "输出已存在",
        "msg_output_exists_body": "以下字幕文件已存在，是否覆盖？\n{preview}",
        "msg_more_files": "另外 {count} 个文件",
        "msg_finished_title": "处理结束",
        "msg_finished_body": "成功：{success}\n失败：{failed}\n取消：{cancelled}\n可在队列中选择文件后打开输出文件夹。",
        "msg_no_dir_title": "没有目录",
        "msg_no_dir_body": "请先添加文件。",
        "msg_running_title": "正在处理",
        "msg_running_body": "当前任务还在运行。请先点击“停止”，等待当前步骤结束后再关闭。",
        "dialog_ok": "确定",
        "dialog_overwrite": "覆盖",
        "dialog_cancel": "取消",
        "translation_dialog_title": "SRT 字幕翻译",
        "translation_intro": "本地翻译已有 SRT 文件，复用当前 Python/CUDA 环境。",
        "translation_source": "SRT 文件",
        "translation_source_placeholder": "选择要翻译的 .srt 文件",
        "translation_browse": "选择 SRT",
        "translation_browse_tooltip": "选择已有 SRT 字幕文件",
        "translation_target": "目标语言",
        "translation_target_tooltip": "选择常用语言，或直接输入其他目标语言",
        "translation_model_mode": "模型模式",
        "translation_model_mode_tooltip": "质量优先使用官方模型，快速模式使用轻量模型",
        "translation_output": "输出文件",
        "translation_output_placeholder": "自动生成输出路径",
        "translation_start": "开始翻译",
        "translation_start_tooltip": "使用本地模型翻译 SRT 文件",
        "translation_ready": "准备翻译",
        "translation_loading": "正在加载翻译模型",
        "translation_stopping": "正在停止翻译",
        "translation_done": "翻译完成",
        "translation_failed": "翻译失败：{message}",
        "translation_select_srt_title": "选择 SRT 文件",
        "translation_missing_source_title": "缺少 SRT 文件",
        "translation_missing_source_body": "请先选择要翻译的 SRT 文件。",
        "translation_model_quality": "质量优先",
        "translation_model_fast": "快速轻量",
        "translation_target_zh": "简体中文",
        "translation_target_zh_hant": "繁體中文",
        "translation_target_en": "英语",
        "translation_target_ja": "日语",
        "translation_target_ko": "韩语",
        "translation_target_fr": "法语",
        "translation_target_de": "德语",
        "translation_target_es": "西班牙语",
        "translation_target_pt": "葡萄牙语",
        "translation_target_ru": "俄语",
        "translation_target_ar": "阿拉伯语",
        "file_status_waiting": "等待",
        "file_status_processing": "处理中",
        "file_status_done": "完成",
        "file_status_failed": "失败，详见日志",
        "file_status_cancelled": "已取消",
        "file_status_model_failed": "模型加载失败",
        "asr_auto": "自动识别",
        "asr_chinese": "中文",
        "asr_english": "英语",
        "asr_japanese": "日语",
        "asr_korean": "韩语",
        "asr_cantonese": "粤语",
        "asr_spanish": "西班牙语",
        "asr_french": "法语",
        "asr_german": "德语",
        "asr_portuguese": "葡萄牙语",
        "asr_russian": "俄语",
        "asr_italian": "意大利语",
        "asr_thai": "泰语",
        "asr_vietnamese": "越南语",
        "log_prepare_model": "正在准备识别模型...",
        "log_cached_audio": "正在使用已缓存的音频。",
        "log_audio_ready": "音频准备完成。",
        "log_asr_start": "开始识别字幕。",
        "log_done": "处理结束。",
        "log_start": "开始处理。",
        "log_subtitle_done": "字幕生成完成。",
        "log_stop_requested": "已请求停止处理",
        "log_cancelled": "已取消：{message}",
        "log_error": "错误：{message}",
        "log_prepare_models_download": "[INFO] 正在准备模型；首次运行会下载模型，耗时取决于网络和硬盘。",
        "log_audio_extract_wav": "[AUDIO] 提取 16k 单声道 WAV：{name}",
        "log_extract_audio": "正在提取音频：{percent}%",
        "log_recognize": "正在识别字幕：{percent}%",
        "log_translate": "正在翻译字幕：{percent}%",
        "log_asr_audio_chunks": "[ASR] 音频时长约 {minutes} 分钟，分为 {total} 个识别块",
        "log_asr_chunk_started": "[ASR] {index}/{total} 开始：{start}-{end} 分钟",
        "log_asr_chunk_completed": "[ASR] {index}/{total} 完成，用时 {seconds}s，总进度 {percent}%",
        "log_asr_missing_timestamps": "[ASR] {index}/{total} 无时间戳，使用该识别块时间范围生成粗略字幕",
        "log_asr_empty_text": "[ASR] {index}/{total} 无识别文本，跳过字幕生成",
        "progress_cached_audio": "使用缓存音频",
        "progress_audio_ready": "音频准备完成",
        "progress_prepare_asr": "准备识别",
        "progress_done": "完成",
        "progress_asr_done": "识别完成",
        "progress_translate": "翻译字幕",
        "progress_extract_audio": "提取音频 {percent}%",
        "progress_recognize": "识别字幕 {percent}%",
        "progress_translate_percent": "翻译字幕 {percent}%",
        "progress_model_failed": "模型加载失败",
        "progress_cancel_remaining": "已取消后续任务",
        "progress_cancelled": "已取消处理",
        "progress_processing_file": "正在处理 {index}/{total}: {name}",
        "progress_done_count": "已完成 {index}/{total}",
    },
    "zh-Hant": {
        "product_name": "AI 大模型字幕助手",
        "product_subtitle": "大模型 ASR 驅動 · 多語言辨識 · 精準時間對齊",
        "ui_language_tooltip": "切換介面語言",
        "add_files": "新增檔案",
        "translate_srt": "翻譯字幕",
        "translate_srt_tooltip": "開啟本地 SRT 翻譯工具，支援多目標語言",
        "start": "開始處理",
        "start_translate": "辨識並翻譯",
        "start_translate_tooltip": "辨識字幕後翻譯為輸出語言，同時保留原始字幕",
        "stop": "停止",
        "open_output_folder": "開啟輸出資料夾",
        "clear_queue": "清空佇列",
        "remove_selected": "移除選取",
        "clear_completed": "清除已完成",
        "retry_failed": "重試失敗",
        "queue_title": "檔案佇列",
        "empty_title": "尚未新增檔案",
        "empty_hint": "點擊「新增檔案」選擇多個媒體檔，或直接把檔案拖入視窗。",
        "table_file": "檔案",
        "table_status": "狀態",
        "table_subtitle_dir": "字幕目錄",
        "settings_title": "常用設定",
        "advanced_settings": "進階設定",
        "advanced_tooltip": "裝置、音訊分塊等不常調整的選項",
        "context_label": "上下文",
        "context_placeholder": "可選：片名、角色名、人名、地名；不確定時留空",
        "context_tooltip": "提供片名或角色名可幫助模型辨識專有名詞，不確定時留空",
        "recognition_language": "辨識語言",
        "recognition_language_tooltip": "預設自動辨識；明確知道音訊語言時可手動指定",
        "output_language": "輸出語言",
        "output_language_tooltip": "點選「辨識並翻譯」時生成的目標字幕語言",
        "profile_label": "執行模式",
        "profile_tooltip": "推薦適合大多數情況，低顯存會使用更保守的參數",
        "model_size": "模型尺寸",
        "model_size_tooltip": "1.7B 品質更好；0.6B 更省顯存、速度更快",
        "profile_recommended": "推薦",
        "profile_low_vram": "低顯存",
        "profile_cpu_slow": "CPU 慢速",
        "advanced_hint": "裝置、音訊分塊和字幕樣式屬於低頻選項，通常保持預設即可。",
        "device": "裝置",
        "device_auto": "自動",
        "device_gpu": "優先 GPU",
        "device_cpu": "CPU",
        "device_tooltip": "一般保持自動；只有排查問題時再手動指定裝置",
        "audio_chunk": "音訊分塊",
        "chunk_safe": "穩妥（30 秒）",
        "chunk_recommended": "推薦（45 秒）",
        "chunk_long": "長分塊（60 秒）",
        "chunk_tooltip": "只提供常用預設，避免無意義的秒級微調",
        "caption_style": "字幕樣式",
        "caption_short": "短句",
        "caption_recommended": "推薦",
        "caption_long": "較長",
        "caption_tooltip": "控制字幕換行傾向；推薦適合大多數電影對白",
        "overwrite": "覆蓋已有輸出",
        "overwrite_tooltip": "未勾選時如字幕已存在，會在開始處理前詢問是否覆蓋",
        "local_only": "只使用本機模型快取",
        "local_only_tooltip": "勾選後不會下載缺失模型",
        "close": "關閉",
        "status_ready": "準備就緒",
        "status_add_files": "請先新增檔案",
        "status_ready_with_files": "已新增 {count} 個檔案，可以開始處理",
        "status_kept_failed": "已保留 {count} 個失敗檔案，可重新開始處理",
        "status_processing": "處理中",
        "status_loading_model": "正在載入模型，首次執行可能需要下載模型",
        "status_cancelled": "已取消",
        "status_summary": "完成 {success} 個，失敗 {failed} 個，取消 {cancelled} 個",
        "status_done_with_failed": "處理完成，有失敗",
        "status_failed_detail": "{failed} 個檔案失敗，詳情見執行日誌",
        "status_done": "處理完成",
        "status_open_output": "可以開啟輸出資料夾查看字幕",
        "status_stopping": "正在停止，當前步驟結束後會退出",
        "log_title": "執行日誌",
        "show_technical_log": "顯示技術日誌",
        "show_technical_log_tooltip": "預設只顯示普通提示，勾選後查看完整技術日誌",
        "clear_log": "清空日誌",
        "clear_log_tooltip": "清空目前執行日誌",
        "log_placeholder": "處理日誌會顯示在這裡。",
        "select_media_files": "選擇媒體檔案",
        "media_files_filter": "媒體檔案 ({extensions});;所有檔案 (*)",
        "msg_no_media_title": "沒有可處理檔案",
        "msg_no_media_body": "沒有找到支援的影片或音訊檔案。",
        "msg_no_failed_title": "沒有失敗檔案",
        "msg_no_failed_body": "目前佇列裡沒有失敗檔案。",
        "msg_no_files_title": "沒有檔案",
        "msg_no_files_body": "請先新增要處理的媒體檔案。",
        "msg_diagnostics_failed": "環境檢查未通過",
        "msg_output_exists": "輸出已存在",
        "msg_output_exists_body": "以下字幕檔案已存在，是否覆蓋？\n{preview}",
        "msg_more_files": "另外 {count} 個檔案",
        "msg_finished_title": "處理結束",
        "msg_finished_body": "成功：{success}\n失敗：{failed}\n取消：{cancelled}\n可在佇列中選擇檔案後開啟輸出資料夾。",
        "msg_no_dir_title": "沒有目錄",
        "msg_no_dir_body": "請先新增檔案。",
        "msg_running_title": "正在處理",
        "msg_running_body": "目前任務還在執行。請先點擊「停止」，等待當前步驟結束後再關閉。",
        "dialog_ok": "確定",
        "dialog_overwrite": "覆蓋",
        "dialog_cancel": "取消",
        "translation_dialog_title": "SRT 字幕翻譯",
        "translation_intro": "本地翻譯已有 SRT 檔案，復用目前 Python/CUDA 環境。",
        "translation_source": "SRT 檔案",
        "translation_source_placeholder": "選擇要翻譯的 .srt 檔案",
        "translation_browse": "選擇 SRT",
        "translation_browse_tooltip": "選擇已有 SRT 字幕檔案",
        "translation_target": "目標語言",
        "translation_target_tooltip": "選擇常用語言，或直接輸入其他目標語言",
        "translation_model_mode": "模型模式",
        "translation_model_mode_tooltip": "品質優先使用官方模型，快速模式使用輕量模型",
        "translation_output": "輸出檔案",
        "translation_output_placeholder": "自動生成輸出路徑",
        "translation_start": "開始翻譯",
        "translation_start_tooltip": "使用本地模型翻譯 SRT 檔案",
        "translation_ready": "準備翻譯",
        "translation_loading": "正在載入翻譯模型",
        "translation_stopping": "正在停止翻譯",
        "translation_done": "翻譯完成",
        "translation_failed": "翻譯失敗：{message}",
        "translation_select_srt_title": "選擇 SRT 檔案",
        "translation_missing_source_title": "缺少 SRT 檔案",
        "translation_missing_source_body": "請先選擇要翻譯的 SRT 檔案。",
        "translation_model_quality": "品質優先",
        "translation_model_fast": "快速輕量",
        "translation_target_zh": "簡體中文",
        "translation_target_zh_hant": "繁體中文",
        "translation_target_en": "英語",
        "translation_target_ja": "日語",
        "translation_target_ko": "韓語",
        "translation_target_fr": "法語",
        "translation_target_de": "德語",
        "translation_target_es": "西班牙語",
        "translation_target_pt": "葡萄牙語",
        "translation_target_ru": "俄語",
        "translation_target_ar": "阿拉伯語",
        "file_status_waiting": "等待",
        "file_status_processing": "處理中",
        "file_status_done": "完成",
        "file_status_failed": "失敗，詳見日誌",
        "file_status_cancelled": "已取消",
        "file_status_model_failed": "模型載入失敗",
        "asr_auto": "自動辨識",
        "asr_chinese": "中文",
        "asr_english": "英語",
        "asr_japanese": "日語",
        "asr_korean": "韓語",
        "asr_cantonese": "粵語",
        "asr_spanish": "西班牙語",
        "asr_french": "法語",
        "asr_german": "德語",
        "asr_portuguese": "葡萄牙語",
        "asr_russian": "俄語",
        "asr_italian": "義大利語",
        "asr_thai": "泰語",
        "asr_vietnamese": "越南語",
        "log_prepare_model": "正在準備辨識模型...",
        "log_cached_audio": "正在使用已快取的音訊。",
        "log_audio_ready": "音訊準備完成。",
        "log_asr_start": "開始辨識字幕。",
        "log_done": "處理結束。",
        "log_start": "開始處理。",
        "log_subtitle_done": "字幕生成完成。",
        "log_stop_requested": "已請求停止處理",
        "log_cancelled": "已取消：{message}",
        "log_error": "錯誤：{message}",
        "log_prepare_models_download": "[INFO] 正在準備模型；首次執行會下載模型，耗時取決於網路和硬碟。",
        "log_audio_extract_wav": "[AUDIO] 提取 16k 單聲道 WAV：{name}",
        "log_extract_audio": "正在提取音訊：{percent}%",
        "log_recognize": "正在辨識字幕：{percent}%",
        "log_translate": "正在翻譯字幕：{percent}%",
        "log_asr_audio_chunks": "[ASR] 音訊時長約 {minutes} 分鐘，分為 {total} 個辨識塊",
        "log_asr_chunk_started": "[ASR] {index}/{total} 開始：{start}-{end} 分鐘",
        "log_asr_chunk_completed": "[ASR] {index}/{total} 完成，用時 {seconds}s，總進度 {percent}%",
        "log_asr_missing_timestamps": "[ASR] {index}/{total} 無時間戳，使用該辨識塊時間範圍生成粗略字幕",
        "log_asr_empty_text": "[ASR] {index}/{total} 無辨識文本，跳過字幕生成",
        "progress_cached_audio": "使用快取音訊",
        "progress_audio_ready": "音訊準備完成",
        "progress_prepare_asr": "準備辨識",
        "progress_done": "完成",
        "progress_asr_done": "辨識完成",
        "progress_translate": "翻譯字幕",
        "progress_extract_audio": "提取音訊 {percent}%",
        "progress_recognize": "辨識字幕 {percent}%",
        "progress_translate_percent": "翻譯字幕 {percent}%",
        "progress_model_failed": "模型載入失敗",
        "progress_cancel_remaining": "已取消後續任務",
        "progress_cancelled": "已取消處理",
        "progress_processing_file": "正在處理 {index}/{total}: {name}",
        "progress_done_count": "已完成 {index}/{total}",
    },
    "en": {
        "product_name": "AI Subtitle Assistant",
        "product_subtitle": "ASR powered · Multilingual recognition · Precise time alignment",
        "ui_language_tooltip": "Switch interface language",
        "add_files": "Add Files",
        "translate_srt": "Translate SRT",
        "translate_srt_tooltip": "Open local SRT translation with multi-language targets",
        "start": "Start",
        "start_translate": "Recognize + Translate",
        "start_translate_tooltip": "Recognize subtitles, translate to the output language, and keep the original subtitles",
        "stop": "Stop",
        "open_output_folder": "Open Subtitle Folder",
        "clear_queue": "Clear Queue",
        "remove_selected": "Remove Selected",
        "clear_completed": "Clear Completed",
        "retry_failed": "Retry Failed",
        "queue_title": "File Queue",
        "empty_title": "No files added",
        "empty_hint": "Click \"Add Files\" to select media files, or drag files into this window.",
        "table_file": "File",
        "table_status": "Status",
        "table_subtitle_dir": "Subtitle Folder",
        "settings_title": "Common Settings",
        "advanced_settings": "Advanced Settings",
        "advanced_tooltip": "Device, audio chunking, and other low-frequency options",
        "context_label": "Context",
        "context_placeholder": "Optional: title, character names, people, places; leave blank if unsure",
        "context_tooltip": "Add names or terms to help recognition; leave blank if unsure",
        "recognition_language": "Language",
        "recognition_language_tooltip": "Keep Auto by default; choose a language when you know it",
        "output_language": "Output language",
        "output_language_tooltip": "Target subtitle language used by Recognize & Translate",
        "profile_label": "Mode",
        "profile_tooltip": "Recommended fits most cases; low VRAM uses safer settings",
        "model_size": "Model Size",
        "model_size_tooltip": "1.7B gives better quality; 0.6B is faster and uses less VRAM",
        "profile_recommended": "Balanced",
        "profile_low_vram": "Low VRAM",
        "profile_cpu_slow": "CPU Slow",
        "advanced_hint": "Device, audio chunking, and subtitle style are low-frequency options. Defaults usually work.",
        "device": "Device",
        "device_auto": "Auto",
        "device_gpu": "Prefer GPU",
        "device_cpu": "CPU",
        "device_tooltip": "Usually keep Auto; only change this when troubleshooting",
        "audio_chunk": "Audio Chunk",
        "chunk_safe": "Stable (30s)",
        "chunk_recommended": "Recommended (45s)",
        "chunk_long": "Long Chunk (60s)",
        "chunk_tooltip": "Common presets only, no second-by-second tuning",
        "caption_style": "Subtitle Style",
        "caption_short": "Short",
        "caption_recommended": "Recommended",
        "caption_long": "Longer",
        "caption_tooltip": "Controls line wrapping; Recommended fits most dialogue",
        "overwrite": "Overwrite existing output",
        "overwrite_tooltip": "When off, the app asks before overwriting existing subtitles",
        "local_only": "Use local model cache only",
        "local_only_tooltip": "When on, missing models will not be downloaded",
        "close": "Close",
        "status_ready": "Ready",
        "status_add_files": "Add files to begin",
        "status_ready_with_files": "{count} file(s) added. Ready to start.",
        "status_kept_failed": "Kept {count} failed file(s). Ready to retry.",
        "status_processing": "Processing",
        "status_loading_model": "Loading models. First run may need to download them.",
        "status_cancelled": "Cancelled",
        "status_summary": "Done {success}, failed {failed}, cancelled {cancelled}",
        "status_done_with_failed": "Completed with failures",
        "status_failed_detail": "{failed} file(s) failed. See the log for details.",
        "status_done": "Completed",
        "status_open_output": "Open the subtitle folder to view results",
        "status_stopping": "Stopping after the current step finishes",
        "log_title": "Run Log",
        "show_technical_log": "Show technical log",
        "show_technical_log_tooltip": "Show user-friendly messages by default; enable for full technical log",
        "clear_log": "Clear Log",
        "clear_log_tooltip": "Clear the current run log",
        "log_placeholder": "Processing logs will appear here.",
        "select_media_files": "Select Media Files",
        "media_files_filter": "Media files ({extensions});;All files (*)",
        "msg_no_media_title": "No supported files",
        "msg_no_media_body": "No supported video or audio files were found.",
        "msg_no_failed_title": "No failed files",
        "msg_no_failed_body": "There are no failed files in the queue.",
        "msg_no_files_title": "No files",
        "msg_no_files_body": "Add media files before processing.",
        "msg_diagnostics_failed": "Environment check failed",
        "msg_output_exists": "Output already exists",
        "msg_output_exists_body": "These subtitle files already exist. Overwrite them?\n{preview}",
        "msg_more_files": "{count} more file(s)",
        "msg_finished_title": "Processing finished",
        "msg_finished_body": "Success: {success}\nFailed: {failed}\nCancelled: {cancelled}\nSelect a file in the queue to open its subtitle folder.",
        "msg_no_dir_title": "No folder",
        "msg_no_dir_body": "Add a file first.",
        "msg_running_title": "Processing",
        "msg_running_body": "A task is still running. Click Stop first, then wait for the current step to finish.",
        "dialog_ok": "OK",
        "dialog_overwrite": "Overwrite",
        "dialog_cancel": "Cancel",
        "translation_dialog_title": "SRT Translation",
        "translation_intro": "Translate SRT files locally and reuse the current Python/CUDA environment.",
        "translation_source": "SRT file",
        "translation_source_placeholder": "Choose the .srt file to translate",
        "translation_browse": "Choose SRT",
        "translation_browse_tooltip": "Choose an existing SRT subtitle file",
        "translation_target": "Target language",
        "translation_target_tooltip": "Choose a common language, or type another target language",
        "translation_model_mode": "Model mode",
        "translation_model_mode_tooltip": "Quality uses the official model; fast uses the lightweight model",
        "translation_output": "Output file",
        "translation_output_placeholder": "Output path is generated automatically",
        "translation_start": "Start Translation",
        "translation_start_tooltip": "Translate the SRT file with a local model",
        "translation_ready": "Ready to translate",
        "translation_loading": "Loading translation model",
        "translation_stopping": "Stopping translation",
        "translation_done": "Translation complete",
        "translation_failed": "Translation failed: {message}",
        "translation_select_srt_title": "Choose SRT File",
        "translation_missing_source_title": "Missing SRT file",
        "translation_missing_source_body": "Choose the SRT file to translate first.",
        "translation_model_quality": "Quality",
        "translation_model_fast": "Fast",
        "translation_target_zh": "Simplified Chinese",
        "translation_target_zh_hant": "Traditional Chinese",
        "translation_target_en": "English",
        "translation_target_ja": "Japanese",
        "translation_target_ko": "Korean",
        "translation_target_fr": "French",
        "translation_target_de": "German",
        "translation_target_es": "Spanish",
        "translation_target_pt": "Portuguese",
        "translation_target_ru": "Russian",
        "translation_target_ar": "Arabic",
        "file_status_waiting": "Waiting",
        "file_status_processing": "Processing",
        "file_status_done": "Done",
        "file_status_failed": "Failed, see log",
        "file_status_cancelled": "Cancelled",
        "file_status_model_failed": "Model load failed",
        "asr_auto": "Auto",
        "asr_chinese": "Chinese",
        "asr_english": "English",
        "asr_japanese": "Japanese",
        "asr_korean": "Korean",
        "asr_cantonese": "Cantonese",
        "asr_spanish": "Spanish",
        "asr_french": "French",
        "asr_german": "German",
        "asr_portuguese": "Portuguese",
        "asr_russian": "Russian",
        "asr_italian": "Italian",
        "asr_thai": "Thai",
        "asr_vietnamese": "Vietnamese",
        "log_prepare_model": "Preparing recognition model...",
        "log_cached_audio": "Using cached audio.",
        "log_audio_ready": "Audio is ready.",
        "log_asr_start": "Starting subtitle recognition.",
        "log_done": "Processing finished.",
        "log_start": "Processing started.",
        "log_subtitle_done": "Subtitle generated.",
        "log_stop_requested": "Stop requested",
        "log_cancelled": "Cancelled: {message}",
        "log_error": "Error: {message}",
        "log_prepare_models_download": "[INFO] Preparing models. First run may download models; time depends on network and disk speed.",
        "log_audio_extract_wav": "[AUDIO] Extracting 16k mono WAV: {name}",
        "log_extract_audio": "Extracting audio: {percent}%",
        "log_recognize": "Recognizing subtitles: {percent}%",
        "log_translate": "Translating subtitles: {percent}%",
        "log_asr_audio_chunks": "[ASR] Audio duration about {minutes} min; split into {total} recognition chunks",
        "log_asr_chunk_started": "[ASR] {index}/{total} started: {start}-{end} min",
        "log_asr_chunk_completed": "[ASR] {index}/{total} completed in {seconds}s; overall progress {percent}%",
        "log_asr_missing_timestamps": "[ASR] {index}/{total} has no timestamps; using the chunk time range for rough subtitles",
        "log_asr_empty_text": "[ASR] {index}/{total} has no recognized text; skipping subtitle generation",
        "progress_cached_audio": "Using cached audio",
        "progress_audio_ready": "Audio ready",
        "progress_prepare_asr": "Preparing recognition",
        "progress_done": "Done",
        "progress_asr_done": "Recognition complete",
        "progress_translate": "Translating subtitles",
        "progress_extract_audio": "Extracting audio {percent}%",
        "progress_recognize": "Recognizing subtitles {percent}%",
        "progress_translate_percent": "Translating subtitles {percent}%",
        "progress_model_failed": "Model load failed",
        "progress_cancel_remaining": "Cancelled remaining tasks",
        "progress_cancelled": "Processing cancelled",
        "progress_processing_file": "Processing {index}/{total}: {name}",
        "progress_done_count": "Finished {index}/{total}",
    },
}

AUDIO_PROGRESS_RE = re.compile(r"^\[AUDIO\]\s+(\d+)%")
ASR_PROGRESS_RE = re.compile(r"总进度\s+(\d+)%")
MODEL_DOWNLOAD_INFO_RE = re.compile(r"^\[INFO\]\s*正在准备模型；首次运行会下载模型，耗时取决于网络和硬盘。$")
AUDIO_EXTRACT_WAV_RE = re.compile(r"^\[AUDIO\]\s*提取 16k 单声道 WAV:\s*(.+)$")
ASR_AUDIO_CHUNKS_RE = re.compile(r"^\[ASR\]\s*音频时长约\s*([0-9.]+)\s*分钟，分为\s*(\d+)\s*个识别块")
ASR_CHUNK_STARTED_RE = re.compile(r"^\[ASR\]\s*(\d+)/(\d+)\s*开始\s*([0-9.]+)-([0-9.]+)\s*分钟")
ASR_CHUNK_COMPLETED_RE = re.compile(r"^\[ASR\]\s*(\d+)/(\d+)\s*完成，用时\s*([0-9.]+)s，总进度\s*(\d+)%")
ASR_MISSING_TIMESTAMPS_RE = re.compile(r"^\[ASR\]\s*(\d+)/(\d+)\s*无时间戳，使用该识别块时间范围生成粗略字幕")
ASR_EMPTY_TEXT_RE = re.compile(r"^\[ASR\]\s*(\d+)/(\d+)\s*无识别文本，跳过字幕生成")
ERROR_DETAIL_TEXT = {
    "没有找到或无法使用 FFmpeg。请先安装 FFmpeg，并确认 ffmpeg 和 ffprobe 可以在命令行中直接运行。": {
        "zh-Hant": "沒有找到或無法使用 FFmpeg。請先安裝 FFmpeg，並確認 ffmpeg 和 ffprobe 可以在命令列中直接執行。",
        "en": "FFmpeg is missing or unavailable. Install FFmpeg and make sure ffmpeg and ffprobe can run from the command line.",
    },
    "没有找到 ffprobe。请检查 FFmpeg 是否完整安装，并确认它在 PATH 中。": {
        "zh-Hant": "沒有找到 ffprobe。請檢查 FFmpeg 是否完整安裝，並確認它在 PATH 中。",
        "en": "ffprobe was not found. Check that FFmpeg is fully installed and available in PATH.",
    },
    "没有检测到 CUDA。可以改用 CPU 慢速模式，或安装 CUDA 版 PyTorch 后重试。": {
        "zh-Hant": "沒有偵測到 CUDA。可以改用 CPU 慢速模式，或安裝 CUDA 版 PyTorch 後重試。",
        "en": "CUDA was not detected. Use CPU Slow mode, or install the CUDA build of PyTorch and retry.",
    },
    "显存不足。建议使用“低显存”运行模式，或切换到 0.6B 模型后重试。": {
        "zh-Hant": "顯存不足。建議使用「低顯存」執行模式，或切換到 0.6B 模型後重試。",
        "en": "Not enough VRAM. Use Low VRAM mode, or switch to the 0.6B model and retry.",
    },
    "本地没有找到模型文件。请取消“只使用本地模型缓存”，或先把模型下载到本地。": {
        "zh-Hant": "本機沒有找到模型檔案。請取消「只使用本機模型快取」，或先把模型下載到本機。",
        "en": "Local model files were not found. Turn off \"Use local model cache only\", or download the models first.",
    },
    "没有写入权限。请换一个输出目录，或确认当前目录允许写入。": {
        "zh-Hant": "沒有寫入權限。請換一個輸出目錄，或確認目前目錄允許寫入。",
        "en": "No write permission. Choose another subtitle folder, or make sure the current folder is writable.",
    },
    "磁盘空间不足。请清理空间后重试，模型缓存和临时音频都会占用较多空间。": {
        "zh-Hant": "磁碟空間不足。請清理空間後重試，模型快取和臨時音訊都會占用較多空間。",
        "en": "Not enough disk space. Free up space and retry. Model cache and temporary audio can use significant storage.",
    },
}


def tr(language: str, key: str, **values: object) -> str:
    bundle = TEXT.get(language, TEXT[DEFAULT_UI_LANGUAGE])
    text = bundle.get(key, TEXT[DEFAULT_UI_LANGUAGE].get(key, key))
    return text.format(**values)


def format_diagnostics_for_ui(results: list[object], language: str) -> str:
    labels = {
        "ok": "OK",
        "warn": "WARN",
        "error": "ERROR",
        "info": "INFO",
    }
    lines = []
    for result in results:
        status = getattr(result, "status", "info")
        message = getattr(result, "message", "")
        lines.append(f"[{labels.get(status, str(status).upper())}] {_diagnostic_message(result, language)}")
    return "\n".join(lines)


def _diagnostic_message(result: object, language: str) -> str:
    name = getattr(result, "name", "")
    status = getattr(result, "status", "")
    message = getattr(result, "message", "")
    if language == "zh-Hans":
        return message

    if name in {"ffmpeg", "ffprobe"}:
        label = "FFmpeg" if name == "ffmpeg" else "ffprobe"
        if status == "ok":
            path = _suffix_after(message, ": ")
            if language == "zh-Hant":
                return f"{label} 可用：{path}"
            return f"{label} is available: {path}"
        if language == "zh-Hant":
            return f"沒有找到 {label}，請先安裝 FFmpeg 並確認 {name} 在 PATH 中。"
        return f"{label} was not found. Install FFmpeg and make sure {name} is in PATH."

    if name == "torch":
        error = _suffix_after(message, ": ")
        if language == "zh-Hant":
            return f"PyTorch 無法匯入：{error}"
        return f"PyTorch could not be imported: {error}"

    if name == "cuda":
        version_match = re.search(r"PyTorch\s+([^，,]+)", message)
        version = version_match.group(1) if version_match else "unknown"
        if status == "ok":
            device = _suffix_after(message, ": ")
            if language == "zh-Hant":
                return f"PyTorch {version}，CUDA 可用：{device}"
            return f"PyTorch {version}. CUDA available: {device}"
        if language == "zh-Hant":
            return f"PyTorch {version}，沒有偵測到 CUDA；可以執行 CPU 模式，但會很慢。"
        return f"PyTorch {version}. CUDA was not detected; CPU mode is available but slow."

    if name == "output":
        path = _suffix_after(message, ": ")
        if "上级目录不存在" in message:
            return f"輸出目錄的上層目錄不存在：{path}" if language == "zh-Hant" else f"Parent folder does not exist: {path}"
        if "上级路径不是目录" in message:
            return f"輸出目錄的上層路徑不是資料夾：{path}" if language == "zh-Hant" else f"Parent path is not a folder: {path}"
        if "不可写" in message:
            return f"輸出目錄不可寫入：{path}" if language == "zh-Hant" else f"Subtitle folder is not writable: {path}"
        return f"輸出目錄可寫：{path}" if language == "zh-Hant" else f"Subtitle folder is writable: {path}"

    if name == "cache":
        path = _suffix_after(message, ": ")
        if status == "ok":
            return f"模型快取目錄：{path}" if language == "zh-Hant" else f"Model cache folder: {path}"
        if language == "zh-Hant":
            return f"模型快取目錄尚不存在，首次執行會建立並下載模型：{path}"
        return f"Model cache folder does not exist yet. It will be created on first run: {path}"

    return message


def _suffix_after(text: str, separator: str) -> str:
    return text.rsplit(separator, 1)[-1] if separator in text else text


def user_log_text(message: str, language: str) -> str | None:
    if message.startswith("[LOAD] ASR"):
        return tr(language, "log_prepare_model")
    if message.startswith("[LOAD]"):
        return None
    if "[AUDIO] 使用缓存音频" in message:
        return tr(language, "log_cached_audio")
    if "[AUDIO] 完成" in message:
        return tr(language, "log_audio_ready")
    if "[ASR local]" in message:
        return tr(language, "log_asr_start")
    if message.startswith("[OK]"):
        return tr(language, "log_subtitle_done")
    if message.startswith("[DONE]"):
        return tr(language, "log_done")
    if message.startswith("[START]"):
        return tr(language, "log_start")
    if message.startswith("[CANCEL]"):
        return tr(language, "log_cancelled", message=_localized_log_detail(message.replace("[CANCEL]", "", 1), language))
    if message.startswith("[ERROR]"):
        return tr(language, "log_error", message=_localized_log_detail(message.replace("[ERROR]", "", 1), language))

    audio_match = AUDIO_PROGRESS_RE.search(message)
    if audio_match:
        return tr(language, "log_extract_audio", percent=audio_match.group(1))

    if message.startswith("[TRANSLATE]"):
        translate_match = ASR_PROGRESS_RE.search(message)
        if translate_match:
            return tr(language, "log_translate", percent=translate_match.group(1))

    asr_match = ASR_PROGRESS_RE.search(message)
    if asr_match:
        return tr(language, "log_recognize", percent=asr_match.group(1))

    return None


def technical_log_text(message: str, language: str) -> str | None:
    detailed = _localized_technical_log_detail(message, language)
    if detailed:
        return detailed

    friendly = user_log_text(message, language)
    if friendly:
        return friendly

    return message


def _localized_technical_log_detail(message: str, language: str) -> str | None:
    if MODEL_DOWNLOAD_INFO_RE.search(message):
        return tr(language, "log_prepare_models_download")

    audio_extract_match = AUDIO_EXTRACT_WAV_RE.search(message)
    if audio_extract_match:
        return tr(language, "log_audio_extract_wav", name=audio_extract_match.group(1))

    audio_chunks_match = ASR_AUDIO_CHUNKS_RE.search(message)
    if audio_chunks_match:
        minutes, total = audio_chunks_match.groups()
        return tr(language, "log_asr_audio_chunks", minutes=minutes, total=total)

    chunk_completed_match = ASR_CHUNK_COMPLETED_RE.search(message)
    if chunk_completed_match:
        index, total, seconds, percent = chunk_completed_match.groups()
        return tr(
            language,
            "log_asr_chunk_completed",
            index=index,
            total=total,
            seconds=seconds,
            percent=percent,
        )

    chunk_started_match = ASR_CHUNK_STARTED_RE.search(message)
    if chunk_started_match:
        index, total, start, end = chunk_started_match.groups()
        return tr(
            language,
            "log_asr_chunk_started",
            index=index,
            total=total,
            start=start,
            end=end,
        )

    missing_timestamps_match = ASR_MISSING_TIMESTAMPS_RE.search(message)
    if missing_timestamps_match:
        index, total = missing_timestamps_match.groups()
        return tr(language, "log_asr_missing_timestamps", index=index, total=total)

    empty_text_match = ASR_EMPTY_TEXT_RE.search(message)
    if empty_text_match:
        index, total = empty_text_match.groups()
        return tr(language, "log_asr_empty_text", index=index, total=total)

    if message.startswith("[LOAD]"):
        return message

    return None


def _localized_log_detail(detail: str, language: str) -> str:
    detail = detail.strip()
    prefix, separator, tail = detail.partition(": ")
    if separator:
        localized_tail = _localized_log_detail(tail, language)
        if localized_tail != tail:
            if prefix == "模型加载失败":
                prefix = tr(language, "progress_model_failed")
            return f"{prefix}: {localized_tail}"
    if detail == "已请求停止处理":
        return tr(language, "log_stop_requested")
    if detail == "模型加载失败":
        return tr(language, "progress_model_failed")
    if detail.startswith("模型加载失败:"):
        return detail.replace("模型加载失败", tr(language, "progress_model_failed"), 1)
    localized = ERROR_DETAIL_TEXT.get(detail, {}).get(language)
    if localized:
        return localized
    return detail
