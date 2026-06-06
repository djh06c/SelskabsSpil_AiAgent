import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = PROJECT_ROOT / "src" / "scripts" / "mcp_server.py"


def pretty_print(title: str, data: Any) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(data)
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def extract_tool_result(result: Any) -> Any:
    """
    MCP returnerer typisk content-lister.
    Denne funktion gør output mere læsbart i terminalen.
    """
    if not hasattr(result, "content"):
        return str(result)

    extracted = []

    for item in result.content:
        if hasattr(item, "text"):
            text = item.text

            try:
                extracted.append(json.loads(text))
            except json.JSONDecodeError:
                extracted.append(text)
        else:
            extracted.append(str(item))

    if len(extracted) == 1:
        return extracted[0]

    return extracted


async def main() -> None:
    if not SERVER_PATH.exists():
        raise FileNotFoundError(f"Kan ikke finde MCP-serveren: {SERVER_PATH}")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            pretty_print(
                "MCP tools fundet",
                [tool.name for tool in tools.tools]
            )

            result = await session.call_tool("get_supported_games", {})
            pretty_print(
                "Tool 1: get_supported_games()",
                extract_tool_result(result)
            )

            result = await session.call_tool(
                "recommend_games_by_equipment",
                {
                    "question": "Vi har kort. Hvilket spil kan vi spille?"
                }
            )
            pretty_print(
                "Tool 2: recommend_games_by_equipment(question)",
                extract_tool_result(result)
            )

            result = await session.call_tool(
                "get_game_info",
                {
                    "game_name": "Meyer"
                }
            )
            pretty_print(
                "Tool 3: get_game_info(game_name)",
                extract_tool_result(result)
            )


if __name__ == "__main__":
    asyncio.run(main())