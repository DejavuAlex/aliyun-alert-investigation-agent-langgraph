import asyncio
import logging
import os
import json
from typing import Iterable


from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.prebuilt import create_react_agent
from langchain.agents import Tool
from asyncio_throttle import Throttler
from src.agent.agentic_RAG_agent import AgenticRAGSystem
from src.message_trim import keep_latest_messages
from src.env_config import set_env
from src.llm import llm
from functools import wraps
set_env()

# Configure logging (level can be overridden via LOG_LEVEL env)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
logger = logging.getLogger("roche_siem_agent")

def check_tool_name(tools: Iterable):
    """
    Enhanced diagnostic for tool objects (dict or Tool instances).
    Prints:
      - index, name, length
      - classification (platform injected vs custom)
      - duplicate detection
      - suspicious (too long) warning
    """
    seen = {}
    duplicates = []
    platform_count = 0
    custom_count = 0
    for i, t in enumerate(tools):
        if isinstance(t, dict):
            name = t.get("function", {}).get("name") or t.get("name")
        else:
            # langchain Tool
            name = getattr(t, "name", "<no-name>")
        kind = "platform" if is_platform_tool(name) else "custom"
        platform_count += (kind == "platform")
        custom_count += (kind == "custom")
        if name in seen:
            duplicates.append(name)
        else:
            seen[name] = 1
        logger.info("[Tool %d] name='%s' len=%d kind=%s", i, name, len(name), kind)
        if os.getenv("LOGGER_LEVEL") == "DEBUG":
            # Print shallow structure only
            try:
                logger.debug("   raw_keys=%s", list(t.keys()) if isinstance(t, dict) else "attrs: %s",
                             )
            except Exception:
                pass
        if len(name or "") > 64:
            logger.warning("   ❌ Name exceeds 64 chars: %s", name)

    logger.info("Tool summary: total=%d custom=%d platform=%d duplicates=%d",
                platform_count + custom_count, custom_count, platform_count, len(duplicates))
    if duplicates:
        logger.warning("Duplicate tool names detected: %s", duplicates)

def is_platform_tool(name: str) -> bool:
    return name.startswith("multi_tool_use.") or name in {"multi_tool_use.parallel"}

def debug_tools(tag: str, tools: Iterable):
    if os.getenv("LOGGER_LEVEL") != "DEBUG":
        return
    out = []
    for t in tools:
        if isinstance(t, dict):
            fn = t.get("function", {})
            out.append({
                "name": fn.get("name") or t.get("name"),
                "desc": fn.get("description") or t.get("description"),
                "keys": list(t.keys())
            })
        else:
            out.append({
                "name": getattr(t, "name", None),
                "desc": getattr(t, "description", None),
                "type": type(t).__name__
            })
    logger.debug("%s tools dump:\n%s", tag, json.dumps(out, ensure_ascii=False, indent=2))

# 全局并发控制
#tool_semaphore = asyncio.Semaphore(5)
tool_throttler = Throttler(rate_limit=30, period=1)  # 每秒最多30次请求

def rate_limit_tool(func):
    """工具限流装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with tool_throttler:
            # 添加最小间隔时间确保QPS控制
            # await asyncio.sleep(0.5)  # 最小间隔100ms
            return await func(*args, **kwargs)
    return wrapper

async def roche_SIEM_agent():
    """ Access AliCloud ActionTrail via MCP server"""
    client = MultiServerMCPClient(
        {
            "roche_siem_server": StreamableHttpConnection(
                url=os.getenv("MCP_SERVER_ENDPOINT"),
                transport="streamable_http"
            )
        }
    )
    # Fetch MCP tools with diagnostics
    try:
        mcp_tools = await client.get_tools()
    except Exception as e:
        logger.exception("Failed to get MCP tools: %s", e)
        mcp_tools = []

    debug_tools("MCP", mcp_tools)

    rag_tool = Tool(
        name="Roche_knowledge_base",
        description="搜索罗氏相关的基础信息，比如罗氏的阿里云出口IP，罗氏拥有的域名等",
        func=AgenticRAGSystem().get_rag_tool().func
    )

    tools = mcp_tools + [rag_tool]

    debug_tools("MERGED", tools)
    check_tool_name(tools)

    # Wrap async tool funcs with throttler
    for tool in tools:
        if hasattr(tool, 'func') and asyncio.iscoroutinefunction(tool.func):
            original = tool.func
            tool.func = rate_limit_tool(original)

    logger.info("Final tool count (including platform + custom): %d", len(tools))
    return tools

# change the recursion limit because of Ali cloud throttling limitation
recursion_limit = 100
roche_siem_agent = create_react_agent(
        llm,
        tools = asyncio.run(roche_SIEM_agent()),
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