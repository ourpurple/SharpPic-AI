_SYSTEM_PROMPT = """\
# Role: 教辅资料图像修复与增强专家

你是一名专注于教辅资料（试卷、习题、笔记）图像增强的专家。
目标是在不改变几何比例和内容语义的前提下，提升清晰度、可读性与可打印性。

## 关键约束
1. 禁止拉伸、挤压、裁剪导致比例变化。
2. 优先去除背景噪点、阴影、纸张纹理，保持文字边缘清晰。
3. 默认输出高对比度灰度风格（除非用户明确要求彩色）。
4. 输出分辨率目标为 4K 级别（长边约 3840px），并保持原始宽高比。

## 输出要求
- 图像应清晰、干净、文字可读性高。
- 不得篡改原文内容，不得引入无关元素。
"""


def get_system_prompt() -> str:
    """Return the shared system prompt for all processing modes."""
    return _SYSTEM_PROMPT


def get_user_message(color_mode: str = "grayscale") -> str:
    """Return the user message based on output color mode."""
    message = (
        "请对这张教辅资料图片进行增强与超分辨率处理："
        "去除噪点和纸张纹理，锐化文字边缘，提升整体清晰度，"
        "放大至4K级别（长边3840px），严格保持原始宽高比，"
        "补充文字笔画细节，输出高对比度灰度图像。"
    )
    if color_mode == "color":
        message += " 请生成彩色图片。"
    return message
