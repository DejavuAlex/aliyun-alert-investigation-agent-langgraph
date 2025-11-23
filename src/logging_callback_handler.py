from langchain_core.callbacks import BaseCallbackHandler

from log_config import get_logger

# logger = logging.getLogger(__file__)
# logger.setLevel(os.getenv("LOGGER_LEVEL") or "INFO")
#
# if not logger.handlers:
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)
logger = get_logger(__name__)

class LoggingCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        logger.debug(f"========= 🤖 LLM 开始调用，提示词========= \n "
                    f"提示词元素个数 {len(prompts)}\n "
                    f"提示词字符串长度(不是tokens长度) {len(''.join(prompts))}\n "
                    f"提示词内容(只截取每个元素的前200个字符):\n"
                    f"{'prompts的每个元素的分隔符'.join([prompt[:200] for prompt in prompts])}...\n"
                    f"========= \n")

    def on_llm_end(self, response, **kwargs):
        gen = response.generations
        if gen and hasattr(gen[0][0], "message"):
            content = gen[0][0].message.content or ""
        elif gen:
            content = gen[0][0].text or ""
        else:
            content = ""
        logger.debug(f"========= ✅ LLM 返回========= \n {content[:200]}...\n")

    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.debug(f"========= 🛠️ 工具 {serialized.get('name')} 开始执行，输入========= \n {input_str}]\n========= \n")

    def on_tool_end(self, output, **kwargs):
        logger.debug(f"========= ✅ 工具执行完成，输出========= \n {output}\n========= \n")

    def on_chain_start(self, serialized, inputs, **kwargs):
        logger.debug(f"========= ⛓️ 链开始: {serialized.get('name')}, 输入========= \n {inputs}\n========= \n")

    def on_chain_end(self, outputs, **kwargs):
        logger.debug(f"========= ✅ 链结束，输出========= \n{outputs}\n========= \n")