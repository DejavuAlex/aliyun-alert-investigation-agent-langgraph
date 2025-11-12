import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, RemoveMessage
from langchain_core.messages.utils import trim_messages,count_tokens_approximately
from langgraph.graph.message import REMOVE_ALL_MESSAGES

from src.env_config import set_env
set_env()

from src.llm import llm
logger = logging.getLogger(__file__)
logger.setLevel(os.getenv("LOGGER_LEVEL") or "INFO")


def monitor_message_trim_status(status,messages):
    logger.info(f"{status}消息数量: {len(messages)}")
    logger.info(f"{status}消息总字符数:{sum(len(message.content) for message in messages)}\n")
    logger.info(f"以下是每条消息的细节\n")
    for id,message in enumerate(messages):
        if type(message) is HumanMessage:
            logger.info("{},the {} of message: it is HumanMessage, the length is {}, the content(前200个字符) is {}\n".format(status,id,len(message.content),(message.content)[:200]))
        elif type(message) is str:
            logger.info("{},the {} of message: it is str, the length is {}, the content(前200个字符) is {}\n".format(status,id,len(message),message[:200]))
        elif type(message) is SystemMessage:
            logger.info("{},the {} of message: it is SystemMessage, the length is {}, the content(前200个字符) is {}\n".format(status,id,message.content,len(message.content),(message.content)[:200]))
        elif type(message) is AIMessage:
            logger.info("{},the {} of message: it is AIMessage, the length is {}, the content(前200个字符) is {}\n".format(status,id,len(message.content),(message.content)[:200]))
        elif type(message) is ToolMessage:
            logger.info("{},the {} of message: it is ToolMessage, the length is {}, the content(前200个字符) is {}\n".format(status,id,len(message.content),(message.content)[:200]))
        else:
            logger.info("{},the {} of message: it is {}, the length is {}, the content is {}\n".format(status,id,type(message),len(message),message[:200]))
"""
method 1:  keep only latest messages until max_tokens is reached
"""
def keep_latest_messages(state,max_tokens=int(os.getenv("LLM_MAX_TOKENS","260000"))):
    logger.info(f"Begin to trim messages to ensure not to reach the {max_tokens} tokens")

    messages = state["messages"]
    monitor_message_trim_status("修剪前",messages)
    if messages and hasattr(messages[0], 'content') and isinstance(messages[0].content, str):
        system_message = messages[0]
        if llm.get_num_tokens(system_message.content) > 1000:  # 如果系统消息超过1000 tokens
            print("系统消息过长，进行截断")
            # 截断系统消息到合理长度
            system_message.content = system_message.content[:2000] + "\n...（系统消息已截断）"

    trimmed_messages = trim_messages(
        state["messages"],
        max_tokens=max_tokens/2,  # 留一半的空间给LLM生成回答
        strategy="last",
        token_counter=count_tokens_approximately,
        include_system=True,
        start_on="human",
        end_on=("human","tool"),
    )
    monitor_message_trim_status("修剪后",trimmed_messages)

    # return {"llm_input_messages": trimmed_messages}
    return {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *trimmed_messages]
        }
"""
method 2 : use LLM model to summarize old messages into fewer tokens
"""
print("get the lLM_MAX_TOKENS is ",int(os.getenv("LLM_MAX_TOKENS")))
from langmem.short_term import SummarizationNode
summarization_messages = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=llm,
    max_tokens=int(os.getenv("LLM_MAX_TOKENS")),
    max_summary_tokens=int(os.getenv("LLM_MAX_TOKENS"))//4,
    output_messages_key="llm_input_messages"
)
