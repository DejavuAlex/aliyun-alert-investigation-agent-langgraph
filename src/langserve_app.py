import asyncio

from fastapi import FastAPI
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import create_react_agent
from langserve import add_routes

from src.llm import llm
from agent.roche_siem_agent import roche_SIEM_agent, recursion_limit
from message_trim import keep_latest_messages

agent_runnable = None  # will be set in lifespan

async def build_roche_siem_agent():
    return create_react_agent(
        llm,
        tools= await roche_SIEM_agent(),
        prompt="""
                你既是安全分析专家也是DevOps专家，具有以下能力：
                    安全分析能力：
                    1. 通过工具访问AliCloud各个资源的配置和日志
                    2. 通过工具能搜索到知识库获取各种企业相关的知识
                    3. 综合多种信息源提供全面的安全分析
                    4，请根据查询内容智能选择合适的工具组合。
                    5，如果需要安全调查时，优先从工具库中查找相关的调查prompt模版，按照模版展开调查，如果没有则你自行展开分析
                    6，如果需要调查阿里云网络安全事件告警，遵循以下原则:
                        - 必须优先调用工具库的相关调查模版
                        - 模版获取后，严格按模版展开调查与输出，再进行补充查询与研判
                        - 所有阿里云接口如果返回 next_token，必须进行分页迭代，直到定位到“最近一次”事件或数据耗尽
                        - 若找不到对应模版工具，必须先告知并征询是否允许“无模版”分析，禁止自行跳过模版
                        - 如果用户输入的是某种安全事件类别，则先查询知识库中'阿里云网络安全事件分类'得出事件分类，然后根据事件分类展开调查
                        - 调用工具时传入的access_key_id都是通过调用工具库中get_aliyun_all_accounts_info工具获得的本智能体所能使用的AK
                    故障排除能力:
                    能够根据用户的需求，做故障排查
                """,
        pre_model_hook=keep_latest_messages,
    ).with_config(recursion_limit=recursion_limit)

async def lifespan(app: FastAPI):
    global agent_runnable
    agent_runnable = await build_roche_siem_agent()
    add_routes(app, agent_runnable, path="/ai_siem")
    yield


app = FastAPI(title="Roche SIEM Agent", lifespan=lifespan)


@app.get("/")
async def root():
    return {"status": "ok", "endpoints": ["/ai_siem/invoke", "/ai_siem/stream"]}

# Optional local run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
