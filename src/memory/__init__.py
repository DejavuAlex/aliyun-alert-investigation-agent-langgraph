from contextlib import AbstractAsyncContextManager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from memory.postgres import get_postgres_saver, get_postgres_store


def initialize_database() -> AbstractAsyncContextManager[
    AsyncPostgresSaver
]:
    """
    Initialize the appropriate database checkpointer based on configuration.
    Returns an initialized AsyncCheckpointer instance.
    """
    return get_postgres_saver()



def initialize_store():
    """
    Initialize the appropriate store based on configuration.
    Returns an async context manager for the initialized store.
    """
    return get_postgres_store()



__all__ = ["initialize_database", "initialize_store"]
