# Birdwatcher Slack Bot - Railway Deployment

This is the Birdwatcher Slack agent that provides data analysis capabilities for your Tinybird Organization.

### Prerequisites

1. **Railway Account**
2. **Slack App**
3. **Tinybird Account** 

### Deployment

Deploy a Tinybird project to store Birdwatcher workspace configuration:

```bash
cd ai/agents/birdwatcher/tinybird
curl https://tinybird.co | sh
tb login
tb --cloud deploy

# Use this token later on as TINYBIRD_BIRDWATCHER_TOKEN
tb token copy "admin token"
```

Deploy the Slack bot API that uses the Birdwatcher agent:

```bash
# macOS
brew install railway

# npm (any OS)
npm install -g @railway/cli

# Or download from https://railway.app/cli

# Navigate to your project directory
cd ai/agents/birdwatcher
   

railway login
railway init
   
# This will create a new project and service
# Follow the prompts to name your project
   
# Deploy directly from local directory
railway up
   
# After first deployment, set environment variables
railway variables --set SLACK_BOT_TOKEN=xoxb-your-bot-token

# get your Slack bot user ID
# curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" https://slack.com/api/auth.test
railway variables --set SLACK_BOT_USER_ID=your-bot-user-id
   
# The bot uses Gemini models, but you can adapt the code to any other model
# set Google Cloud credentials, use JSON content (not file path):
railway variables --set GOOGLE_APPLICATION_CREDENTIALS='{"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'
railway variables --set GOOGLE_CLOUD_PROJECT=
railway variables --set GOOGLE_CLOUD_LOCATION=

# This is to store Birdwatcher Tinybird tokens on /birdwatcher-config
railway variables --set TINYBIRD_BIRDWATCHER_TOKEN=
# This is to encrypt config tokens
# generate with python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" or similar
railway variables --set ENCRYPTION_KEY=

# Optional, to enable storage and email
railway variables --set PG_URL=your-postgres-connection-url
railway variables --set RESEND_API_KEY=your-resend-api-key
   
# Redeploy with new variables
railway up

# Get your URL
railway domain
```

### Configure the Slack app

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
      url: <YOUR_RAILWAY_DOMAIN>/api/slack
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
    request_url: <YOUR_RAILWAY_DOMAIN>/api/slack
    bot_events:
      - app_home_opened
      - app_mention
      - message.channels
      - message.groups
      - message.im
  interactivity:
    is_enabled: true
    request_url: <YOUR_RAILWAY_DOMAIN>/api/slack
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (check .env.example for the complete list)
export SLACK_BOT_TOKEN=your-token
export SLACK_BOT_USER_ID=your-bot-user-id
export ...
...
export PORT=8000

# Run locally
python server.py

# Use ngrok to test the Slack app with your local server
ngrok http 8000
```
