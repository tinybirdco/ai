Birdwatcher is an open-source agent that provides data analysis capabilities for your data in Tinybird

It connects to the [Tinybird MCP server](https://www.tinybird.co/docs/forward/work-with-data/mcp) using your Tinybird token and enables analytics via natural language

## Quickstart

Use it locally by passing a prompt, and optionally specify a Slack channel or email address where you want to receive the response notification

```sh
git clone git@github.com:tinybirdco/ai.git
cd ai/agents/birdwatcher
# Fill in the required environment variables for your Tinybird account and LLMs.
# Optionally, provide your Slack or Resend API keys to enable notifications
cp .env.example .env
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run python birdwatcher.py \
   --prompt "analyse website visits and notify me on #tmp-birdwatcher" \
   --mission base
```

Schedule it as a GitHub Action:

```yaml
name: Birdwatcher Endpoint Errors Monitor

on:
  schedule:
    - cron: '0 9 * * *'  # Runs daily at 9:00 UTC
  workflow_dispatch:      # Allows manual triggering

jobs:
  monitor-endpoint-errors:
    runs-on: ubuntu-latest
    steps:
      - uses: tinybirdco/ai@main
        with:
          slack_token: ${{ secrets.SLACK_TOKEN }}
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          tinybird_token: ${{ secrets.TINYBIRD_TOKEN }}
          tinybird_host: ${{ secrets.TINYBIRD_HOST }}
          prompt: |
            Report endpoint errors in the last 24 hours.
            Send a Slack message to #tmp-birdwatcher with the results.
            No markdown.
          mission: base
          model: 'claude-4-sonnet-20250514'
```

## Missions

Missions are predefined instructions that guide the Birdwatcher agent to perform specific analyses

You can find the available missions in the [GitHub repository](https://github.com/tinybirdco/ai/tree/main/agents/birdwatcher/missions)

To use a mission, provide both a prompt and the name of the mission (Markdown file):

```sh
uv run python birdwatcher.py \
   --prompt "Investigate cpu spikes in the last hour and notify to alrocar@tinybird.co" \
   --mission cpu_spikes
```

You can contribute your own missions or use the `--mission` flag to instruct the agent to run a custom analysis.

```sh
uv run python birdwatcher.py \
   --prompt "Analyze my web analytics metrics in the last month. Notify in #website-metrics" \
   --mission "<Your custom mission rules>"
```

## CLI mode

```plaintext
uv run python birdwatcher.py
🤖 Birdwatcher Chat CLI
--------------------------------------------------

💬 You: top 5 pages with more visits in the last 24 hours
┏━ Message ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                               ┃
┃ top 5 pages with more visits in the last 24 hours                             ┃
┃                                                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┏━ Response (26.1s) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                               ┃
┃ Here are the top 5 most visited pages in the last 24 hours:                   ┃
┃                                                                               ┃
┃  1 Homepage (/) - 153 visits                                                  ┃
┃  2 Documentation quick start page (/docs/forward/get-started/quick-start)     ┃
┃   - 50 visits                                                                 ┃
┃  3 Pricing page (/pricing) - 42 visits                                        ┃
┃  4 Templates page (/templates) - 21 visits                                    ┃
┃  5 Product page (/product) - 21 visits                                        ┃
┃                                                                               ┃
┃ The homepage is by far the most visited page, with nearly three times as      ┃
┃ many visits as the second most popular page.                                  ┃
┃                                                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
┏━ Session Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                               ┃
┃ Session summary updated                                                       ┃
┃                                                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```
