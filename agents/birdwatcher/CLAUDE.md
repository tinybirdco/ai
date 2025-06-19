# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Environment
- **Setup**: `uv sync` (installs dependencies)
- **Main entry point**: `uv run python birdwatcher.py`
- **Linting**: `uv run ruff check` (follows tool.ruff config in pyproject.toml)
- **Server**: `python server.py` (runs Slack bot server on port 8000)

### Running Birdwatcher
- **Interactive CLI mode**: `uv run python birdwatcher.py` (no arguments)
- **Single query**: `uv run python birdwatcher.py --prompt "your query" --mission base`
- **With notifications**: Include Slack channel (#channel) or email in prompt for notifications

### Testing Specific Components
- **Check notifications**: `python check_notifications.py`
- **Daily summary**: `python daily_summary.py`

## Architecture

### Core Components
- **birdwatcher.py**: Main agent entry point using Agno framework with Claude models
- **prompts.py**: System prompts and rules for data analysis behavior
- **server.py**: Slack bot server using aiohttp
- **api/**: API integrations (Slack, Tinybird, thinking messages)

### Mission System
- **missions/**: Predefined analysis instructions as markdown files
- Available missions: base, cpu_spikes, daily_summary, explore
- Missions guide agent behavior for specific analysis types

### Data Integration
- Uses **MCP (Model Context Protocol)** to connect to Tinybird
- **tinybird/**: Contains datasource and endpoint definitions
- Agent has tools to explore data, list datasources/endpoints

### Agent Framework
- Built on **Agno framework** with multiple model support (Claude, Gemini, OpenAI)
- Memory persistence via PostgreSQL when PG_URL is configured
- Tools: MCP, Slack, Resend (email), Reasoning, Thinking

### Key Patterns
- All datetime operations use ClickHouse dialect and YYYY-MM-DD HH:MM:SS format
- Service data source duration metrics are in seconds
- Auto-retry failed tools once with error context
- Notifications sent via Slack or email when specified in prompts

### Environment Variables Required
- TINYBIRD_TOKEN, TINYBIRD_HOST
- ANTHROPIC_API_KEY (or other model API keys)
- Optional: SLACK_TOKEN, RESEND_API_KEY, PG_URL