from aiohttp import web
import json
import os
import aiohttp
import re
import asyncio
from birdwatcher import create_agno_agent
from prompts import SYSTEM_PROMPT, EXPLORATIONS_PROMPT
from textwrap import dedent
import tempfile
import time
import random
from datetime import datetime
from .tinybird import create_tinybird_config, encrypt_token, decrypt_token
from .thinking_messages import THINKING_MESSAGES

# File to store processed message IDs
PROCESSED_MESSAGES_FILE = os.path.join(tempfile.gettempdir(), "slack_bot_processed_messages.txt")

# Initialize TinybirdConfig instance
tinybird_config = None

# Initialize aiohttp app
app = web.Application()
routes = web.RouteTableDef()

async def init_tinybird_config():
    """Initialize TinybirdConfig with token from environment"""
    global tinybird_config
    token = os.getenv('TINYBIRD_BIRDWATCHER_TOKEN')
    if not token:
        print("Missing TINYBIRD_BIRDWATCHER_TOKEN environment variable")
        return False
    tinybird_config = create_tinybird_config(token=token)
    return True

async def get_channel_config(channel_id, user_id):
    """Get configuration for a specific channel from Tinybird"""
    if not tinybird_config:
        if not await init_tinybird_config():
            return None

    # For DMs, we need both channel_id and user_id
    if channel_id.startswith('D'):
        return await tinybird_config.get_channel_config(channel_id, user_id)
    
    # For regular channels, we only need channel_id
    return await tinybird_config.get_channel_config(channel_id)

async def save_channel_config(channel_id, config):
    """Save configuration for a specific channel to Tinybird"""
    if not tinybird_config:
        if not await init_tinybird_config():
            return False
    return await tinybird_config.save_channel_config(channel_id, config)

async def save_notification_config(channel_id, config):
    """Save notification config for a specific channel to Tinybird"""
    if not tinybird_config:
        if not await init_tinybird_config():
            return False
    return await tinybird_config.save_notification_config(channel_id, config)

def create_config_modal(channel_id):
    """Create the configuration modal using Slack Blocks"""
    modal = {
        "type": "modal",
        "callback_id": "agno_config_modal",
        "title": {
            "type": "plain_text",
            "text": "Configure Birdwatcher"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save Configuration"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": channel_id,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Configure Birdwatcher for:* <#{channel_id}>"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Get your Tinybird <https://cloud.tinybird.co/tokens|organization admin token> and <https://www.tinybird.co/docs/api-reference?#regions-and-endpoints|API host>"
                }
            },
            {
                "type": "input",
                "block_id": "tinybird_token_block",
                "label": {
                    "type": "plain_text",
                    "text": "Tinybird org admin token"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "tinybird_token",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Enter your Tinybird organization admin token"
                    }
                }
            },
            {
                "type": "input",
                "block_id": "tinybird_host_block",
                "label": {
                    "type": "plain_text",
                    "text": "Tinybird API Host"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "tinybird_host",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., https://api.tinybird.co"
                    }
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Learn how to build your own agent in <https://github.com/tinybirdco/ai/blob/main/agents/birdwatcher/README.md|our README>"
                }
            }
        ]
    }
    
    return modal

def create_notifications_modal(channel_id, existing_config=None):
    """Create the notifications subscription modal using Slack Blocks"""
    # Get existing notification types or default to empty list
    notification_types = existing_config.get("notification_types", []) if existing_config else []
    
    # Create initial options list only if there are selected types
    initial_options = []
    if "daily_summary" in notification_types:
        initial_options.append({
            "text": {
                "type": "plain_text",
                "text": "Daily organization metrics summary"
            },
            "value": "daily_summary"
        })
    if "cpu_spikes" in notification_types:
        initial_options.append({
            "text": {
                "type": "plain_text",
                "text": "Dedicated cluster health"
            },
            "value": "cpu_spikes"
        })
    
    # Create checkbox element configuration
    checkbox_element = {
        "type": "checkboxes",
        "action_id": "notification_options",
        "options": [
            {
                "text": {
                    "type": "plain_text",
                    "text": "Daily organization metrics summary"
                },
                "value": "daily_summary"
            },
            {
                "text": {
                    "type": "plain_text",
                    "text": "Dedicated cluster health"
                },
                "value": "cpu_spikes"
            }
        ]
    }
    
    # Only add initial_options if there are any
    if initial_options:
        checkbox_element["initial_options"] = initial_options
    
    modal = {
        "type": "modal",
        "callback_id": "agno_notifications_modal",
        "title": {
            "type": "plain_text",
            "text": "Notifications"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "private_metadata": channel_id,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Configure notifications for:* <#{channel_id}>"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select the notifications you want to receive in this channel:"
                }
            },
            {
                "type": "input",
                "block_id": "notification_options_block",
                "optional": True,
                "label": {
                    "type": "plain_text",
                    "text": "Notification Preferences"
                },
                "element": checkbox_element
            }
        ]
    }
    return modal

