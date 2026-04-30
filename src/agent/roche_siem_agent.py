"""GitHub MCP Agent - An agent that uses GitHub MCP tools for repository management."""
import asyncio
import json
import os
from functools import wraps
from typing import Iterable, Any

from asyncio_throttle import Throttler
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import RemoveMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime

from agent.agentic_RAG_agent import AgenticRAGSystem
from agent.lazy_agent import LazyLoadingAgent
from env_config import set_env
from llm import get_model

from log_config import get_logger
from schema.models import  OpenAIModelName
logger = get_logger(__name__)
set_env()

class LoggingSummarizationMiddleware(SummarizationMiddleware):
    def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:  # noqa: ARG002
        """Process messages before model invocation, potentially triggering summarization."""
        messages = state["messages"]
        self._ensure_message_ids(messages)

        total_tokens = self.token_counter(messages)
        logger.debug(f"before input model, get the total tokens: {total_tokens}")
        if (
                self.max_tokens_before_summary is not None
                and total_tokens < self.max_tokens_before_summary
        ):
            logger.debug(f"the total tokens {total_tokens} < hit_tokens_threshold_must_summary {self.max_tokens_before_summary}, so no need to summarize")
            return None
        else:
            logger.debug(f"the total tokens {total_tokens} > hit_tokens_threshold_must_summary {self.max_tokens_before_summary}, so have to summarize")

        cutoff_index = self._find_safe_cutoff(messages)

        if cutoff_index <= 0:
            logger.debug("for summarization, can not find appropriate cutoff_index, so skip summarization")
            return None

        messages_to_summarize, preserved_messages = self._partition_messages(messages, cutoff_index)

        summary = self._create_summary(messages_to_summarize)
        logger.debug(f"after summary, get the result is: {summary}")
        new_messages = self._build_new_messages(summary)

        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages,
                *preserved_messages,
            ]
        }

prompt = """
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
        """.strip()


class RocheSIEMAgent(LazyLoadingAgent):
    """Roche Security MCP Agent with async initialization."""

    def __init__(self) -> None:
        super().__init__()
        self._mcp_tools: list[BaseTool] = []
        self.recursion_limit = 100

    def _check_tool_name(self,tools: Iterable):
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
            kind = "platform" if self._is_platform_tool(name) else "custom"
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

    def _is_platform_tool(self,name: str) -> bool:
        return name.startswith("multi_tool_use.") or name in {"multi_tool_use.parallel"}

    def _debug_tools(self,tag: str, tools: Iterable):
        if os.getenv("LOG_LEVEL") != "DEBUG":
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



    def _rate_limit_tool(self,func):
        """工具限流装饰器"""
        _tool_throttler = Throttler(rate_limit=30, period=1)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with _tool_throttler:
                # 添加最小间隔时间确保QPS控制
                # await asyncio.sleep(0.5)  # 最小间隔100ms
                return await func(*args, **kwargs)

        return wrapper

    async def _get_roche_SIEM_agent_tools(self) -> list[BaseTool]:
        """Fetch and combine tools from MCP and custom RAG tools."""
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

        self._debug_tools("MCP",mcp_tools)

        rag_local_tool = AgenticRAGSystem().get_local_rag_tool()
        # rag_raas_tool = AgenticRAGSystem().get_RAAS_rag_tool()
        rag_flow_tool = AgenticRAGSystem().get_rag_flow_tool()
        rag_flow_prompt_tool = AgenticRAGSystem().get_rag_flow_prompt_tool()
        # rag_tool_local = Tool(
        #     name="Roche_knowledge_base",
        #     description="第一个RAG库，搜索罗氏相关的基础信息，比如罗氏的阿里云出口IP，罗氏拥有的域名等，如果找不到，可以继续在其他知识库中搜索",
        #     func=rag_local_tool
        # )
        # rag_tool_roche = Tool(
        #     name="Roche_SIEM_knowledge_search",
        #     description="第二个RAG库，搜索罗氏相关的基础信息，比如罗氏的阿里云出口IP，罗氏拥有的域名等，如果找不到，可以继续在其他知识库中搜索",
        #     func=rag_raas_tool
        # )

        tools = mcp_tools + [rag_local_tool, rag_flow_tool, rag_flow_prompt_tool]

        self._debug_tools("MERGED", tools)
        self._check_tool_name(tools)

        # Wrap async tool funcs with throttler
        for tool in tools:
            if hasattr(tool, 'func') and asyncio.iscoroutinefunction(tool.func):
                original = tool.func
                tool.func = self._rate_limit_tool(original)

        logger.info("Final tool count (including platform + custom): %d", len(tools))
        return tools

    async def load(self) -> None:
        """Initialize the Roche SIEM agent"""
        try:
            # Get tools from the client
            self._mcp_tools = await self._get_roche_SIEM_agent_tools()
            logger.info(f"Roche SIEM agent initialized with {len(self._mcp_tools)} tools")

        except Exception as e:
            logger.error(f"Failed to initialize Roche SIEM agent: {e}")
            self._mcp_tools = []
            self._mcp_client = None

        # Create and store the graph
        self.graph = self._create_graph()
        self._loaded = True

    def _create_graph(self) -> CompiledStateGraph:
        """Create the GitHub MCP agent graph."""
        model = get_model(OpenAIModelName.GPT_5)

        return create_agent(
            checkpointer=None,
            model=model,
            tools=self._mcp_tools,
            name="roche-siem-agent",
            system_prompt=prompt,
            middleware=[
                LoggingSummarizationMiddleware(
                    model,
                    max_tokens_before_summary=150000,
                    summary_prompt="总结一下到目前为止的网络安全调查结果",
                    token_counter=count_tokens_approximately
                )
            ],
        ).with_config(recursion_limit=self.recursion_limit)



# Create the agent instance
roche_siem_agent = RocheSIEMAgent()
