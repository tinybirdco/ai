## 💭 Birdwatcher Slack Agent

Birdwatcher integrates into Slack and enables you to query your data in Tinybird using natural language.

### ✅ Usage

1. Deploy Birdwatcher to your Slack workspace.
2. Invite `@Birdwatcher` to a channel or open a DM
3. Run `/birdwatcher-config` slash command to configure your Tinybird admin token and host (or organization admin token)
![birdwatcher-config](./birdwatcher-config.png)
4. Mention `@Birdwatcher` or DM it and ask questions about your data in Tinybird
![birdwatcher-thread](./birdwatcher-thread.png)

### 🚀 Deployment guide

Birdwatcher is deployed as a web server which publishes an `api/slack` API endpoint that connects with a Slack app to subscribe to Slack events and route accordingly to the Birdwatcher agent.

This is the general architecture.

```
                              ┌─────────────┐
                              │ Slack App   │
                              │             │
                              └─────────────┘
                                       |
                              event subscription
                                       |
                                       v
                       ┌─────────────────────┐
                       │ Birdwatcher Web     │
                       │ Server              │
                       └─────────────────────┘
                              |
                              v
                       ┌─────────────────┐
                       │ Birdwatcher     │
                       │ Agent           │
                       └─────────────────┘
                              |
                       +------+------+
                       |             |
              get user/channel token  token
                       |             |
                       v             v
            ┌───────────────────┐   ┌──────────────┐
            │birdwatcher_config │   │ Tinybird     │
            │                   │   │ MCP          │
            └───────────────────┘   └──────────────┘
                                           |
                                           token
                                           |
                                           v
                                    ┌─────────────────┐
                                    │ Your Tinybird   │
                                    │ Workspace       │
                                    └─────────────────┘
```
Deployment steps

1. Deploy the Birdwatcher web server
2. Deploy the Tinybird `birdwatcher_config` workspace
3. Create a [Slack app](https://api.slack.com/apps)
4. Configure the environment variables
5. Configure the Slack app


**Step 1: Deploy the Birdwatcher web server**

Deploying the Birdwatcher web server is out of the scope of this guide, just use your preferred PaaS (Railway, Fly, Heroku, etc.). You can use the [Dockerfile](./Dockerfile) provided.

**Step 2: Deploy the Tinybird `birdwatcher_config` workspace**

`/birdwatcher-config` stores the `@Birdwatcher` credentials in a Tinybird workspace. Deploy it following the next steps:

```bash
cd ai/agents/birdwatcher/tinybird
curl https://tinybird.co | sh
tb login
tb --cloud deploy

# Use this token later on as TINYBIRD_BIRDWATCHER_TOKEN
tb token copy "admin token"
```

**Step 3: Create a Slack app**

Copy the Slack bot token and get the Slack bot user id:

```sh
curl -H "Authorization: Bearer <YOUR_SLACK_TOKEN>" https://slack.com/api/auth.test
```

**Step 4: Configure the environment variables**

Configure the next environment variables in the PaaS where you deployed the Birdwatcher web server

```sh
SLACK_TOKEN=xoxb-your-bot-token
SLACK_BOT_USER_ID=your-bot-user-id
TINYBIRD_BIRDWATCHER_TOKEN=your-birdwatcher_config-workspace-admin-token
ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Model name
MODEL=

# Fill in depending on your model
GOOGLE_APPLICATION_CREDENTIALS=
VERTEX_API_KEY=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

**Step 5: Configure the Slack app**

Use this `App Manifest` and make sure you verify the event subscription domain.

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
      url: https://<YOUR_DOMAIN>/api/slack
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
    request_url: https://<YOUR_DOMAIN>/api/slack
    bot_events:
      - app_home_opened
      - app_mention
      - message.channels
      - message.groups
      - message.im
  interactivity:
    is_enabled: true
    request_url: https://<YOUR_DOMAIN>/api/slack
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

### 🧪 Local Development

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
