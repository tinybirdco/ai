# @tinybirdco/ai

Tinybird utilities for your AI-based applications.

## Installation

```bash
npm install @tinybirdco/ai
# or
yarn add @tinybirdco/ai
# or
pnpm add @tinybirdco/ai
```

## Usage

Check out LLM Performance Tracker template to get started: https://github.com/tinybirdco/llm-performance-tracker

This package provides a wrapper for the AI SDK by Vercel that enables integration with Tinybird's analytics platform. Here's how to use it in your Next.js application:

### Next.js App Router API Route Example

```typescript
import { createOpenAI } from "@ai-sdk/openai";
import { wrapModel } from "@tinybirdco/ai/ai-sdk";
import { streamText } from "ai";

// Allow streaming responses up to 30 seconds
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

### Environment Variables

Make sure to set up the following environment variables in your `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
TINYBIRD_HOST=your_tinybird_host
TINYBIRD_TOKEN=your_tinybird_token
```

## Features

- Seamless integration with Vercel AI SDK
- Streaming support for real-time responses
- Easy configuration with Tinybird's analytics platform
- TypeScript support out of the box

## License

MIT
