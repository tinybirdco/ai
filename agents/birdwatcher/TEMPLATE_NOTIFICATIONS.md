Birdwatcher Notifications is a background open source agent that monitors your Tinybird workspace according to a prompt and notifies you as instructed

## Quickstart

Use it locally:

```sh
git clone git@github.com:tinybirdco/ai.git
cd nombre_del_repo/agents/birdwatcher
# fill in environment variables for your Tinybird account and LLMs
cp .env.example .env 
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run python birdwatcher.py –prompt “analyse website visits and notify me on #tmp-birdwatcher”
```

Schedule as a GitHub Action:

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
          model: 'claude-4-sonnet-20250514'
```
