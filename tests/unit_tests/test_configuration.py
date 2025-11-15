import os

from langgraph.pregel import Pregel

from agent.graph import graph
from client.roche_RAG_SAAS_client import Roche_RAG_SAAS_client
from env_config import set_env
from logger_config import get_logger


logger = get_logger(__name__)

def test_placeholder() -> None:
    # TODO: You can add actual unit tests
    # for your graph and other logic here.
    assert isinstance(graph, Pregel)

def test_remove_all_collections_in_RAAS():
    set_env()
    print("get google drive:", os.getenv("GOOGLE_SHARE_DRIVE"))
    print("get RAAS API KEY:", os.getenv("RAAS_API_KEY"))
    roche_rag_saas_client = Roche_RAG_SAAS_client(
        google_share_drive=os.getenv("GOOGLE_SHARE_DRIVE"),
        embedding_model=os.getenv("LLM_EMBEDDING_MODEL"),
        base_url=os.getenv("RAAS_BASE_URL"),
        rass_api_key=os.getenv("RAAS_API_KEY"),
        api_id=os.getenv("API_ID"),
        portkey_api_key=os.getenv("LLM_API_KEY")
    )
    collections = roche_rag_saas_client.list_collections()
    logger.info("get collections from RAAS: %s", collections)
