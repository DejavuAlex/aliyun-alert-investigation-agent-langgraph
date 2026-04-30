import logging
import os
import time
import hashlib
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader, JSONLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import CharacterTextSplitter
from portkey_ai import Portkey, createHeaders

from env_config import set_env
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

        # self.roche_rag_saas_client = Roche_RAG_SAAS_client(
        #     google_share_drive=os.getenv("GOOGLE_SHARE_DRIVE"),
        #     embedding_model=os.getenv("LLM_EMBEDDING_MODEL"),
        #     base_url=os.getenv("RAAS_BASE_URL"),
        #     rass_api_key=os.getenv("RAAS_API_KEY"),
        #     api_id=os.getenv("API_ID"),
        #     portkey_api_key=os.getenv("LLM_API_KEY")
        # )
        # self.RAAS_enabled = self._initialize_RAAS()

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
        from langchain_core.tools import Tool
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
            # 需要分割的文档：txt、json、md
            chunkable_documents = []
            loader = DirectoryLoader(self.local_knowledge_base_path, glob="**/*.txt")
            chunkable_documents.extend(loader.load())

            json_documents = []
            for file in Path(self.local_knowledge_base_path).glob("**/*.json"):
                json_document = JSONLoader(
                    file,
                    jq_schema=".",
                    text_content=False,
                ).load()
                json_documents.extend(json_document)
            chunkable_documents = chunkable_documents + json_documents

            markdown_documents = []
            for file in Path(self.local_knowledge_base_path).glob("**/*.md"):
                markdown_document = UnstructuredMarkdownLoader(
                    file,
                ).load()
                markdown_documents.extend(markdown_document)
            chunkable_documents = chunkable_documents + markdown_documents

            # 不分割的文档：sh脚本
            shell_documents = []
            for file in Path(self.local_knowledge_base_path).glob("**/*.sh"):
                docs = TextLoader(file, encoding="utf-8").load()
                # 增加元数据，方便后续脚本上传与执行定位原始文件，并做完整性校验
                try:
                    with open(file, "rb") as f:
                        file_bytes = f.read()
                    sha256 = hashlib.sha256(file_bytes).hexdigest()
                except Exception:
                    sha256 = None
                for d in docs:
                    d.metadata.update({
                        "file_ext": ".sh",
                        "no_split": True,
                        "source_path": str(file),
                        "filename": os.path.basename(file),
                        "sha256": sha256
                    })
                shell_documents.extend(docs)

            # 仅分割 chunkable 文档
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            chunked_docs = text_splitter.split_documents(chunkable_documents)

            # 合并：分割后的普通文档 + 原样的 .sh 脚本文档
            all_docs = chunked_docs + shell_documents

            # 创建向量存储
            self.local_knowledge_vector_store = FAISS.from_documents(all_docs, self.embeddings)
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
        from langchain_core.tools import Tool
        if self.local_knowledge_retriever is not None:
            def rag_search(query: str) -> str:
                """使用RAG检索相关信息"""
                try:
                    docs = self.local_knowledge_retriever.invoke(query)
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
        from langchain_core.documents import Document
        new_doc = Document(page_content=text, metadata=metadata)

        # 添加到向量存储
        self.local_knowledge_vector_store.add_documents([new_doc])

        # 更新检索器
        self.local_knowledge_retriever = self.local_knowledge_vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )

    def get_rag_flow_tool(self):
        from langchain_core.tools import Tool
        import json
        # RAG检索工具
        def rag_flow_retrieve(query: str) -> str:
            """
            从RAG系统检索数据块
            Args:
                query: 用户查询问题
            """
            import requests
            # 获取环境变量中的API地址和密钥
            api_base_url = os.getenv("RAGFLOW_API_BASE")
            api_key = os.getenv("RAGFLOW_API_KEY")

            if not api_base_url or not api_key:
                error_msg = "RAG系统配置缺失，请检查RAGFLOW_API_BASE和RAGFLOW_API_KEY环境变量"
                logger.error(error_msg)
                return error_msg

            url = api_base_url.rstrip('/')
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            # 构造请求体
            payload = {
                "question": query
            }
            dataset_ids = os.getenv("RAGFLOW_DATASET_IDS")
            # 可选参数
            if dataset_ids:
                dataset_ids = [id.strip() for id in dataset_ids.split(",")]
                payload["dataset_ids"] = dataset_ids
            document_ids = os.getenv("RAGFLOW_DOCUMENT_IDS")
            if document_ids:
                document_ids = [id.strip() for id in document_ids.split(",")]
                payload["document_ids"] = document_ids

            try:
                print(f"调用RAG系统检索接口: {url}, 查询: {query}")
                logger.info(f"调用RAG系统检索接口: {url}, 查询: {query}")
                response = requests.post(url, headers=headers, json=payload)
                logger.info(f"RAG系统响应状态码: {response.status_code}")
                print(f"RAG系统响应状态码: {response.status_code}")
                response.raise_for_status()

                result = response.json()
                if result.get("code") == 0:
                    chunks = result.get("data", {}).get("chunks", [])
                    if not chunks:
                        logger.info("RAG系统未找到相关数据块")
                        return "未找到相关数据块"
                    # 提取关键信息
                    contents = []
                    for chunk in chunks:
                        content = chunk.get("content", "")
                        similarity = chunk.get("similarity", 0)
                        contents.append(f"相关度: {similarity:.2f}\n内容: {content}")

                    logger.info(f"成功检索到{len(chunks)}个数据块")
                    print(f"成功检索到{len(chunks)}个数据块")
                    return "检索到的相关信息:\n" + "\n---\n".join(contents)
                else:
                    error_msg = f"检索失败: {result.get('message', '未知错误')}"
                    logger.error(f"RAG系统返回错误: {error_msg}, 完整响应: {result}")
                    return error_msg

            except requests.exceptions.RequestException as e:
                error_msg = f"检索过程中发生网络错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg
            except json.JSONDecodeError as e:
                error_msg = f"解析RAG系统响应失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg
            except Exception as e:
                error_msg = f"检索过程中发生未知错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg

        return Tool(
            name="rag_flow_retrieve",
            description="从RAG系统检索数据，用于获取更广泛的知识库信息",
            func=rag_flow_retrieve
        )
    def get_rag_flow_prompt_tool(self):
        from langchain_core.tools import Tool
        import json
        # RAG检索prompt工具
        def rag_flow_prompt_retrieve(query: str) -> str:
            """
            从RAG系统检索数据块
            Args:
                query: 用户查询问题
            """
            import requests
            # 获取环境变量中的API地址和密钥
            api_base_url = os.getenv("RAGFLOW_API_BASE")
            api_key = os.getenv("RAGFLOW_API_KEY")
            dataset_ids = os.getenv("RAGFLOW_DATASET_PROMPT_IDS")
            if not api_base_url or not api_key or not dataset_ids:
                error_msg = "RAG系统配置缺失，请检查RAGFLOW_API_BASE和RAGFLOW_API_KEY和RAGFLOW_DATASET_PROMPT_IDS环境变量"
                logger.error(error_msg)
                return error_msg

            url = api_base_url.rstrip('/')
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            # 构造请求体
            payload = {
                "question": query
            }
            dataset_ids = [id.strip() for id in dataset_ids.split(",")]
            payload["dataset_ids"] = dataset_ids
            # 可选参数
            document_ids = os.getenv("RAGFLOW_DOCUMENT_PROMPT_IDS")
            if document_ids:
                document_ids = [id.strip() for id in document_ids.split(",")]
                payload["document_ids"] = document_ids
            try:
                print(f"调用RAG系统检索接口: {url}, 查询: {query}")
                logger.info(f"调用RAG系统检索接口: {url}, 查询: {query}")
                response = requests.post(url, headers=headers, json=payload)
                logger.info(f"RAG系统响应状态码: {response.status_code}")
                print(f"RAG系统响应状态码: {response.status_code}")
                response.raise_for_status()

                result = response.json()
                if result.get("code") == 0:
                    chunks = result.get("data", {}).get("chunks", [])
                    if not chunks:
                        logger.info("RAG系统未找到相关数据块")
                        return "未找到相关数据块"
                    # 提取关键信息
                    contents = []
                    for chunk in chunks:
                        content = chunk.get("content", "")
                        similarity = chunk.get("similarity", 0)
                        contents.append(f"相关度: {similarity:.2f}\n内容: {content}")

                    logger.info(f"成功检索到{len(chunks)}个数据块")
                    print(f"成功检索到{len(chunks)}个数据块")
                    return "检索到的相关信息:\n" + "\n---\n".join(contents)
                else:
                    error_msg = f"检索失败: {result.get('message', '未知错误')}"
                    logger.error(f"RAG系统返回错误: {error_msg}, 完整响应: {result}")
                    return error_msg

            except requests.exceptions.RequestException as e:
                error_msg = f"检索过程中发生网络错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg
            except json.JSONDecodeError as e:
                error_msg = f"解析RAG系统响应失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg
            except Exception as e:
                error_msg = f"检索过程中发生未知错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return error_msg

        return Tool(
            name="rag_flow_prompt_retrieve",
            description="从RAG系统检索prompt，用于优化用户问题",
            func=rag_flow_prompt_retrieve
        )
