Birdwatcher Notifications is an open-source background agent that monitors your Tinybird workspace based on a prompt and sends notifications as instructed

## Quickstart

Use it locally by passing a prompt, and optionally specify a Slack channel or email address where you want to receive the response

```sh
git clone git@github.com:tinybirdco/ai.git
cd ai/agents/birdwatcher
# Fill in the required environment variables for your Tinybird account and LLMs. Optionally, provide your Slack or Resend API keys to enable notifications
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
          prompt: 'Report endpoint errors in the last 24 hours. Send a Slack message to #tmp-birdwatcher with the results. No markdown.'
          mission: base
          model: 'claude-4-sonnet-20250514'
```

## Missions

Missions are predefined instructions that guide the Birdwatcher agent to perform specific analyses

You can find the available missions in the [GitHub repository](https://github.com/tinybirdco/ai/tree/main/agents/birdwatcher/missions)

To use a mission, provide both a prompt and the name of the mission (Markdown file):

```sh
uv run python birdwatcher.py \
   --prompt "Investigate cpu spikes in the last hour" \
   --mission cpu_spikes
```

You can contribute your own missions or use the `--mission` flag to instruct the agent to run a custom analysis.

```sh
uv run python birdwatcher.py \
   --prompt "Analyze my web analytics metrics in the last month" \
   --mission "<Your custom mission rules>"
```