def is_thinking_message(text):
    """Check if a message is one of the bot's thinking messages"""
    if not text:
        return False
    
    # Check against all thinking messages (remove emojis for comparison)
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    
    for thinking_msg in THINKING_MESSAGES:
        clean_thinking = re.sub(r'[^\w\s]', '', thinking_msg.lower())
        if clean_thinking in clean_text or clean_text in clean_thinking:
            return True
    
    # Also check for the old message format
    if "analyzing your request" in clean_text or "processing your request" in clean_text:
        return True
        
    return False

def is_message_processed(message_id):
    """Check if a message has already been processed"""
    try:
        if not os.path.exists(PROCESSED_MESSAGES_FILE):
            return False
        
        current_time = time.time()
        cutoff_time = current_time - 300  # 5 minutes ago
        
        with open(PROCESSED_MESSAGES_FILE, 'r') as f:
            lines = f.readlines()
        
        # Check if message_id exists and clean up old entries
        processed_ids = []
        message_exists = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('|')
            if len(parts) == 2:
                stored_id, timestamp_str = parts
                try:
                    timestamp = float(timestamp_str)
                    if timestamp > cutoff_time:  # Keep recent entries
                        processed_ids.append(line)
                        if stored_id == message_id:
                            message_exists = True
                except ValueError:
                    continue
        
        # Write back cleaned up entries
        with open(PROCESSED_MESSAGES_FILE, 'w') as f:
            f.write('\n'.join(processed_ids) + '\n')
        
        return message_exists
    except Exception as e:
        print(f"Error checking processed messages: {e}")
        return False

def mark_message_processed(message_id):
    """Mark a message as processed"""
    try:
        current_time = time.time()
        with open(PROCESSED_MESSAGES_FILE, 'a') as f:
            f.write(f"{message_id}|{current_time}\n")
    except Exception as e:
        print(f"Error marking message as processed: {e}")

async def send_slack_message(channel: str, text: str, thread_ts: str = None):
    """Send a message to Slack using aiohttp"""
    slack_token = os.environ.get("SLACK_TOKEN", "")
    if not slack_token:
        print("ERROR: No SLACK_TOKEN found!")
        return False

    slack_data = {"channel": channel, "text": text}
    if thread_ts:
        slack_data["thread_ts"] = thread_ts
        print(f"DEBUG: Sending message to thread {thread_ts} in channel {channel}")
    else:
        print(f"DEBUG: Sending message to channel {channel} (no thread)")

    print(f"DEBUG: Slack payload: {json.dumps(slack_data, indent=2)}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://slack.com/api/chat.postMessage",
                json=slack_data,
                headers={
                    "Authorization": f"Bearer {slack_token}",
                    "Content-Type": "application/json",
                }
            ) as response:
                response_data = await response.json()
                print(f"DEBUG: Slack API response: {response_data}")

                if not response_data.get("ok"):
                    print(f"Slack API error: {response_data.get('error')}")
                    print(f"Full error response: {response_data}")
                    return False
                else:
                    print(f"DEBUG: Message sent successfully. Response ts: {response_data.get('ts')}")
                    return True

    except Exception as e:
        print(f"Error sending Slack message: {e}")
        import traceback
        traceback.print_exc()
        return False

async def send_followup_response(response_url: str, text: str):
    """Send a follow-up response to Slack using aiohttp"""
    try:
        response_data = {
            "response_type": "ephemeral",
            "text": text
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                response_url,
                json=response_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    print(f"Error sending follow-up response: {await response.text()}")
                return response.status == 200
    except Exception as e:
        print(f"Error sending follow-up response: {e}")
        return False

async def get_thread_history(channel: str, thread_ts: str, limit: int = 50):
    """Fetch thread history from Slack API using aiohttp"""
    slack_token = os.environ.get("SLACK_TOKEN", "")
    if not slack_token or not thread_ts:
        return []
    
    try:
        url = f"https://slack.com/api/conversations.replies?channel={channel}&ts={thread_ts}&limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Authorization": f"Bearer {slack_token}"}
            ) as response:
                data = await response.json()
            
            if data.get("ok"):
                return data.get("messages", [])
            else:
                print(f"Slack API error fetching thread: {data.get('error', 'Unknown error')}")
                return []
                
    except Exception as e:
        print(f"Error fetching thread history: {e}")
        return []

