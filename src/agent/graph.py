
from langgraph.prebuilt import create_react_agent

from src.env_config import set_env
set_env()

from src.llm import llm


def get_whether(city:str) -> str:
    """模拟一个获取天气的函数"""
    # 这里可以调用实际的天气API
    return f"{city}的天气是晴天，25摄氏度"

graph = create_react_agent(
    llm,
    tools = [
        get_whether
    ],
    prompt="you are an assistant"

)
#
# graph.invoke(
#     {"message":"北京的天气怎么样？"}
# )
