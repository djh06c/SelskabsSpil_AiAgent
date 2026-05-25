import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Selskabsspils Agent MCP")

N8N_BASE_URL = "http://localhost:5678/webhook"


@mcp.tool()
def recommend_games(equipment: str) -> str:
    """
    Anbefaler selskabsspil ud fra udstyr.
    Eksempel: equipment='Kort' returnerer spil som Fisk, Snyd og Vandfald.
    """
    response = requests.post(
        f"{N8N_BASE_URL}/recommend-games",
        json={"equipment": equipment},
        timeout=30
    )
    response.raise_for_status()
    return response.text


@mcp.tool()
def ask_rules(question: str) -> str:
    """
    Svarer på regelspørgsmål om Meyer, Fisk, Vandfald, Beer Pong og Snyd
    ved at kalde projektets Vector RAG workflow.
    """
    response = requests.post(
        f"{N8N_BASE_URL}/ask-rules",
        json={"question": question},
        timeout=60
    )
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    mcp.run()