@routes.post('/api/slack')
async def handle_slack(request):
    try:
        print(f"=== INCOMING REQUEST DEBUG ===")
        print(f"Request path: {request.path}")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"========================")

        # Read request body
        body = await request.text()
        print(f"=== HTTP REQUEST DEBUG ===")
        print(f"Request body: {body}")
        print(f"========================")

        try:
            data = json.loads(body)
            print(f"=== PARSED DATA DEBUG ===")
            print(f"Data type: {data.get('type')}")
            print(f"Full data: {json.dumps(data, indent=2)}")
            print(f"========================")

            if data.get("type") == "url_verification":
                challenge = data.get("challenge", "")
                return web.Response(text=challenge)

            if data.get("type") == "event_callback":
                event = data.get("event", {})
                event_type = event.get("type", "")

                if event_type in ["message", "app_mention", "message.im"]:
                    await handle_slack_event(event)

                return web.json_response({
                    "status": "success",
                    "message": "Event processed successfully"
                })

        except json.JSONDecodeError:
            try:
                form_data = await request.post()
                parsed_data = dict(form_data)
                print(f"=== FORM DATA DEBUG ===")
                print(f"Parsed form data: {parsed_data}")
                print(f"========================")

                # Handle view submission
                if "payload" in parsed_data:
                    try:
                        payload = json.loads(parsed_data["payload"])
                        print(f"=== PAYLOAD DEBUG ===")
                        print(f"Payload type: {payload.get('type')}")
                        print(f"Full payload: {json.dumps(payload, indent=2)}")
                        print(f"========================")

                        if payload.get("type") == "view_submission":
                            print("Received view submission")
                            try:
                                result = await handle_modal_submission(payload)
                                return web.json_response(result)
                            except Exception as e:
                                print(f"Error handling view submission: {e}")
                                return web.json_response({
                                    "response_action": "errors",
                                    "errors": {
                                        "tinybird_token_block": f"Error processing submission: {str(e)}"
                                    }
                                })

                    except json.JSONDecodeError as e:
                        print(f"Error parsing payload JSON: {e}")
                        return web.json_response({"status": "error", "message": str(e)})

                # Handle slash commands
                command = parsed_data.get("command", "")
                if command == "/birdwatcher-config":
                    await handle_config_command(parsed_data)
                    return web.json_response({
                        "response_type": "ephemeral",
                        "text": "Opening configuration modal..."
                    })
                elif command == "/birdwatcher-notifications":
                    await handle_notifications_command(parsed_data)
                    return web.json_response({
                        "response_type": "ephemeral",
                        "text": "Opening notifications modal..."
                    })

            except Exception as e:
                print(f"Error parsing form data: {e}")
                return web.json_response({
                    "status": "error",
                    "message": f"Error processing request: {str(e)}"
                })

        return web.json_response({
            "status": "success",
            "message": "Request processed successfully"
        })

    except Exception as e:
        print(f"Error in handler: {e}")
        return web.json_response({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }, status=500)

@routes.get('/api/slack')
async def health_check(request):
    return web.json_response({
        "status": "healthy",
        "service": "agno-slack-bot"
    })

# Add root path health check
@routes.get('/')
async def health_check(request):
    return web.Response(text='OK', status=200)

