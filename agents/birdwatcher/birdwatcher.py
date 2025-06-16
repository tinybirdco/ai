from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude
from agno.models.google import Gemini
# from agno.models.openai import OpenAIChat

from agno.storage.postgres import PostgresStorage
from rich.pretty import pprint
from agno.tools.resend import ResendTools
from agno.tools.slack import SlackTools

import json
from agno.tools.reasoning import ReasoningTools
import tempfile
import argparse
import sys

from prompts import *
from textwrap import dedent
from agno.tools.mcp import MCPTools
import os
import asyncio
from datetime import datetime

from dotenv import load_dotenv

async def create_agno_agent(
    role="Autonomous Data Analyst",
    system_prompt=SYSTEM_PROMPT,
    instructions=None,
    markdown=True,
    tinybird_host=None,
    tinybird_api_key=None,
):
    use_storage = os.getenv("PG_URL")
    if use_storage:
        db_url = os.getenv("PG_URL")
        memory = Memory(
            model=Claude(id="claude-4-sonnet-20250514"),
            db=PostgresMemoryDb(table_name="user_memories", db_url=db_url),
        )
        storage = PostgresStorage(table_name="bird_watcher_agent", db_url=db_url)

    if not tinybird_host:
        server_url = (
            f"https://cloud.tinybird.co/mcp?token={tinybird_api_key}"
        )
    else:
        server_url = (
            f"https://cloud.tinybird.co/mcp?token={tinybird_api_key}&host={tinybird_host}"
        )

    mcp_tools = MCPTools(
        transport="streamable-http", url=server_url, timeout_seconds=300
    )

    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    credentials_file = None

    if google_creds:
        try:
            creds_data = json.loads(google_creds)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(creds_data, f)
                credentials_file = f.name
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
        except json.JSONDecodeError:
            pass

    agent = Agent(
        model=Gemini(
            # id="gemini-2.5-pro-preview-06-05",
            # id="gemini-2.5-flash-preview-05-20",
            id="gemini-2.0-flash",
            vertexai=True,
            # api_key=os.getenv("VERTEX_API_KEY"),
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", ""),
        ),
        # model=OpenAIChat(id="o3-mini"),
        # model=Claude(id="claude-4-opus-20250514"),
        role=role,
        name=role,
        session_state={"current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        tools=[
            mcp_tools,
            ResendTools(from_email="onboarding@resend.dev"),
            SlackTools(),
            # ReasoningTools(add_instructions=True),
        ],
        # reasoning=True,
        # memory=memory,
        # enable_agentic_memory=True,
        # enable_user_memories=True,
        storage=storage if use_storage else None,
        add_history_to_messages=True,
        num_history_runs=5,
        markdown=markdown,
        read_chat_history=False,
        read_tool_call_history=False,
        enable_session_summaries=True,
        description=dedent(system_prompt),
        instructions=instructions,
        # disabled
        search_previous_sessions_history=False,
        num_history_sessions=2,
        show_tool_calls=False,
        debug_mode=True,
        exponential_backoff=True,
    )

    return agent, mcp_tools, credentials_file


async def run_single_command(prompt, user_id="alrocar", instructions=None):
    """Run a single command and exit - useful for cron jobs"""
    load_dotenv()
    tinybird_api_key = os.getenv("TINYBIRD_API_KEY")
    if not tinybird_api_key:
        raise ValueError("TINYBIRD_API_KEY is not set")
    tinybird_host = os.getenv("TINYBIRD_HOST")
    memory_agent, mcp_tools, _ = await create_agno_agent(
        system_prompt=SYSTEM_PROMPT,
        instructions=instructions,
        tinybird_host=tinybird_host,
        tinybird_api_key=tinybird_api_key,
    )

    async with mcp_tools:
        try:
            print(f"📝 Prompt: {prompt}")
            print("-" * 50)
            
            await memory_agent.aprint_response(
                prompt,
                user_id=user_id,
                stream=True,
                show_full_reasoning=True,
                show_reasoning=True,
                stream_intermediate_steps=True
            )
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


async def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Birdwatcher Agent - Interactive chat or single command mode")
    parser.add_argument("--prompt", "-p", type=str, help="Run a single command instead of interactive chat")
    parser.add_argument("--user-id", "-u", type=str, default="alrocar", help="User ID for memory storage")
    
    args = parser.parse_args()
    
    # Single command mode
    if args.prompt:
        await run_single_command(args.prompt, args.user_id)
        return
    
    # Interactive chat mode
    user_id = args.user_id
    tinybird_api_key = os.getenv("TINYBIRD_API_KEY")
    tinybird_host = os.getenv("TINYBIRD_HOST")
    memory_agent, mcp_tools, _ = await create_agno_agent(
        system_prompt=SYSTEM_PROMPT,
        # instructions=[dedent(ORGANIZATION_METRICS_PROMPT)] + [dedent(INVESTIGATION_TEMPLATES)],
        instructions=[dedent(EXPLORATIONS_PROMPT)],
        tinybird_host=tinybird_host,
        tinybird_api_key=tinybird_api_key,
        role="Analytics Agent",
    )

    print("🤖 Birdwatcher Chat CLI")
    print("Type 'exit' to quit")
    print("Example: Find pipes with the most errors in the last 24 hours")
    print("-" * 50)

    async with mcp_tools:
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                if user_input.lower() == "exit":
                    print("\n👋 Goodbye!")
                    break

                await memory_agent.aprint_response(
                    user_input,
                    user_id=user_id,
                    stream=True,
                    stream_intermediate_steps=False,
                )
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue


if __name__ == "__main__":
    asyncio.run(main())
