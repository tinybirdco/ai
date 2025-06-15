from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
import re
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from memory_chat import create_agno_agent
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
    return await tinybird_config.get_channel_config(channel_id, user_id)

async def save_channel_config(channel_id, config):
    """Save configuration for a specific channel to Tinybird"""
    if not tinybird_config:
        if not await init_tinybird_config():
            return False
    return await tinybird_config.save_channel_config(channel_id, config)

def create_config_modal(channel_id, current_config=None):
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
                },
                "hint": {
                    "type": "plain_text",
                    "text": "Token needs to have access to organization service data sources"
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

class handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self._loop = None
        self._executor = ThreadPoolExecutor(max_workers=4)
        super().__init__(*args, **kwargs)

    def _get_or_create_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()

            def run_loop():
                asyncio.set_event_loop(self._loop)
                self._loop.run_forever()

            loop_thread = threading.Thread(target=run_loop, daemon=True)
            loop_thread.start()
        return self._loop

    def _run_async_in_loop(self, coro):
        try:
            loop = self._get_or_create_loop()
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=300)
        except Exception as e:
            print(f"Error running async function: {e}")
            import traceback

            traceback.print_exc()
            raise

    def _send_slack_message(self, channel: str, text: str, thread_ts: str = None):
        slack_token = os.environ.get("SLACK_BOT_TOKEN", "")

        if not slack_token:
            print("ERROR: No SLACK_BOT_TOKEN found!")
            return False

        slack_data = {"channel": channel, "text": text}

        if thread_ts:
            slack_data["thread_ts"] = thread_ts
            print(f"DEBUG: Sending message to thread {thread_ts} in channel {channel}")
            print(f"DEBUG: thread_ts type: {type(thread_ts)}, value: '{thread_ts}'")
        else:
            print(f"DEBUG: Sending message to channel {channel} (no thread)")

        print(f"DEBUG: Slack payload: {json.dumps(slack_data, indent=2)}")

        try:
            req = urllib.request.Request(
                "https://slack.com/api/chat.postMessage",
                data=json.dumps(slack_data).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {slack_token}",
                    "Content-Type": "application/json",
                },
            )

            response = urllib.request.urlopen(req)
            response_data = response.read().decode("utf-8")

            print(f"DEBUG: Slack API response: {response_data}")

            try:
                response_json = json.loads(response_data)
                if not response_json.get("ok"):
                    print(f"Slack API error: {response_json.get('error')}")
                    print(f"Full error response: {response_json}")
                    return False
                else:
                    print(
                        f"DEBUG: Message sent successfully. Response ts: {response_json.get('ts')}"
                    )
            except json.JSONDecodeError:
                print("Could not parse Slack API response as JSON")

            return response.status == 200
        except Exception as e:
            print(f"Error sending Slack message: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _send_followup_response(self, response_url: str, text: str):
        try:
            response_data = {"response_type": "in_channel", "text": text}

            req = urllib.request.Request(
                response_url,
                data=json.dumps(response_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

            response = urllib.request.urlopen(req)
            return response.status == 200
        except Exception as e:
            print(f"Error sending follow-up response: {e}")
            return False

    def _get_thread_history(self, channel: str, thread_ts: str, limit: int = 50):
        """Fetch thread history from Slack API"""
        slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
        
        if not slack_token or not thread_ts:
            return []
        
        try:
            url = f"https://slack.com/api/conversations.replies?channel={channel}&ts={thread_ts}&limit={limit}"
            
            req = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {slack_token}"}
            )
            
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode("utf-8"))
            
            if data.get("ok"):
                return data.get("messages", [])
            else:
                print(f"Slack API error fetching thread: {data.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            print(f"Error fetching thread history: {e}")
            return []

    def _is_thread_created_by_bot(self, thread_messages):
        """Check if the thread was created by the bot"""
        if not thread_messages:
            return False
        
        bot_user_id = os.environ.get("SLACK_BOT_USER_ID", "U08V1K4MXFD")
        if not bot_user_id:
            return False
        
        # Check if the first message in the thread is from the bot
        first_message = thread_messages[0]
        return first_message.get("user") == bot_user_id

    def _extract_bot_messages_context(self, thread_messages):
        """Extract first and last bot messages from thread"""
        bot_user_id = os.environ.get("SLACK_BOT_USER_ID", "U08V1K4MXFD")
        if not bot_user_id or not thread_messages:
            return None, None
        
        bot_messages = []
        for msg in thread_messages:
            if msg.get("user") == bot_user_id:
                text = msg.get("text", "")
                if text:
                    # Clean up Slack formatting
                    clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
                    if clean_text:
                        bot_messages.append(clean_text)
        
        if not bot_messages:
            return None, None
        
        first_bot_message = bot_messages[0] if bot_messages else None
        last_bot_message = bot_messages[-1] if len(bot_messages) > 1 else None
        
        return first_bot_message, last_bot_message

    def do_POST(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            body = post_data.decode("utf-8")

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
                    self._send_response_safely(
                        200, "text/plain", challenge.encode("utf-8")
                    )
                    return

                if data.get("type") == "event_callback":
                    event = data.get("event", {})
                    event_type = event.get("type", "")

                    if event_type in ["message", "app_mention"]:
                        self._handle_slack_event(event)

                    self._send_response_safely(
                        200,
                        "application/json",
                        json.dumps({"status": "ok"}).encode("utf-8"),
                    )
                    return
            except json.JSONDecodeError:
                try:
                    parsed_data = urllib.parse.parse_qs(body)
                    print(f"=== FORM DATA DEBUG ===")
                    print(f"Parsed form data: {parsed_data}")
                    print(f"========================")

                    # Handle view submission
                    if "payload" in parsed_data:
                        try:
                            payload = json.loads(parsed_data["payload"][0])
                            print(f"=== PAYLOAD DEBUG ===")
                            print(f"Payload type: {payload.get('type')}")
                            print(f"Full payload: {json.dumps(payload, indent=2)}")
                            print(f"========================")

                            if payload.get("type") == "view_submission":
                                print("Received view submission")
                                try:
                                    result = self._run_async_in_loop(self._handle_modal_submission(payload))
                                    self._send_response_safely(
                                        200,
                                        "application/json",
                                        json.dumps(result).encode("utf-8")
                                    )
                                    return
                                except Exception as e:
                                    print(f"Error handling view submission: {e}")
                                    self._send_response_safely(
                                        200,
                                        "application/json",
                                        json.dumps({
                                            "response_action": "errors",
                                            "errors": {
                                                "tinybird_token_block": f"Error processing submission: {str(e)}"
                                            }
                                        }).encode("utf-8")
                                    )
                                    return
                        except json.JSONDecodeError as e:
                            print(f"Error parsing payload JSON: {e}")
                            return

                    # Handle slash commands
                    command = parsed_data.get("command", [""])[0]
                    if command == "/birdwatcher-config":
                        self._run_async_in_loop(self._handle_config_command(parsed_data))
                        return
                except Exception as e:
                    print(f"Error parsing form data: {e}")

            self._send_response_safely(
                200, "application/json", json.dumps({"status": "ok"}).encode("utf-8")
            )

        except Exception as e:
            print(f"Error in handler: {e}")
            self._send_response_safely(
                500, "text/plain", f"Error: {str(e)}".encode("utf-8")
            )

    def _send_response_safely(
        self, status_code: int, content_type: str, content: bytes
    ):
        try:
            self.send_response(status_code)
            self.send_header("Content-type", content_type)
            self.end_headers()
            self.wfile.write(content)
        except BrokenPipeError:
            print("Client disconnected before response could be sent (BrokenPipeError)")
        except ConnectionResetError:
            print("Client reset connection before response could be sent")
        except Exception as e:
            print(f"Error sending response: {e}")

    def _handle_slack_event(self, event):
        try:
            if event.get("bot_id") or event.get("subtype") == "bot_message":
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

            # Create unique message ID for deduplication
            message_id = f"{channel}_{ts}_{user}"
            
            # Check if we've already processed this message
            if is_message_processed(message_id):
                print(f"Message already processed, skipping: {message_id}")
                return
            
            # Mark message as processed immediately to prevent race conditions
            mark_message_processed(message_id)

            reply_thread_ts = thread_ts or ts

            print(f"=== EVENT DEBUG ===")
            print(f"Raw event: {json.dumps(event, indent=2)}")
            print(f"Event type: {event_type}")
            print(f"Message ID: {message_id}")
            print(f"ts: '{ts}' (type: {type(ts)})")
            print(f"thread_ts: '{thread_ts}' (type: {type(thread_ts)})")
            print(
                f"reply_thread_ts: '{reply_thread_ts}' (type: {type(reply_thread_ts)})"
            )
            print(f"channel: '{channel}'")
            print(f"==================")

            if not user_message or not user:
                return

            # Check if bot is mentioned in the message or if it's an app_mention event
            bot_mentioned = False
            
            if event_type == "app_mention":
                # This is a direct mention event
                bot_mentioned = True
                print("Bot mentioned via app_mention event")
            elif bot_user_id and f"<@{bot_user_id}>" in user_message:
                # Bot is mentioned in the message text
                bot_mentioned = True
                print("Bot mentioned in message text")

            # Only respond if bot is mentioned
            if not bot_mentioned:
                print(f"Bot not mentioned in message, ignoring: {user_message}")
                return

            # Clean up the mention from the message
            user_message = re.sub(r"<@[A-Z0-9]+>", "", user_message).strip()

            if not user_message:
                self._send_slack_message(
                    channel,
                    "Hi! Ask me about your organization metrics or data analysis.",
                    reply_thread_ts,
                )
                return

            print(f"Processing message from {user}: {user_message}")

            def process_async():
                try:
                    print(
                        f"Sending thinking message to channel {channel}, reply_thread_ts: {reply_thread_ts}"
                    )
                    self._send_slack_message(
                        channel,
                        random.choice(THINKING_MESSAGES),
                        reply_thread_ts,
                    )

                    response = self._run_async_in_loop(self._process_with_agno(
                        user_message, user, channel, reply_thread_ts
                    ))

                    print(
                        f"Sending response to channel {channel}, reply_thread_ts: {reply_thread_ts}"
                    )
                    self._send_slack_message(
                        channel, f"<@{user}> {response}", reply_thread_ts
                    )
                except Exception as e:
                    print(f"Error in async processing: {e}")
                    import traceback

                    traceback.print_exc()
                    self._send_slack_message(
                        channel,
                        f"<@{user}> Sorry, I encountered an error processing your request.",
                        reply_thread_ts,
                    )

            try:
                self._executor.submit(process_async)
            except Exception as e:
                print(f"Error submitting to executor: {e}")
                thread = threading.Thread(target=process_async)
                thread.daemon = True
                thread.start()

        except Exception as e:
            print(f"Error handling Slack event: {e}")
            import traceback

            traceback.print_exc()

    async def _process_with_agno(
        self, message: str, user_id: str, channel: str = None, thread_ts: str = None
    ) -> str:
        try:
            # Check if we're in a thread and gather context if it was created by the bot
            thread_context = ""
            if thread_ts and channel:
                print(f"Fetching thread history for thread_ts: {thread_ts}")
                thread_messages = self._get_thread_history(channel, thread_ts)
                print(f"Thread messages: {thread_messages}")
                
                if thread_messages and self._is_thread_created_by_bot(thread_messages):
                    print("Thread was created by bot, extracting full thread context...")
                    
                    # Build full thread context with all messages
                    thread_context = "\n\nTHREAD CONTEXT (Full conversation history):\n"
                    for i, msg in enumerate(thread_messages):
                        user_id_msg = msg.get("user", "unknown")
                        text = msg.get("text", "")
                        timestamp = msg.get("ts", "")
                        
                        # Clean up Slack formatting
                        clean_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
                        
                        if clean_text:
                            # Identify if it's a bot message or user message
                            bot_user_id = os.environ.get("SLACK_BOT_USER_ID", "U08V1K4MXFD")
                            is_bot = user_id_msg == bot_user_id
                            sender_type = "Bot" if is_bot else "User"
                            
                            # Skip thinking messages from thread context
                            if not is_thinking_message(clean_text):
                                thread_context += f"Message {i+1} ({sender_type}): {clean_text}\n"
                    
                    print(f"Added full thread context: {thread_context}")

            # Get channel configuration
            channel_config = await get_channel_config(channel, user_id)
            if not channel_config:
                return "❌ No configuration found for this channel. Please use `/birdwatcher-config` to set up the channel first."

            # Get Tinybird configuration
            tinybird_host = channel_config.get("tinybird_host")
            encrypted_token = channel_config.get("tinybird_token")

            if not encrypted_token or not tinybird_host:
                return "❌ No Tinybird token or host configured for this channel. Please use `/birdwatcher-config` to set up the channel first."

            try:
                tinybird_token = decrypt_token(encrypted_token)
                if not tinybird_token:
                    return "❌ Error decrypting Tinybird token. Please reconfigure the channel using `/birdwatcher-config`."
            except Exception as e:
                print(f"Error decrypting token: {e}")
                return "❌ Error decrypting Tinybird token. Please reconfigure the channel using `/birdwatcher-config`."

            async def run_agent():
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
                    return (
                        f"I encountered an error while analyzing your request: {str(e)}"
                    )
                finally:
                    try:
                        if mcp_tools and hasattr(mcp_tools, "aclose"):
                            await mcp_tools.aclose()
                    except Exception as cleanup_error:
                        print(
                            f"Warning: Error during MCP tools cleanup: {cleanup_error}"
                        )

                    try:
                        await asyncio.sleep(0.1)
                    except Exception:
                        pass

            response = self._run_async_in_loop(run_agent())
            return response

        except Exception as e:
            print(f"Error in _process_with_agno: {e}")
            import traceback

            traceback.print_exc()
            return f"Sorry, I encountered an error processing your request: {str(e)}"

    def cleanup(self):
        try:
            if self._executor:
                self._executor.shutdown(wait=False)
        except Exception as e:
            print(f"Error shutting down executor: {e}")

        try:
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception as e:
            print(f"Error stopping event loop: {e}")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({"status": "healthy", "service": "agno-slack-bot"}).encode(
                "utf-8"
            )
        )

    async def _handle_config_command(self, parsed_data):
        """Handle the /birdwatcher-config command"""
        try:
            user_id = parsed_data.get("user_id", [""])[0]
            channel_id = parsed_data.get("channel_id", [""])[0]
            trigger_id = parsed_data.get("trigger_id", [""])[0]
            response_url = parsed_data.get("response_url", [""])[0]

            # Send immediate acknowledgment
            response = {
                "response_type": "ephemeral",
                "text": "Opening configuration modal..."
            }
            self._send_response_safely(
                200,
                "application/json",
                json.dumps(response).encode("utf-8")
            )

            # Get current config and create modal
            current_config = await get_channel_config(channel_id, user_id)
            modal = create_config_modal(channel_id, current_config)

            # Open modal using Slack API
            slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
            if not slack_token:
                self._send_followup_response(
                    response_url,
                    "❌ Error: Bot token not configured"
                )
                return

            try:
                req = urllib.request.Request(
                    "https://slack.com/api/views.open",
                    data=json.dumps({
                        "trigger_id": trigger_id,
                        "view": modal
                    }).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {slack_token}",
                        "Content-Type": "application/json"
                    }
                )

                response = urllib.request.urlopen(req)
                response_data = json.loads(response.read().decode("utf-8"))

                if not response_data.get("ok"):
                    error_msg = response_data.get("error", "Unknown error")
                    self._send_followup_response(
                        response_url,
                        f"❌ Error opening configuration modal: {error_msg}"
                    )
                    return

            except Exception as e:
                print(f"Error opening modal: {e}")
                self._send_followup_response(
                    response_url,
                    f"❌ Error opening configuration modal: {str(e)}"
                )

        except Exception as e:
            print(f"Error handling config command: {e}")
            if "response_url" in locals():
                self._send_followup_response(
                    response_url,
                    f"❌ Error processing configuration command: {str(e)}"
                )

    async def _handle_modal_submission(self, payload):
        """Handle modal submission for configuration"""
        try:
            view = payload.get("view", {})
            channel_id = view.get("private_metadata")
            user_id = payload.get("user", {}).get("id")
            values = view.get("state", {}).get("values", {})

            # Extract form values
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
            self._send_slack_message(
                channel_id,
                f"✅ Birdwatcher configuration updated successfully!"
            )

            return {"response_action": "clear"}

        except Exception as e:
            print(f"Error handling modal submission: {e}")
            return {
                "response_action": "errors",
                "errors": {
                    "tinybird_token_block": f"Error saving configuration: {str(e)}"
                }
            }
