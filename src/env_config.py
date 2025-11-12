import os

def set_env():
    from pathlib import Path
    env_path = Path(__file__).parent.parent
    from dotenv import load_dotenv
    APP_ENV = os.getenv("APP_ENV","dev")
    if APP_ENV:
        if APP_ENV == "dev":
            load_dotenv(f"{env_path}/.env.{APP_ENV}")
        else:
            load_dotenv(f"{env_path}.env")


