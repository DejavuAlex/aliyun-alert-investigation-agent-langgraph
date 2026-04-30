from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult

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
    """
    [[ChatGeneration(generation_info={'finish_reason': 'tool_calls', 'model_name': 'gpt-5-2025-08-07'}, message=AIMessage(content='', additional_kwargs={}, response_metadata={'finish_reason': 'tool_calls', 'model_name': 'gpt-5-2025-08-07', 'model_provider': 'openai'}, id='lc_run--5058f176-80c5-4ab6-9b8c-429006332976', tool_calls=[{'name': 'ali_cloud_account_mcp_server_get_aliyun_all_accounts_info', 'args': {}, 'id': 'call_JPoDlYL58m0ZcfI80kXFFBe3', 'type': 'tool_call'}]))]] llm_output=None run=None type='LLMResult'
    """
    def on_llm_end(self, response:LLMResult, **kwargs):
        logger.debug("get the llm response is {}".format(response))
        # gen = response.generations
        # if gen and hasattr(gen[0][0], "message"):
        #     content = gen[0][0].message.content or ""
        # elif gen:
        #     content = gen[0][0].text or ""
        # else:
        #     content = ""
        logger.debug(f"========= ✅ LLM 返回========= \n")
        for i, generation in enumerate(response.generations):
            for j, generation_piece in enumerate(generation):
                logger.debug(f"--- 返回片段 {i}-{j} ---\n")
                if hasattr(generation_piece, "message"):
                    if isinstance(generation_piece.message,AIMessage):
                        logger.debug("返回message类型为{}".format(generation_piece.type))
                        ai_message:AIMessage = generation_piece.message
                        logger.debug(f"返回内容: {ai_message.content}\n")
                        if hasattr(ai_message, "tool_calls"):
                            logger.debug("返回包含工具调用信息\n")
                            for tool_call in ai_message.tool_calls:
                                logger.debug("调用的工具名: {}\n".format(tool_call.get("name")))
                                logger.debug("调用的工具参数: {}\n".format(tool_call.get("args")))
                    else:
                        logger.debug("返回message类型未知{}".format(type(generation_piece.message)))
                else:
                    logger.debug("返回文本内容: {}\n".format(generation_piece.text))
                tool_call = generation_piece.generation_info.get("tool_call") if generation_piece.generation_info else None
                if tool_call:
                    logger.debug(f"调用的工具: {tool_call}\n")
                logger.debug(f"附加信息: {generation_piece.generation_info}\n")


    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.debug(f"========= 🛠️ 工具 {serialized.get('name')} 开始执行，输入========= \n {input_str}]\n========= \n")

    def on_tool_end(self, output, **kwargs):
        logger.debug(f"========= ✅ 工具执行完成，输出========= \n {output}\n========= \n")

    def on_chain_start(self, serialized, inputs, **kwargs):
        logger.debug(f"========= ⛓️ 链开始: {serialized.get('name')}, 输入========= \n {inputs}\n========= \n")

    def on_chain_end(self, outputs, **kwargs):
        logger.debug(f"========= ✅ 链结束，输出========= \n{outputs}\n========= \n")