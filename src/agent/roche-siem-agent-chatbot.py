

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
# from langgraph.func import entrypoint
#
# import schema.models
# from llm import get_model
#
#
# @entrypoint()
# async def roche_siem_agent_chatbot(
#     inputs: dict[str, list[BaseMessage]],
#     *,
#     previous: dict[str, list[BaseMessage]],
#     config: RunnableConfig,
# ):
#     messages = inputs["messages"]
#     if previous:
#         messages = previous["messages"] + messages
#
#     model = get_model(schema.models.OpenAIModelName.GPT_5)
#     response = await model.ainvoke(messages)
#     return entrypoint.final(
#         value={"messages": [response]}, save={"messages": messages + [response]}
#     )