import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError(
        "Mangler Neo4j miljøvariabler. Tjek .env: "
        "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE"
    )

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

mcp = FastMCP("Selskabsspils MCP Server")


def run_query(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Kører en Cypher-query mod Neo4j og returnerer resultater som dictionaries."""
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


def normalize_text(text: str) -> str:
    return text.lower().strip()


def equipment_keywords_from_question(question: str) -> list[str]:
    """
    Simpel natural-language mapping.
    Formålet er ikke at lave fuld AI her, men at demonstrere at MCP-tool kan
    omsætte brugerinput til Neo4j-opslag.
    """
    q = normalize_text(question)

    keyword_map = {
        "kort": ["kort", "spillekort", "cards", "card"],
        "terning": ["terning", "terninger", "dice", "die"],
        "kop": ["kop", "kopper", "cups", "cup"],
        "bold": ["bold", "bolde", "ping pong", "pingpong", "ball"],
        "øl": ["øl", "alkohol", "beer"],
    }

    found = []

    for equipment_name, keywords in keyword_map.items():
        if any(keyword in q for keyword in keywords):
            found.append(equipment_name)

    return found


@mcp.tool()
def get_supported_games() -> list[dict[str, Any]]:
    """
    Returnerer alle spil som findes i Neo4j.
    """
    query = """
    MATCH (g:Game)
    OPTIONAL MATCH (g)-[:USES]->(e:Equipment)
    OPTIONAL MATCH (g)-[:HAS_CATEGORY]->(c:Category)
    RETURN
        g.name AS name,
        g.players AS players,
        g.purpose AS purpose,
        collect(DISTINCT e.name) AS equipment,
        collect(DISTINCT c.name) AS categories
    ORDER BY name
    """

    return run_query(query)


@mcp.tool()
def recommend_games_by_equipment(question: str) -> dict[str, Any]:
    """
    Anbefaler spil baseret på udstyr nævnt i naturlig tekst.
    Eksempel: 'Vi har kort. Hvilket spil kan vi spille?'
    """
    equipment_keywords = equipment_keywords_from_question(question)

    if not equipment_keywords:
        return {
            "question": question,
            "detected_equipment": [],
            "games": [],
            "message": "Jeg kunne ikke finde noget kendt udstyr i spørgsmålet."
        }

    query = """
    MATCH (g:Game)-[:USES]->(e:Equipment)
    WHERE toLower(e.name) IN $equipment
    OPTIONAL MATCH (g)-[:HAS_CATEGORY]->(c:Category)
    OPTIONAL MATCH (g)-[:HAS_DOCUMENT]->(d:Document)
    RETURN
        g.name AS name,
        g.players AS players,
        g.purpose AS purpose,
        collect(DISTINCT e.name) AS matched_equipment,
        collect(DISTINCT c.name) AS categories,
        collect(DISTINCT d.title) AS documents
    ORDER BY name
    """

    games = run_query(query, {"equipment": equipment_keywords})

    return {
        "question": question,
        "detected_equipment": equipment_keywords,
        "games": games,
        "message": f"Fandt {len(games)} relevante spil baseret på udstyr."
    }


@mcp.tool()
def get_game_info(game_name: str) -> dict[str, Any]:
    """
    Returnerer detaljer om et bestemt spil.
    Eksempel: 'Meyer'
    """
    cleaned_name = re.sub(r"\s+", " ", game_name).strip()

    query = """
    MATCH (g:Game)
    WHERE toLower(g.name) = toLower($game_name)
    OPTIONAL MATCH (g)-[:USES]->(e:Equipment)
    OPTIONAL MATCH (g)-[:HAS_CATEGORY]->(c:Category)
    OPTIONAL MATCH (g)-[:HAS_DOCUMENT]->(d:Document)
    RETURN
        g.name AS name,
        g.players AS players,
        g.purpose AS purpose,
        g.rules AS rules,
        collect(DISTINCT e.name) AS equipment,
        collect(DISTINCT c.name) AS categories,
        collect(DISTINCT {
            title: d.title,
            content: d.content
        }) AS documents
    LIMIT 1
    """

    result = run_query(query, {"game_name": cleaned_name})

    if not result:
        return {
            "game_name": game_name,
            "found": False,
            "message": "Spillet blev ikke fundet i Neo4j."
        }

    game = result[0]
    game["found"] = True
    return game


if __name__ == "__main__":
    mcp.run(transport="stdio")