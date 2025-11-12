import asyncio
import os
from pathlib import Path
from typing import List, Optional
import jq
import portkey_ai
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader, JSONLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import CharacterTextSplitter
from portkey_ai import Portkey, createHeaders

from pydantic import SecretStr

from src.message_trim import keep_latest_messages
from src.env_config import set_env
set_env()

"""
The agent will be wrapped as a tool combined roche SIEM agent tools to use

"""
class AgenticRAGSystem:
    def __init__(self, knowledge_base_path: str = Path(__file__).parent.parent.resolve()/"knowledge"):
        print("Initializing Agentic RAG System...")
        knowledge_path = Path(__file__).parent.parent.resolve()/"knowledge"
        print("The knowledge base path is {}".format(knowledge_path))
        self.knowledge_base_path = knowledge_base_path
        portkey_headers = createHeaders(api_key=os.getenv("LLM_API_KEY"),provider="azure-openai")
        self.embeddings =OpenAIEmbeddings(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=os.getenv("LLM_EMBEDDING_MODEL"),
            default_headers=portkey_headers
        )
        self.vector_store = None
        self.retriever = None
        self._initialize_rag()

    def _initialize_rag(self):
        """初始化RAG系统"""
        # 加载知识库文档
        if os.path.exists(self.knowledge_base_path):
            loader = DirectoryLoader(self.knowledge_base_path, glob="**/*.txt")
            documents = loader.load()

            json_documents = []
            for file in Path(self.knowledge_base_path).glob("**/*.json"):
                json_document = JSONLoader(
                    file,
                    jq_schema=".",
                    text_content=False,
                ).load()
                json_documents.extend(json_document)

            documents = documents + json_documents

            markdown_documents = []
            for file in Path(self.knowledge_base_path).glob("**/*.md"):
                markdown_document = UnstructuredMarkdownLoader(
                    file,
                ).load()
                markdown_documents.extend(markdown_document)
            documents = documents + markdown_documents



            # 分割文档
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.split_documents(documents)

            # 创建向量存储
            self.vector_store = FAISS.from_documents(docs, self.embeddings)
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
        else:
            # 创建空的向量存储
            self.vector_store = FAISS.from_texts([""], self.embeddings)
            self.retriever = self.vector_store.as_retriever()

    def get_rag_tool(self):
        """创建RAG工具"""
        from langchain.tools import Tool

        def rag_search(query: str) -> str:
            """使用RAG检索相关信息"""
            try:
                docs = self.retriever.get_relevant_documents(query)
                if not docs:
                    return "未找到相关信息"

                context = "\n\n".join([doc.page_content for doc in docs])
                return f"检索到的相关信息：\n{context}"
            except Exception as e:
                return f"检索错误：{str(e)}"

        return Tool(
            name="knowledge_search",
            description="搜索安全知识库获取相关背景信息",
            func=rag_search
        )

    def add_document(self, text: str, metadata: dict = None):
        """动态添加文档到知识库"""
        if metadata is None:
            metadata = {}

        # 创建新文档
        from langchain.schema import Document
        new_doc = Document(page_content=text, metadata=metadata)

        # 添加到向量存储
        self.vector_store.add_documents([new_doc])

        # 更新检索器
        self.retriever = self.vector_store.as_retriever()


# # 初始化RAG系统
# rag_system = AgenticRAGSystem()
#
#
# async def create_enhanced_agent():
#     """创建增强的SIEM Agent with RAG"""
#     # 获取MCP工具
#     client = MultiServerMCPClient(
#         {
#             "aliyun_actiontrail_mcp_server": StreamableHttpConnection(
#                 url=os.getenv("MCP_SERVER_ENDPOINT"),
#                 transport="streamable_http"
#             )
#         }
#     )
#     mcp_tools = await client.get_tools()
#
#     # 添加RAG工具
#     rag_tool = rag_system.get_rag_tool()
#     all_tools = mcp_tools + [rag_tool]
#
#     # 创建自定义提示
#     custom_prompt = """
#     你是一个安全情报分析专家，具有以下能力：
#     1. 通过AliCloud ActionTrail MCP服务器访问云安全日志
#     2. 通过知识库搜索获取安全事件背景信息
#     3. 综合分析日志和知识库信息提供安全建议
#
#     请根据用户查询选择合适的工具，并结合多种信息源进行分析。
#
#     {context}
#     """
#
#     # 创建agent
#     agent = create_react_agent(
#         llm,
#         tools=all_tools,
#         prompt=custom_prompt,
#         pre_model_hook=keep_latest_messages,
#     )
#
#     return agent
#
#
# # 创建agent实例
# roche_siem_agent = asyncio.run(create_enhanced_agent())