import asyncio

from fastapi import FastAPI
from langchain_core.runnables import RunnableLambda
from langserve import add_routes

# Import the prepared agent instance
from agent.roche_siem_agent import roche_siem_agent

agent_runnable = None

async def lifespan(app: FastAPI):
    global agent_runnable
    agent_runnable = roche_siem_agent
    add_routes(app, agent_runnable, path="/ai_siem")
    yield  # Optional cleanup after shutdown
app = FastAPI(title="Roche SIEM Agent",lifespan=lifespan)

# Expose the agent (Runnable) at /ai_siem




@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/ai_siem/invoke", "/ai_siem/stream"]}

# Optional local run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

