import os
import json
import requests
import aiohttp
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import logging
from cryptography.fernet import Fernet
from base64 import b64encode, b64decode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable.
    If not set, generate a new one and log a warning.
    
    Returns:
        bytes: Encryption key
    """
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        logger.warning("ENCRYPTION_KEY not set in environment variables")
        return None
    return key.encode()

def encrypt_token(token: str) -> Optional[str]:
    """
    Encrypt a token using the encryption key from environment variables.
    
    Args:
        token (str): Token to encrypt
        
    Returns:
        Optional[str]: Encrypted token as base64 string, or None if encryption fails
    """
    try:
        key = get_encryption_key()
        if not key:
            logger.error("Cannot encrypt: No encryption key available")
            return None
            
        f = Fernet(key)
        encrypted_data = f.encrypt(token.encode())
        return b64encode(encrypted_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encrypting token: {str(e)}")
        return None

def decrypt_token(encrypted_token: str) -> Optional[str]:
    """
    Decrypt a token using the encryption key from environment variables.
    
    Args:
        encrypted_token (str): Encrypted token as base64 string
        
    Returns:
        Optional[str]: Decrypted token, or None if decryption fails
    """
    try:
        key = get_encryption_key()
        if not key:
            logger.error("Cannot decrypt: No encryption key available")
            return None
            
        f = Fernet(key)
        encrypted_data = b64decode(encrypted_token.encode('utf-8'))
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting token: {str(e)}")
        return None

class TinybirdConfig:
    """Class to handle Tinybird configuration storage and retrieval"""
    
    def __init__(self, host: str, token: str):
        """
        Initialize Tinybird configuration handler.
        
        Args:
            host (str): Tinybird host URL (e.g., 'https://api.tinybird.co')
            token (str): Tinybird API token with admin access
        """
        self.host = host.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """
        Make a request to Tinybird API.
        
        Args:
            method (str): HTTP method ('GET', 'POST', etc.)
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            
        Returns:
            Dict: API response
        """
        # TODO: Implement API request handling
        pass

    async def get_channel_config(self, channel_id: str, user_id: str = None) -> Optional[Dict]:
        """
        Get the latest configuration for a specific channel from Tinybird.
        
        Args:
            channel_id (str): Slack channel ID
            
        Returns:
            Optional[Dict]: Channel configuration or None if not found
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.host}/v0/pipes/get_latest_user_token.json"
                params = {
                    "channel_id": channel_id,
                }
                if user_id:
                    params["user_id"] = user_id
                headers = {
                    "Authorization": f"Bearer {self.token}"
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("data") and len(result["data"]) > 0:
                            config = result["data"][0]
                            return config
                        logger.info(f"No configuration found for channel {channel_id}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get configuration. Status: {response.status}, Error: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting channel configuration: {str(e)}")
            return None

    async def save_event(self, event_data: Dict, table_name: str) -> bool:
        """
        Save an event to Tinybird events API.
        
        Args:
            event_data (Dict): Event data to save
            table_name (str): Name of the Tinybird table to save to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to NDJSON format
            ndjson_data = json.dumps(event_data) + "\n"
            
            # Make async POST request to Tinybird events API
            async with aiohttp.ClientSession() as session:
                url = f"{self.host}/v0/events"
                params = {"name": table_name}
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/x-ndjson"
                }
                
                async with session.post(url, params=params, headers=headers, data=ndjson_data) as response:
                    if response.status == 202:
                        logger.info(f"Successfully saved event to {table_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to save event. Status: {response.status}, Error: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error saving event: {str(e)}")
            return False

    async def save_channel_config(self, channel_id: str, config: Dict) -> bool:
        """
        Save configuration for a specific channel to Tinybird events API.
        
        Args:
            channel_id (str): Slack channel ID
            config (Dict): Channel configuration to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare the event data according to the schema
            event_data = {
                "user_id": config.get("updated_by", "unknown"),
                "channel_id": channel_id,
                "token": config.get("tinybird_token", ""),  # Already encrypted by the caller
                "host": config.get("tinybird_host", ""),
                "updated_at": datetime.now().isoformat()
            }
            
            return await self.save_event(event_data, "user_tokens")
                        
        except Exception as e:
            logger.error(f"Error saving channel configuration: {str(e)}")
            return False

    async def save_notification_config(self, channel_id: str, config: Dict) -> bool:
        """
        Save notification configuration for a specific channel to Tinybird events API.
        
        Args:
            channel_id (str): Slack channel ID
            config (Dict): Notification configuration to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare the event data according to the schema
            event_data = {
                "user_id": config.get("updated_by", "unknown"),
                "channel_id": channel_id,
                "notification_types": config.get("notification_types", []),
                "updated_at": datetime.now().isoformat()
            }
            
            return await self.save_event(event_data, "notification_configs")
                        
        except Exception as e:
            logger.error(f"Error saving notification configuration: {str(e)}")
            return False

    async def save_slack_oauth_tokens(self, team_id: str, bot_token: str, bot_user_id: str, authed_user_id: str = None) -> bool:
        """
        Save Slack OAuth tokens for a workspace to Tinybird events API.
        
        Args:
            team_id (str): Slack team/workspace ID
            bot_token (str): Bot token from OAuth flow (will be encrypted)
            bot_user_id (str): Bot user ID from OAuth flow
            authed_user_id (str, optional): User ID who authorized the app
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Encrypt the bot token before storing
            encrypted_bot_token = encrypt_token(bot_token)
            if not encrypted_bot_token:
                logger.error("Failed to encrypt bot token")
                return False
            
            # Prepare the event data according to the schema
            event_data = {
                "team_id": team_id,
                "bot_token": encrypted_bot_token,
                "bot_user_id": bot_user_id,
                "authed_user_id": authed_user_id or "unknown",
                "updated_at": datetime.now().isoformat()
            }
            
            return await self.save_event(event_data, "slack_oauth_tokens")
                        
        except Exception as e:
            logger.error(f"Error saving Slack OAuth tokens: {str(e)}")
            return False

    async def get_slack_oauth_tokens(self, team_id: str) -> Optional[Dict]:
        """
        Get the latest Slack OAuth tokens for a workspace from Tinybird.
        
        Args:
            team_id (str): Slack team/workspace ID
            
        Returns:
            Optional[Dict]: OAuth tokens or None if not found
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.host}/v0/pipes/get_latest_slack_oauth_tokens.json"
                params = {
                    "team_id": team_id,
                }
                headers = {
                    "Authorization": f"Bearer {self.token}"
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("data") and len(result["data"]) > 0:
                            tokens = result["data"][0]
                            # Decrypt the bot token
                            if tokens.get("bot_token"):
                                decrypted_token = decrypt_token(tokens["bot_token"])
                                if decrypted_token:
                                    tokens["bot_token"] = decrypted_token
                                else:
                                    logger.error("Failed to decrypt bot token")
                                    return None
                            return tokens
                        logger.info(f"No OAuth tokens found for team {team_id}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get OAuth tokens. Status: {response.status}, Error: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting Slack OAuth tokens: {str(e)}")
            return None

    async def save_mission(self, channel_id: str, config: Dict) -> bool:
        """
        Save a mission for a specific channel to Tinybird events API.
        Args:
            channel_id (str): Slack channel ID
            config (Dict): Mission configuration to save (expects 'mission' and 'updated_by')
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            event_data = {
                "user_id": config.get("updated_by", "unknown"),
                "channel_id": channel_id,
                "mission": config.get("mission", ""),
                "updated_at": datetime.now().isoformat()
            }
            return await self.save_event(event_data, "missions")
        except Exception as e:
            logger.error(f"Error saving mission: {str(e)}")
            return False

def create_tinybird_config(host: str = "https://api.europe-west2.gcp.tinybird.co", token: str = None) -> TinybirdConfig:
    """
    Create a TinybirdConfig instance.
    
    Args:
        host (str): Tinybird host URL
        token (str): Tinybird API token
        
    Returns:
        TinybirdConfig: Configuration handler instance
    """
    return TinybirdConfig(host, token)

# Example usage
if __name__ == '__main__':
    async def main():
        # Get configuration from environment variables
        token = os.getenv('TINYBIRD_BIRDWATCHER_TOKEN')
        
        if not token:
            logger.error("Missing required environment variables")
            exit(1)
        
        # Test encryption/decryption
        test_token = "test_token_123"
        encrypted = encrypt_token(test_token)
        if encrypted:
            logger.info(f"Encrypted token: {encrypted}")
            decrypted = decrypt_token(encrypted)
            logger.info(f"Decrypted token: {decrypted}")
            assert decrypted == test_token, "Encryption/decryption test failed"
        
        # Create config handler
        config_handler = create_tinybird_config(token=token)
        
        # Example channel configuration
        channel_id = "C1234567890"
        config = {
            "tinybird_token": encrypt_token(test_token),  # Store encrypted token
            "updated_by": "U1234567890",
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            # Save configuration
            if await config_handler.save_channel_config(channel_id, config):
                logger.info(f"Configuration saved for channel {channel_id}")
            
            # Get configuration
            saved_config = await config_handler.get_channel_config(channel_id)
            if saved_config:
                # Decrypt token for logging (don't do this in production)
                if 'tinybird_token' in saved_config:
                    saved_config['tinybird_token'] = decrypt_token(saved_config['tinybird_token'])
                logger.info(f"Retrieved configuration: {json.dumps(saved_config, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error in example operations: {str(e)}")

    # Run the async main function
    asyncio.run(main()) 