async def handle_slack_event(event):
    try:
        # Allow USLACKBOT messages if they're reminders
        is_reminder = "Reminder:" in event.get("text", "")
        if (event.get("bot_id") or event.get("subtype") == "bot_message") and not is_reminder:
            return

        bot_user_id = os.environ.get("SLACK_BOT_USER_ID", "U08V1K4MXFD")
        if bot_user_id and event.get("user") == bot_user_id:
            return

        user_message = event.get("text", "")
        user = event.get("user", "")
        channel = event.get("channel", "")
        ts = event.get("ts", "")
        thread_ts = event.get("thread_ts")
        event_type = event.get("type", "")

        # Debug channel type
        print(f"=== CHANNEL DEBUG ===")
        print(f"Channel ID: {channel}")
        print(f"Channel type: {'DM' if channel.startswith('D') else 'Channel'}")
        print(f"Event type: {event_type}")
        print(f"==================")

        # Create unique message ID for deduplication
        message_id = f"{channel}_{ts}_{user}"
        
        # For non-reminder messages, check if already processed
        if is_message_processed(message_id):
            print(f"Message already processed, skipping: {message_id}")
            return

        # Mark message as processed BEFORE sending any responses
        mark_message_processed(message_id)

        reply_thread_ts = thread_ts or ts

        print(f"=== EVENT DEBUG ===")
        print(f"Raw event: {json.dumps(event, indent=2)}")
        print(f"Event type: {event_type}")
        print(f"Message ID: {message_id}")
        print(f"ts: '{ts}' (type: {type(ts)})")
        print(f"thread_ts: '{thread_ts}' (type: {type(thread_ts)})")
        print(f"reply_thread_ts: '{reply_thread_ts}' (type: {type(reply_thread_ts)})")
        print(f"channel: '{channel}'")
        print(f"==================")

        if not user_message or not user:
            await send_slack_message(
                channel,
                "Hi! Ask me about your organization metrics or data analysis.",
                reply_thread_ts,
            )
            return

        print(f"Processing message from {user}: {user_message}")

        # For reminders, check if we've already responded in the thread
        if is_reminder and thread_ts:
            thread_messages = await get_thread_history(channel, thread_ts)
            for msg in thread_messages:
                if msg.get("user") == bot_user_id and not is_thinking_message(msg.get("text", "")):
                    print(f"Already responded to reminder in thread, skipping: {message_id}")
                    return

        # Send thinking message only if not from USLACKBOT
        print(f"Sending thinking message to channel {channel}, reply_thread_ts: {reply_thread_ts}")
        await send_slack_message(
            channel,
            random.choice(THINKING_MESSAGES),
            reply_thread_ts,
        )

        # Process with Agno
        response = await process_with_agno(
            user_message, user, channel, reply_thread_ts
        )

        print(f"Sending response to channel {channel}, reply_thread_ts: {reply_thread_ts}")
        await send_slack_message(
            channel, f"<@{user}> {response}", reply_thread_ts
        )

    except Exception as e:
        print(f"Error handling Slack event: {e}")
        import traceback
        traceback.print_exc()

