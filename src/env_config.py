import os
from pathlib import Path

from dotenv import load_dotenv


def set_env():
    env_path = Path(__file__).parent.parent
    app_env = os.getenv("APP_ENV", "dev")
    app_env_normalized = app_env.strip().lower()

    if not app_env_normalized:
        print("[env] APP_ENV empty, fallback to 'dev'")
        app_env_normalized = "dev"

    if app_env_normalized == "dev":
        env_file = env_path / ".env.dev"
    else:
        env_file = env_path / ".env"

    if not env_file.exists():
        print(f"[env] WARNING file not found: {env_file}")
    else:
        # override=True 确保覆盖之前已加载的变量
        load_dotenv(env_file, override=True)
        print(f"[env] Loaded: {env_file}")

    # 调试输出
    print(f"[env] APP_ENV(raw)='{app_env}' normalized='{app_env_normalized}'")
    # print(f"[env] MCP_SERVER_ENDPOINT='{os.getenv('MCP_SERVER_ENDPOINT')}'")


