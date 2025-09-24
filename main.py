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
    "1.0.2", # 版本号微调
)
class FinalReplyTrimmer(Star):
    # --- 兼容性修正 ---
    # __init__ 函数现在只接收 context 参数，以兼容较旧版本的 AstrBot
    def __init__(self, context: Context):
        super().__init__(context)
        # --- 修正结束 ---

        # 为了效率，预先编译正则表达式
        self.FINAL_REPLY_PATTERN = re.compile(r"最终的罗莎回复[:：]?\s*", re.IGNORECASE)
        logger.info("[FinalReplyTrimmer] 最终保险丝插件已加载。")

    @filter.on_decorating_result(priority=200)
    async def trim_final_reply(self, event: AstrMessageEvent, *args, **kwargs):
        result = event.get_result()
        if not result or not result.result_message:
            return

        plain_text = result.get_plain_text()

        if not self.FINAL_REPLY_PATTERN.search(plain_text):
            return

        parts = self.FINAL_REPLY_PATTERN.split(plain_text)
        clean_text = parts[-1].strip()

        new_message_chain = []
        text_part_updated = False
        for component in result.result_message:
            if isinstance(component, Comp.Text) and not text_part_updated:
                new_message_chain.append(Comp.Text(text=clean_text))
                text_part_updated = True
            elif not isinstance(component, Comp.Text):
                new_message_chain.append(component)
        
        if new_message_chain:
            result.result_message.clear()
            result.result_message.extend(new_message_chain)
            logger.debug(f"[FinalReplyTrimmer] 已触发最终保险丝，成功裁剪 '最终的罗莎回复' 标记。")
        else:
            event.stop_event()
            logger.debug(f"[FinalReplyTrimmer] 裁剪后消息为空，已阻止发送。")
