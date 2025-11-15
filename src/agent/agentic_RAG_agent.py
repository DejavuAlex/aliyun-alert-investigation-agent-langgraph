import logging
import os
import time
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader, JSONLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import CharacterTextSplitter
from portkey_ai import Portkey, createHeaders

from src.client.roche_RAG_SAAS_client import Roche_RAG_SAAS_client
from src.env_config import set_env
set_env()

logger = logging.getLogger(__name__)
"""
The agent will be wrapped as a tool combined roche SIEM agent tools to use

"""
class AgenticRAGSystem:
    def __init__(self, local_knowledge_base_path: str = Path(__file__).parent.parent.resolve() / "knowledge"):
        print("Initializing Agentic RAG System...")
        self.check_env_variables()
        knowledge_path = Path(__file__).parent.parent.resolve()/"knowledge"
        print("The knowledge base path is {}".format(knowledge_path))
        self.local_knowledge_base_path = local_knowledge_base_path
        portkey_headers = createHeaders(api_key=os.getenv("LLM_API_KEY"),provider="azure-openai")
        self.embeddings =OpenAIEmbeddings(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            model=os.getenv("LLM_EMBEDDING_MODEL"),
            default_headers=portkey_headers
        )
        self.local_knowledge_vector_store = None
        self.local_knowledge_retriever = None
        self.local_rag_enabled = self._initialize_local_rag()

        self.roche_rag_saas_client = Roche_RAG_SAAS_client(
            google_share_drive=os.getenv("GOOGLE_SHARE_DRIVE"),
            embedding_model=os.getenv("LLM_EMBEDDING_MODEL"),
            base_url=os.getenv("RAAS_BASE_URL"),
            rass_api_key=os.getenv("RAAS_API_KEY"),
            api_id=os.getenv("API_ID"),
            portkey_api_key=os.getenv("LLM_API_KEY")
        )
        self.RAAS_enabled = self._initialize_RAAS()

    def check_env_variables(self):
        required_vars = [
            "LLM_API_KEY",
            "LLM_BASE_URL",
            "LLM_EMBEDDING_MODEL",
            "API_ID",
            "RAAS_API_KEY",
            "GOOGLE_SHARE_DRIVE",
            "RAAS_BASE_URL"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # initialize ROCHE RAG SAAS
    def _initialize_RAAS(self) -> bool:
        # 创建RAG SAAS集合
        collection_id = self.roche_rag_saas_client.create_collection()
        if collection_id:
            logger.info(f"RAG SAAS collection created with ID: {collection_id}")
            self.collection_id = collection_id
            # 检查RAG SAAS collections创建状态
            timeout_seconds = 60
            start_time = time.time()
            poll_interval = 2

            while True:
                if self.roche_rag_saas_client.retrieve_collection_status(self.collection_id):
                    logger.info(f"RAG SAAS collection {self.collection_id} is active.")
                    return True
                if time.time() - start_time >= timeout_seconds:
                    logger.warning(
                        f"Timeout waiting for RAG SAAS collection {self.collection_id} to become active after {timeout_seconds} seconds.")
                    return False
                logger.info(f"RAG SAAS collection {self.collection_id} is not active. Retrying in {poll_interval}s...")
                time.sleep(poll_interval)

        else:
            logger.info("Failed to create RAG SAAS collection.")
            return False




    def get_RAAS_rag_tool(self):
        """创建RAG工具"""
        from langchain.tools import Tool
        if self.RAAS_enabled:
            def rag_search(query: str) -> str:
                """使用RAG检索相关信息"""
                try:
                    docs = self.roche_rag_saas_client.search(self.collection_id,query)
                    if not docs:
                        return "未找到相关信息"
                    return f"检索到的相关信息：\n{docs}"
                except Exception as e:
                    return f"检索错误：{str(e)}"

            return Tool(
                name="RAAS_knowledge_search",
                description="搜索安全知识库获取相关背景信息",
                func=rag_search
            )
        else:
            logger.warning("RAAS RAG tool requested but RAAS is not enabled.")
            def rag_search_unavailable(query: str) -> str:
                return "ROCHE RAG SAAS知识库未初始化，无法进行检索。"
            return Tool(
                name="RAAS_knowledge_search_unavailable",
                description="ROCHE RAG SAAS知识库未初始化，无法进行检索。",
                func=rag_search_unavailable
            )


    def _initialize_local_rag(self) -> bool:
        """初始化RAG系统"""
        # 加载知识库文档
        if os.path.exists(self.local_knowledge_base_path):
            loader = DirectoryLoader(self.local_knowledge_base_path, glob="**/*.txt")
            documents = loader.load()

            json_documents = []
            for file in Path(self.local_knowledge_base_path).glob("**/*.json"):
                json_document = JSONLoader(
                    file,
                    jq_schema=".",
                    text_content=False,
                ).load()
                json_documents.extend(json_document)

            documents = documents + json_documents

            markdown_documents = []
            for file in Path(self.local_knowledge_base_path).glob("**/*.md"):
                markdown_document = UnstructuredMarkdownLoader(
                    file,
                ).load()
                markdown_documents.extend(markdown_document)
            documents = documents + markdown_documents



            # 分割文档
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.split_documents(documents)

            # 创建向量存储
            self.local_knowledge_vector_store = FAISS.from_documents(docs, self.embeddings)
            self.local_knowledge_retriever = self.local_knowledge_vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            return True
        else:
            logger.info(f"local knowledge path {self.local_knowledge_base_path} not found.")
            self.local_knowledge_retriever = None
            return False
            # 创建空的向量存储
            # self.vector_store = FAISS.from_texts([""], self.embeddings)
            # self.retriever = self.vector_store.as_retriever()

    def get_local_rag_tool(self):
        """创建RAG工具"""
        from langchain.tools import Tool
        if self.local_knowledge_retriever is not None:
            def rag_search(query: str) -> str:
                """使用RAG检索相关信息"""
                try:
                    docs = self.local_knowledge_retriever.get_relevant_documents(query)
                    if not docs:
                        return "未找到相关信息"

                    context = "\n\n".join([doc.page_content for doc in docs])
                    return f"检索到的相关信息：\n{context}"
                except Exception as e:
                    return f"检索错误：{str(e)}"

            return Tool(
                name="local_knowledge_search",
                description="搜索本地安全知识库获取相关背景信息",
                func=rag_search
            )
        else:
            logger.warning("Local RAG tool requested but local knowledge retriever is not initialized.")
            def rag_search_unavailable(query: str) -> str:
                return "本地知识库未初始化，无法进行检索。"
            return Tool(
                name="local_knowledge_search_unavailable",
                description="本地知识库未初始化，无法进行检索。",
                func=rag_search_unavailable
            )

    def add_local_document(self, text: str, metadata: dict = None):
        """动态添加文档到知识库"""
        if metadata is None:
            metadata = {}

        # 创建新文档
        from langchain.schema import Document
        new_doc = Document(page_content=text, metadata=metadata)

        # 添加到向量存储
        self.local_knowledge_vector_store.add_documents([new_doc])

        # 更新检索器
        self.local_knowledge_retriever = self.local_knowledge_vector_store.as_retriever()