async def process_with_agno(
    message: str, user_id: str, channel: str = None, thread_ts: str = None
) -> str:
    try:
        # Check if we're in a thread and gather context if it was created by the bot
        thread_context = ""
        if thread_ts and channel:
            print(f"Fetching thread history for thread_ts: {thread_ts}")
            thread_messages = await get_thread_history(channel, thread_ts)
            print(f"Thread messages: {thread_messages}")
            
            if thread_messages:
                print("Extracting full thread context...")
                
                # Build full thread context with all messages
                thread_context = "\n\nTHREAD CONTEXT (Full conversation history):\n"
                for i, msg in enumerate(thread_messages):
                    user_id_msg = msg.get("user", "unknown")
                    _user_id = msg.get("user_id", "unknown")
                    text = msg.get("text", "")
                    timestamp = msg.get("ts", "")
                    
                    # Clean up Slack formatting
                    clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
                    
                    if clean_text:
                        # Identify if it's a bot message or user message
                        bot_user_id = os.environ.get("SLACK_BOT_USER_ID", "U08V1K4MXFD")
                        is_bot = user_id_msg == bot_user_id or _user_id == bot_user_id or _user_id == "USLACKBOT"
                        sender_type = "Bot" if is_bot else "User"
                        
                        # Skip thinking messages from thread context
                        if not is_thinking_message(clean_text):
                            thread_context += f"Message {i+1} ({sender_type}): {clean_text}\n"
                
                print(f"Added full thread context: {thread_context}")

        # Get channel configuration
        channel_config = await get_channel_config(channel, user_id)
        if not channel_config:
            return "❌ No configuration found for this channel. Please use `/birdwatcher-config` to set up the agent first."

        # Get Tinybird configuration
        tinybird_host = channel_config.get("host")
        encrypted_token = channel_config.get("token")

        if not encrypted_token or not tinybird_host:
            return "❌ No Tinybird token or host configured for this channel. Please use `/birdwatcher-config` to set up the agent first."

        try:
            tinybird_token = decrypt_token(encrypted_token)
            if not tinybird_token or not tinybird_host:
                return "❌ Error decrypting Tinybird token or host. Please reconfigure the channel using `/birdwatcher-config`."
        except Exception as e:
            print(f"Error decrypting token: {e}")
            return "❌ Error decrypting Tinybird token or host. Please reconfigure the channel using `/birdwatcher-config`."

        agent = None
        mcp_tools = None
        try:
            if thread_ts:
                session_id = f"slack_{channel}_{thread_ts}"
            elif channel:
                session_id = f"slack_{channel}_{user_id}"
            else:
                session_id = f"slack_{user_id}"

            if thread_context:
                instructions = [f"You MUST reply in the same Slack thread as the user's message: Thread ts: {thread_ts}"] + [dedent(thread_context)] + [dedent(EXPLORATIONS_PROMPT)]
            else:
                instructions = [f"You MUST reply in the same Slack thread as the user's message: Thread ts: {thread_ts}"] + [dedent(EXPLORATIONS_PROMPT)]

            agent, mcp_tools, _ = await create_agno_agent(
                system_prompt=SYSTEM_PROMPT,
                instructions=instructions,
                markdown=False,
                tinybird_host=tinybird_host,
                tinybird_api_key=tinybird_token,
            )

            async with mcp_tools:
                result = await agent.arun(
                    message,
                    user_id=user_id,
                    session_id=session_id,
                    stream=False,
                    show_full_reasoning=True,
                    show_reasoning=True,
                    stream_intermediate_steps=True,
                )

                if hasattr(result, "content"):
                    return str(result.content) if result.content else "I've completed the analysis, but no specific response was generated."
                elif hasattr(result, "data"):
                    return str(result.data) if result.data else "I've completed the analysis, but no specific response was generated."
                else:
                    # Avoid sending the entire RunResponse object
                    return "I've completed the analysis, but encountered an issue formatting the response."

        except Exception as e:
            print(f"Error in agent processing: {e}")
            import traceback
            traceback.print_exc()
            return f"I encountered an error while analyzing your request: {str(e)}"
        finally:
            try:
                if mcp_tools and hasattr(mcp_tools, "aclose"):
                    await mcp_tools.aclose()
            except Exception as cleanup_error:
                print(f"Warning: Error during MCP tools cleanup: {cleanup_error}")

            try:
                await asyncio.sleep(0.1)
            except Exception:
                pass

    except Exception as e:
        print(f"Error in process_with_agno: {e}")
        import traceback
        traceback.print_exc()
        return f"Sorry, I encountered an error processing your request: {str(e)}"

