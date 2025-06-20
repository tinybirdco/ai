# Tinybird AI Utilities

A comprehensive toolkit of AI-powered utilities for Tinybird, enabling intelligent data analysis, monitoring, and integration capabilities.

## 🚀 What's Inside

This repository contains powerful AI utilities designed to enhance your Tinybird experience:

- **🐦 Birdwatcher**: An intelligent agent for automated data analysis and monitoring
- **📦 JavaScript SDK**: Seamless integration with Vercel AI SDK for web applications

---

## 🐦 Birdwatcher Agent

Birdwatcher is an open-source AI agent that provides intelligent data analysis capabilities for your Tinybird data. It connects to the [Tinybird MCP server](https://www.tinybird.co/docs/forward/work-with-data/mcp) and enables analytics via natural language.

<a href="https://slack.com/oauth/v2/authorize?client_id=1689466861365.9006719895489&scope=app_mentions:read,channels:history,chat:write,im:history,im:read,im:write,groups:history,commands&user_scope="><img alt="Add to Slack" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcSet="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>

### Quick Start

**Local Usage:**
```sh
git clone git@github.com:tinybirdco/ai.git
cd ai/agents/birdwatcher
cp .env.example .env  # Configure your environment variables
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run python birdwatcher.py \
   --prompt "analyse website visits and notify me on #tmp-birdwatcher" \
   --mission base
```

**GitHub Actions:**
```yaml
name: Birdwatcher Endpoint Errors Monitor

on:
  schedule:
    - cron: '0 9 * * *'  # Runs daily at 9:00 UTC
  workflow_dispatch:

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

### Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Automated Monitoring**: Set up scheduled analysis and alerts
- **Slack Integration**: Receive notifications directly in your Slack channels
- **Mission System**: Predefined analysis templates for common use cases
- **CLI Mode**: Interactive chat interface for data exploration

### Missions

Missions are predefined instructions that guide Birdwatcher to perform specific analyses. Available missions include:
- **Base**: General data analysis
- **CPU Spikes**: Infrastructure monitoring
- **Daily Summary**: Regular reporting
- **Explore**: Data discovery

[View all missions →](https://github.com/tinybirdco/ai/tree/main/agents/birdwatcher/missions)

---

## 📦 JavaScript Tools

The `@tinybirdco/ai` package provides seamless integration between Vercel AI SDK and Tinybird's analytics platform, enabling you to track and analyze AI model performance in your web applications.

### Installation

```bash
npm install @tinybirdco/ai
# or
yarn add @tinybirdco/ai
# or
pnpm add @tinybirdco/ai
```

### Quick Start

**Next.js App Router Example:**
```typescript
import { createOpenAI } from "@ai-sdk/openai";
import { wrapModel } from "@tinybirdco/ai/ai-sdk";
import { streamText } from "ai";

export const maxDuration = 30;

export async function POST(req: Request) {
  const { messages } = await req.json();

  const openai = createOpenAI({
    apiKey: process.env.OPENAI_API_KEY,
  });

  const model = wrapModel(openai("chatgpt-4o-latest"), {
    host: process.env.TINYBIRD_HOST!,
    token: process.env.TINYBIRD_TOKEN!,
  });

  const result = streamText({
    model: model,
    messages,
  });

  return result.toDataStreamResponse();
}
```

### Features

- **Vercel AI SDK Integration**: Seamless compatibility with Vercel's AI SDK
- **Streaming Support**: Real-time response streaming
- **Performance Tracking**: Monitor AI model performance and usage
- **TypeScript Support**: Full type safety out of the box

### Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key
TINYBIRD_HOST=your_tinybird_host
TINYBIRD_TOKEN=your_tinybird_token
```

---

## 🛠️ Getting Started

1. **Choose Your Tool**: 
   - Use Birdwatcher for automated data analysis and monitoring
   - Use the JavaScript SDK for web application integration

2. **Set Up Your Environment**: Configure your Tinybird credentials and API keys

3. **Start Building**: Follow the quick start guides above to get up and running

## 📚 Documentation

- [Birdwatcher Documentation](agents/birdwatcher/README.md)
- [JavaScript SDK Documentation](js/README.md)
- [Tinybird MCP Server](https://www.tinybird.co/docs/forward/work-with-data/mcp)
- [LLM Performance Tracker Template](https://github.com/tinybirdco/llm-performance-tracker)

## 🤝 Contributing

We welcome contributions! Please check out our contributing guidelines and feel free to submit pull requests or open issues.

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.
