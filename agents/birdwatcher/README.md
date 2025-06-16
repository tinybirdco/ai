# Birdwatcher

Birdwatcher is an AI agent that provides data analysis capabilities for your Tinybird Organization.

It connects to the [Tinybird MCP server](https://www.tinybird.co/docs/forward/work-with-data/mcp) using your organization’s admin token and enables conversational analytics via natural language.

Birdwatcher can answer questions such as:
- _What's my storage usage?_
- _What are the pipes with more errors in the last 24 hours?_
- _What are the datasources with more rows in quarantine in the last hour?_

You can run Birdwatcher as a standalone agent (locally or scheduled), or connect it to a Slack bot for a conversational experience and proactive reminders about key metrics.

## 📂 Project structure

- `/api` -> Contains the Slack API that connects `@Birdwatcher` to Slack
- `/tinybird` -> Tinybird project to manage the `@Birdwatcher` user configuration
- `birdwatcher.py` -> Main agent logic; usable as standalone or via Slack
- `prompts.py` -> Default prompt templates you can customize

## 💭 Birdwatcher Slack Agent

Birdwatcher integrates into Slack and enables you to query your Tinybird metrics using natural language.

### ✅ Usage

1. Invite `@Birdwatcher` to a channel or open a DM
2. Run `/birdwatcher-config` slash command to configure your Tinybird organization admin token and host
![birdwatcher-config](./birdwatcher-config.png)
3. Mention `@Birdwatcher` to ask questions about your workspaces or organization
![birdwatcher-thread](./birdwatcher-thread.png)



### 🚀 Deployment guide

Deploy Birdwatcher as a multi-tenant Slack app using Railway, or your preferred hosting provider

Pre-requisites:
1. Railway account
2. Create a [Slack app](https://api.slack.com/apps)
3. Tinybird account

#### Step 1: Deploy the Tinybird project

```bash
cd ai/agents/birdwatcher/tinybird
curl https://tinybird.co | sh
tb login
tb --cloud deploy

# Use this token later on as TINYBIRD_BIRDWATCHER_TOKEN
tb token copy "admin token"
```

#### Step 2: Deploy the Slack Bot API (via Railway)

```bash
# Install the Railway CLI
brew install railway             # macOS
npm install -g @railway/cli     # any OS

cd ai/agents/birdwatcher

# Login and initialize project
railway login
railway init

# Deploy from local directory
railway up

# Set required environment variables
railway variables --set SLACK_TOKEN=xoxb-your-bot-token
railway variables --set SLACK_BOT_USER_ID=your-bot-user-id
railway variables --set TINYBIRD_BIRDWATCHER_TOKEN=your-admin-token
railway variables --set ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Gemini model config
railway variables --set GOOGLE_APPLICATION_CREDENTIALS='{"type":...}'  # Full JSON
railway variables --set GOOGLE_CLOUD_PROJECT=
railway variables --set GOOGLE_CLOUD_LOCATION=

# Optional extras
railway variables --set PG_URL=your-postgres-connection-url
railway variables --set RESEND_API_KEY=your-resend-api-key

# Final deployment
railway up

# Retrieve deployment domain
railway domain
```

#### Step3: Slack App Configuration

Use this `App Manifest`

```yaml
display_information:
  name: Birdwatcher
  description: An agent to analyze Tinybird organization metrics
  background_color: "#0a0a0a"
  long_description: "1. Invite the app to any channel or write DMs to it\r

    2. Use `/birdwatcher-config` to configure your Tinybird token and host\r

    3. Mention `@Birdwatcher` to ask questions about your workspaces or organization"
features:
  bot_user:
    display_name: Birdwatcher
    always_online: true
  slash_commands:
    - command: /birdwatcher-config
      url: https://<YOUR_RAILWAY_DOMAIN>/api/slack
      description: configure tokens
      should_escape: false
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history
      - chat:write
      - im:history
      - im:read
      - im:write
      - groups:history
      - commands
settings:
  event_subscriptions:
    request_url: https://<YOUR_RAILWAY_DOMAIN>/api/slack
    bot_events:
      - app_home_opened
      - app_mention
      - message.channels
      - message.groups
      - message.im
  interactivity:
    is_enabled: true
    request_url: https://<YOUR_RAILWAY_DOMAIN>/api/slack
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

### 🧪 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (check .env.example for the complete list)
export SLACK_TOKEN=your-token
export SLACK_BOT_USER_ID=your-bot-user-id
export ...
...
export PORT=8000

# Run locally
python server.py

# Use ngrok to test the Slack app with your local server
ngrok http 8000
```

## 🔁 Standalone Birdwatcher Agent

You can run Birdwatcher outside of Slack for manual queries or scheduled background tasks.

### ⚙️ Required Environment Variables

Create a `.env` file with the following:

```bash
# Birdwatcher uses gemini models via VertexAI
GOOGLE_APPLICATION_CREDENTIALS='{"type": "service_account","project_id": ...}'
VERTEX_API_KEY=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=

# Tinybird Token and Host. Use organization admin token
TINYBIRD_API_KEY=
TINYBIRD_HOST=

# Optional if you use storage or memory
ANTHROPIC_API_KEY=
PG_URL=

# Optional tools to notify via email or Slack
RESEND_API_KEY=
SLACK_TOKEN=
SLACK_BOT_USER_ID=
```

### 📦 Install

```bash
uv sync
```

### 💬 Run in CLI mode

This is useful for an interactive conversational interface with your Tinybird organization metrics and workspaces

```sh
uv run python birdwatcher.py
🤖 Birdwatcher Chat CLI
Type 'exit' to quit
Example: Find pipes with the most errors in the last 24 hours
```

### 🔁 Run in ambient mode

Use this mode to run an ambient agent on schedule that notifies via Slack or e-mail.

This mode uses by default the `INVESTIGATION_TEMPLATES` prompt, to notify to Slack about CPU spikes in your organization and find culprits. Adapt the prompt to your specific needs.

```sh
uv run python birdwatcher.py --prompt "investigate cpu spikes in the last day and notify to #tmp-birdwatcher Slack channel"
```