async def handle_config_command(parsed_data):
    """Handle the /birdwatcher-config command"""
    try:
        user_id = parsed_data.get("user_id", "")
        channel_id = parsed_data.get("channel_id", "")
        trigger_id = parsed_data.get("trigger_id", "")
        response_url = parsed_data.get("response_url", "")

        modal = create_config_modal(channel_id)

        # Open modal using Slack API
        slack_token = os.environ.get("SLACK_TOKEN", "")
        if not slack_token:
            await send_followup_response(
                response_url,
                "❌ Error: Bot token not configured"
            )
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://slack.com/api/views.open",
                    json={
                        "trigger_id": trigger_id,
                        "view": modal
                    },
                    headers={
                        "Authorization": f"Bearer {slack_token}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response_data = await response.json()

                    if not response_data.get("ok"):
                        error_msg = response_data.get("error", "Unknown error")
                        await send_followup_response(
                            response_url,
                            f"❌ Error opening configuration modal: {error_msg}"
                        )
                        return

        except Exception as e:
            print(f"Error opening modal: {e}")
            await send_followup_response(
                response_url,
                f"❌ Error opening configuration modal: {str(e)}"
            )

    except Exception as e:
        print(f"Error handling config command: {e}")
        if "response_url" in locals():
            await send_followup_response(
                response_url,
                f"❌ Error processing configuration command: {str(e)}"
            )

async def handle_notifications_command(parsed_data):
    """Handle the /birdwatcher-notifications command"""
    try:
        user_id = parsed_data.get("user_id", "")
        channel_id = parsed_data.get("channel_id", "")
        trigger_id = parsed_data.get("trigger_id", "")
        response_url = parsed_data.get("response_url", "")

        # Get existing configuration
        channel_config = await get_channel_config(channel_id, user_id)
        print(f"Channel config: {channel_config}")
        modal = create_notifications_modal(channel_id, channel_config)

        # Open modal using Slack API
        slack_token = os.environ.get("SLACK_TOKEN", "")
        if not slack_token:
            await send_followup_response(
                response_url,
                "❌ Error: Bot token not configured"
            )
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://slack.com/api/views.open",
                    json={
                        "trigger_id": trigger_id,
                        "view": modal
                    },
                    headers={
                        "Authorization": f"Bearer {slack_token}",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    response_data = await response.json()

                    if not response_data.get("ok"):
                        error_msg = response_data.get("error", "Unknown error")
                        await send_followup_response(
                            response_url,
                            f"❌ Error opening notifications modal: {error_msg}"
                        )
                        return

        except Exception as e:
            print(f"Error opening modal: {e}")
            await send_followup_response(
                response_url,
                f"❌ Error opening notifications modal: {str(e)}"
            )

    except Exception as e:
        print(f"Error handling notifications command: {e}")
        if "response_url" in locals():
            await send_followup_response(
                response_url,
                f"❌ Error processing notifications command: {str(e)}"
            )

async def send_ephemeral_message(channel: str, user: str, text: str):
    """Send an ephemeral message to a channel using aiohttp"""
    try:
        slack_token = os.environ.get("SLACK_TOKEN", "")
        if not slack_token:
            print("ERROR: No SLACK_TOKEN found!")
            return False

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://slack.com/api/chat.postEphemeral",
                json={
                    "channel": channel,
                    "user": user,
                    "text": text
                },
                headers={
                    "Authorization": f"Bearer {slack_token}",
                    "Content-Type": "application/json",
                }
            ) as response:
                response_data = await response.json()
                return response_data.get("ok", False)
    except Exception as e:
        print(f"Error sending ephemeral message: {e}")
        return False

async def handle_modal_submission(payload):
    """Handle modal submission for configuration"""
    try:
        view = payload.get("view", {})
        callback_id = view.get("callback_id")
        channel_id = view.get("private_metadata")
        user_id = payload.get("user", {}).get("id")
        values = view.get("state", {}).get("values", {})

        if callback_id == "agno_config_modal":
            # Handle configuration modal submission
            tinybird_host = values.get("tinybird_host_block", {}).get("tinybird_host", {}).get("value", "")
            tinybird_token = values.get("tinybird_token_block", {}).get("tinybird_token", {}).get("value", "")

            # Validate required fields
            if not tinybird_token:
                return {
                    "response_action": "errors",
                    "errors": {
                        "tinybird_token_block": "Tinybird token is required" if not tinybird_token else None,
                    }
                }

            # Save configuration
            config = {
                "tinybird_host": tinybird_host or '',
                "tinybird_token": encrypt_token(tinybird_token) or '',
                "updated_by": user_id,
                "updated_at": datetime.now().isoformat()
            }

            success = await save_channel_config(channel_id, config)
            if not success:
                return {
                    "response_action": "errors",
                    "errors": {
                        "tinybird_token_block": "Failed to save configuration"
                    }
                }

            # Send confirmation message
            await send_ephemeral_message(
                channel_id,
                user_id,
                "✅ Birdwatcher configuration updated successfully!"
            )

        elif callback_id == "agno_notifications_modal":
            # Handle notifications modal submission
            selected_options = values.get("notification_options_block", {}).get("notification_options", {}).get("selected_options", [])
            
            # Convert selected options to a list of values
            notification_types = [option.get("value") for option in selected_options]
            
            # Save notification preferences
            config = {
                "notification_types": notification_types,
                "updated_by": user_id,
                "channel_id": channel_id,
                "updated_at": datetime.now().isoformat()
            }
            
            success = await save_notification_config(channel_id, config)
            
            if not success:
                return {
                    "response_action": "errors",
                    "errors": {
                        "notification_options_block": "Failed to save notification preferences"
                    }
                }

            # Send confirmation message
            await send_ephemeral_message(
                channel_id,
                user_id,
                "✅ Notification preferences updated successfully!"
            )

        return {"response_action": "clear"}

    except Exception as e:
        print(f"Error handling modal submission: {e}")
        return {
            "response_action": "errors",
            "errors": {
                "notification_options_block": f"Error saving preferences: {str(e)}"
            }
        }

# Add the routes to the app
app.add_routes(routes)

def run_server():
    web.run_app(app, host='0.0.0.0', port=8000)

if __name__ == "__main__":
    run_server()
