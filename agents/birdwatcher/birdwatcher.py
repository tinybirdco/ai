from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat

from agno.storage.postgres import PostgresStorage
from agno.tools.resend import ResendTools
from agno.tools.slack import SlackTools

import json
from agno.tools.reasoning import ReasoningTools
from agno.tools.thinking import ThinkingTools
import tempfile
import argparse

from prompts import *
from textwrap import dedent
from agno.tools.mcp import MCPTools
import os
import asyncio
from datetime import datetime
import glob

from dotenv import load_dotenv

MISSIONS = {}
missions_dir = os.path.join(os.path.dirname(__file__), 'missions')
for path in glob.glob(os.path.join(missions_dir, '*.md')):
    name = os.path.splitext(os.path.basename(path))[0]
    MISSIONS[name] = path

async def create_agno_agent(
    role="Autonomous Data Analyst",
    system_prompt=SYSTEM_PROMPT,
    instructions=None,
    mission=None,
    markdown=True,
    tinybird_host=None,
    tinybird_api_key=None,
    reasoning=False,
    slack_token=None,
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

    tools=[
        mcp_tools,
        SlackTools(token=slack_token or ""),
    ]

    resend_api_key = os.getenv("RESEND_API_KEY")
    if resend_api_key:
        tools.append(ResendTools(from_email="onboarding@resend.dev"))

    if reasoning:
        tools.append(ReasoningTools(add_instructions=True))
        tools.append(ThinkingTools(add_instructions=True))

    model = os.getenv("MODEL", "gemini-2.0-flash")
    if "gemini" in model:
        model = Gemini(
            id=model,
            vertexai=True,
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", ""),
        )
    elif "claude" in model:
        model = Claude(id=model)
    else:
        model = OpenAIChat(id=model)

    if mission:
        if mission in MISSIONS:
            with open(MISSIONS[mission], 'r') as f:
                mission_content = f.read()
            if instructions is None:
                instructions = [mission_content]
            elif isinstance(instructions, list):
                instructions.append(mission_content)
            else:
                instructions = [instructions, mission_content]
        else:
            if instructions is None:
                instructions = [mission]
            elif isinstance(instructions, list):
                instructions.append(mission)
            else:
                instructions = [instructions, mission]

    agent = Agent(
        model=model,
        role=role,
        name=role,
        session_state={"current_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        tools=tools,
        reasoning=reasoning,
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
        description=dedent(system_prompt).format(current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        instructions=instructions,
        # disabled
        search_previous_sessions_history=False,
        num_history_sessions=2,
        show_tool_calls=False,
        debug_mode=True,
        exponential_backoff=True,
    )

    return agent, mcp_tools, credentials_file


async def run_single_command(prompt, user_id="alrocar", instructions=None, reasoning=False, mission=None):
    """Run a single command and exit - useful for cron jobs"""
    load_dotenv()
    tinybird_api_key = os.getenv("TINYBIRD_TOKEN")
    if not tinybird_api_key:
        raise ValueError("TINYBIRD_TOKEN is not set")
    tinybird_host = os.getenv("TINYBIRD_HOST")
    memory_agent, mcp_tools, _ = await create_agno_agent(
        system_prompt=SYSTEM_PROMPT,
        instructions=instructions,
        mission=mission,
        tinybird_host=tinybird_host,
        tinybird_api_key=tinybird_api_key,
        reasoning=reasoning,
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


async def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Birdwatcher Agent - Interactive chat or single command mode")
    parser.add_argument("--prompt", "-p", type=str, help="Run a single command instead of interactive chat")
    parser.add_argument("--mission", "-m", type=str, help="The agent mission instructions. Choose from: " + ", ".join(MISSIONS.keys()))
    parser.add_argument("--user-id", "-u", type=str, default="alrocar", help="User ID for memory storage")
    
    args = parser.parse_args()
    
    # Single command mode
    if args.prompt:
        await run_single_command(args.prompt, args.user_id, mission=args.mission or "base")
        return
    
    # Interactive chat mode
    user_id = args.user_id
    tinybird_api_key = os.getenv("TINYBIRD_TOKEN")
    tinybird_host = os.getenv("TINYBIRD_HOST")
    memory_agent, mcp_tools, _ = await create_agno_agent(
        system_prompt=SYSTEM_PROMPT,
        # instructions=[dedent(ORGANIZATION_METRICS_PROMPT)] + [dedent(INVESTIGATION_TEMPLATES)],
        mission="explore",
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
