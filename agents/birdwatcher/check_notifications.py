import os
import aiohttp
import asyncio
from datetime import datetime, timedelta
from api.tinybird import decrypt_token
from dotenv import load_dotenv
from birdwatcher import run_single_command, EXPLORATIONS_PROMPT, INVESTIGATION_TEMPLATES
from textwrap import dedent

load_dotenv()

async def get_notification_configs():
    """Get all notification configurations from Tinybird"""
    token = os.getenv('TINYBIRD_BIRDWATCHER_TOKEN')
    if not token:
        raise ValueError("TINYBIRD_BIRDWATCHER_TOKEN not set")
    host = "https://api.europe-west2.gcp.tinybird.co"
    
    url = f"{host}/v0/pipes/get_latest_user_token.json"
    params = {"schedule": "true"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers={"Authorization": f"Bearer {token}"}) as response:
            if response.status != 200:
                raise Exception(f"Failed to get configurations: {await response.text()}")
            return await response.json()

async def run_notification_check(config):
    """Run notification check for a specific configuration"""
    channel_id = config.get('channel_id')
    notification_types = config.get('notification_types', [])
    encrypted_token = config.get('token')
    tinybird_host = config.get('host')
    user_id = config.get('user_id', 'system')
    
    if not all([channel_id, notification_types, encrypted_token, tinybird_host]):
        print(f"Skipping invalid configuration: {config}")
        return
        
    # Decrypt the token
    tinybird_token = decrypt_token(encrypted_token)
    if not tinybird_token:
        print(f"Failed to decrypt token for channel {channel_id}")
        return
        
    # Set environment variables for the script
    os.environ['TINYBIRD_API_KEY'] = tinybird_token
    os.environ['TINYBIRD_HOST'] = tinybird_host
    
    for notification_type in notification_types:
        if notification_type == 'cpu_spikes':
            prompt = f"investigate cpu spikes in the last day. notify to the slack channel with #room-birdwatcher-agent"
            instructions = [dedent(INVESTIGATION_TEMPLATES)]
        elif notification_type == 'daily_summary':
            prompt = f"report metrics for pipes, datasources and jobs in the last 24 hours. Use the explore_data tool to get the data and these datasources: organization.pipe_metrics_by_minute, organization.datasource_metrics_by_minute, organization.jobs_log. Run three times the explore_data tool with each one of these datasources to build a summary. Notify to the slack channel with id: {channel_id}"
            instructions = [dedent(EXPLORATIONS_PROMPT)]
        else:
            print(f"Unknown notification type: {notification_type}")
            continue
            
        try:
            await run_single_command(
                prompt=prompt,
                user_id=user_id,
                instructions=instructions,
            )        
        except Exception as e:
            print(f"Error running notification check: {str(e)}")

async def main():
    try:
        # Get all notification configurations
        response = await get_notification_configs()
        if not response.get('data'):
            print("No notification configurations found")
            return
            
        # Process each configuration
        for config in response['data']:
            await run_notification_check(config)
            
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 