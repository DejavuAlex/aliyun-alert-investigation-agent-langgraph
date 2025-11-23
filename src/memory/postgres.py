import os
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from log_config import get_logger

logger = get_logger(__name__)


def get_postgres_connection_string() -> str:
    """Build and return the PostgreSQL connection string from settings."""
    if os.getenv("POSTGRES_PASSWORD") is None:
        raise ValueError("POSTGRES_PASSWORD is not set")
    db_str = "postgresql://{}:{}@{}:{}/{}".format(
        os.getenv("POSTGRES_USER"),
        os.getenv("POSTGRES_PASSWORD"),
        os.getenv("POSTGRES_HOST"),
        os.getenv("POSTGRES_PORT"),
        os.getenv("POSTGRES_DB"),
    )
    logger.debug("PostgreSQL connection string: {}".format(db_str))
    return db_str


@asynccontextmanager
async def get_postgres_saver():
    """Initialize and return a PostgreSQL saver instance based on a connection pool for more resilent connections."""
    logger.info("set up database saver based on a connection pool...")
    if os.getenv("POSTGRES_APPLICATION_NAME") and os.getenv("POSTGRES_MIN_CONNECTIONS_PER_POOL") and os.getenv("POSTGRES_MAX_CONNECTIONS_PER_POOL"):
        application_name = os.getenv("POSTGRES_APPLICATION_NAME") + "-" + "saver"
    else:
        raise RuntimeError("POSTGRES_APPLICATION_NAME or POSTGRES_MIN_CONNECTIONS_PER_POOL or POSTGRES_MAX_CONNECTIONS_PER_POOL not set")

    async with AsyncConnectionPool(
        get_postgres_connection_string(),
        min_size=int(os.getenv("POSTGRES_MIN_CONNECTIONS_PER_POOL")),
        max_size=int(os.getenv("POSTGRES_MAX_CONNECTIONS_PER_POOL")),
        # Langgraph requires autocommmit=true and row_factory to be set to dict_row.
        # Application_name is passed so you can identify the connection in your Postgres database connection manager.
        kwargs={"autocommit": True, "row_factory": dict_row, "application_name": application_name},
        # makes sure that the connection is still valid before using it
        check=AsyncConnectionPool.check_connection,
    ) as pool:
        try:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            yield checkpointer
        finally:
            await pool.close()


@asynccontextmanager
async def get_postgres_store():
    """
    Get a PostgreSQL store instance based on a connection pool for more resilent connections.

    Returns an AsyncPostgresStore instance that can be used with async context manager pattern.

    """
    logger.info("set up database store based on a connection pool...")
    if os.getenv("POSTGRES_APPLICATION_NAME") and os.getenv("POSTGRES_MIN_CONNECTIONS_PER_POOL") and os.getenv("POSTGRES_MAX_CONNECTIONS_PER_POOL"):
        application_name = os.getenv("POSTGRES_APPLICATION_NAME") + "-" + "store"
    else:
        raise RuntimeError("POSTGRES_APPLICATION_NAME or POSTGRES_MIN_CONNECTIONS_PER_POOL or POSTGRES_MAX_CONNECTIONS_PER_POOL not set")

    async with AsyncConnectionPool(
        get_postgres_connection_string(),
        min_size=int(os.getenv("POSTGRES_MIN_CONNECTIONS_PER_POOL")),
        max_size=int(os.getenv("POSTGRES_MAX_CONNECTIONS_PER_POOL")),
        # Langgraph requires autocommmit=true and row_factory to be set to dict_row
        # Application_name is passed so you can identify the connection in your Postgres database connection manager.
        kwargs={"autocommit": True, "row_factory": dict_row, "application_name": application_name},
        # makes sure that the connection is still valid before using it
        check=AsyncConnectionPool.check_connection,
    ) as pool:
        try:
            store = AsyncPostgresStore(pool)
            await store.setup()
            yield store
        finally:
            await pool.close()
