import re

# 导入 AstrBot 核心 API
from astrbot.api import logger, AstrBotConfig
from astrbot.api.star import Context, Star, register
from astrbot.api.event import AstrMessageEvent, filter
import astrbot.api.message_components as Comp

@register(
    "final_reply_trimmer",
    "最终回复裁剪插件",
    "一个简单的正则插件，作为最后防线，移除 '最终的罗莎回复：' 及其之前的所有内容。",
    "1.0.0",
)
class FinalReplyTrimmer(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        # 为了效率，预先编译正则表达式
        # 这个正则会匹配 "最终的罗莎回复" + 一个可选的中文或英文冒号 + 任意数量的空格
        self.FINAL_REPLY_PATTERN = re.compile(r"最终的罗莎回复[:：]?\s*", re.IGNORECASE)
        logger.info("[FinalReplyTrimmer] 最终保险丝插件已加载。")

    @filter.on_decorating_result(priority=200)
    async def trim_final_reply(self, event: AstrMessageEvent, *args, **kwargs):
        """在消息发送前的最后一刻进行检查和裁剪"""
        result = event.get_result()
        # 确保有结果且结果消息不为空
        if not result or not result.result_message:
            return

        # 获取准备发送的纯文本内容
        plain_text = result.get_plain_text()

        # 检查文本中是否包含我们需要处理的模式
        if not self.FINAL_REPLY_PATTERN.search(plain_text):
            return # 如果不包含，就什么都不做，直接返回

        # --- 核心逻辑 ---
        # 使用 re.split() 来分割字符串。这个方法会返回一个列表。
        # 例如，"OS...最终回复: ABC" 会被分割成 ["OS...", "ABC"]
        # 我们只需要取列表的最后一个元素，就是我们想要的干净文本。
        parts = self.FINAL_REPLY_PATTERN.split(plain_text)
        clean_text = parts[-1].strip()

        # --- 重建消息链 ---
        # 为了防止消息中包含图片等非文本组件，我们不能简单地替换整个消息。
        # 我们需要遍历原始消息链，只替换文本部分。
        new_message_chain = []
        text_part_updated = False
        for component in result.result_message:
            # 只处理第一个文本组件，并用我们的干净文本替换它
            if isinstance(component, Comp.Text) and not text_part_updated:
                new_message_chain.append(Comp.Text(text=clean_text))
                text_part_updated = True # 标记已替换，后续的文本组件将被丢弃
            # 如果不是文本组件（例如图片），则原样保留
            elif not isinstance(component, Comp.Text):
                new_message_chain.append(component)
        
        # 用我们新建的、干净的消息链来更新最终结果
        result.result_message.clear()
        result.result_message.extend(new_message_chain)
        logger.debug(f"[FinalReplyTrimmer] 已触发最终保险丝，成功裁剪 '最终的罗莎回复' 标记。")
