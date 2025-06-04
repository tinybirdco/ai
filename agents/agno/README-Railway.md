# Agno Slack Bot - Railway Deployment

This is the Agno-powered Slack bot that provides data analysis capabilities using the Agno framework.

## 🚀 Deploy to Railway

Railway supports Docker deployments and has more generous size limits than Vercel, making it perfect for the Agno framework.

### Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Slack App**: Set up your Slack app (see main README.md for details)

### Deployment Options

#### Option 1: Deploy from Local Directory (No GitHub Required)

1. **Install Railway CLI**:
   ```bash
   # macOS
   brew install railway
   
   # npm (any OS)
   npm install -g @railway/cli
   
   # Or download from https://railway.app/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Initialize and Deploy**:
   ```bash
   # Navigate to your project directory
   cd ai/agents/agno
   
   # Login and create a new project
   railway login
   railway init
   
   # This will create a new project and service
   # Follow the prompts to name your project
   
   # Deploy directly from local directory
   railway up
   
   # After first deployment, set environment variables
   railway variables --set SLACK_BOT_TOKEN=xoxb-your-bot-token
   railway variables --set SLACK_SIGNING_SECRET=your-signing-secret
   railway variables --set SLACK_CLIENT_SECRET=your-client-secret
   railway variables --set SLACK_VERIFICATION_TOKEN=your-verification-token
   railway variables --set SLACK_BOT_USER_ID=your-bot-user-id
   railway variables --set AGNO_INVESTIGATION_STYLE=multi_step
   railway variables --set TINYBIRD_HOST=your-tinybird-host
   railway variables --set ANTHROPIC_API_KEY=your-anthropic-api-key
   railway variables --set RESEND_API_KEY=your-resend-api-key
   railway variables --set PG_USER=your-postgres-user
   railway variables --set PG_PWD=your-postgres-password
   
   # For Google Cloud credentials, use JSON content (not file path):
   railway variables --set GOOGLE_APPLICATION_CREDENTIALS='{"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'
   
   # Alternative: Set individual Google Cloud variables
   railway variables --set GOOGLE_CLOUD_PROJECT=your-project-id
   railway variables --set GOOGLE_CLOUD_LOCATION=europe-west1
   
   # Redeploy with new variables
   railway up
   ```

4. **Get Your URL**:
   ```bash
   railway domain
   ```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SLACK_BOT_TOKEN=your-token
...
export PORT=8000

# Run locally
python server.py
```
