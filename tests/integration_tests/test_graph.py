import asyncio
import ssl

import nltk
import pytest
import os
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from openai import api_key

from agent import graph
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent.agentic_RAG_agent import AgenticRAGSystem

pytestmark = pytest.mark.anyio
import dotenv
dotenv.load_dotenv()

@pytest.mark.langsmith
async def test_agent_simple_passthrough() -> None:
    inputs = {"changeme": "some_val"}
    res = await graph.ainvoke(inputs)
    assert res is not None


async def _test_call_mpc_tools():
    print("get hte mcp server is {}".format(os.getenv("MCP_SERVER_ENDPOINT")))
    client = MultiServerMCPClient(
        {
            "aliyun_actiontrail_mcp_server": StreamableHttpConnection(
                url=os.getenv("MCP_SERVER_ENDPOINT"),
                # headers={
                #     "Authorization": f"Bearer {os.getenv('MCP_SERVER_API_KEY')}",
                #     "X-Custom-Header": "CustomValue"
                # },
                transport="streamable_http"
            )
        }

    )
    tools =  await asyncio.gather(client.get_tools())
    print("tools are {}".format(tools))

def test_call_mpc_tools():
    asyncio.run(_test_call_mpc_tools())

def test_rag_tool():
   tools = AgenticRAGSystem("../../src/knowledge-deprecate").get_local_rag_tool()
   print(tools.name)


def test_download_nltk_data():
    import sys
    try:
        # 创建未验证的SSL上下文
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        # 设置NLTK数据目录
        nltk_data_dir = os.path.expanduser("~/nltk_data")
        if not os.path.exists(nltk_data_dir):
            os.makedirs(nltk_data_dir)

        # 设置下载路径
        nltk.data.path.append(nltk_data_dir)

        # 下载必要的NLTK数据包
        print("开始下载NLTK数据包...")
        packages = [
            'punkt',
            'punkt_tab',
            'averaged_perceptron_tagger',
            'averaged_perceptron_tagger_eng',  # 添加英语标注器
            'maxent_ne_chunker',
            'words',
            'perluniprops',  # 用于Unicode属性
            'universal_tagset',  # 通用标记集
            'nonbreaking_prefixes'  # 非断句前缀
        ]

        for package in packages:
            try:
                print(f"正在下载 {package}...")
                nltk.download(package, download_dir=nltk_data_dir, quiet=False)
                print(f"{package} 下载成功")
            except Exception as e:
                print(f"下载 {package} 时出错: {str(e)}")

        print("\n所有数据包下载完成")
        print(f"NLTK数据目录: {nltk.data.path}")

        # 验证关键包是否可用
        try:
            from nltk.tokenize import sent_tokenize
            from nltk.tag import pos_tag

            # 测试分句
            test_text = "This is a test sentence. This is another test sentence."
            sentences = sent_tokenize(test_text)

            # 测试词性标注
            words = nltk.word_tokenize(test_text)
            tags = pos_tag(words)

            print("\n验证测试成功！NLTK功能正常工作。")
            print(f"词性标注示例: {tags[:3]}")

        except Exception as e:
            print(f"\n验证测试失败: {str(e)}")
            sys.exit(1)

    except Exception as e:
        print(f"发生错误: {str(e)}")

