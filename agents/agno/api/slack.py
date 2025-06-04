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

# File to store processed message IDs
PROCESSED_MESSAGES_FILE = os.path.join(tempfile.gettempdir(), "slack_bot_processed_messages.txt")

# Bird-themed thinking messages with fun facts (100 amazing bird facts!)
THINKING_MESSAGES = [
    # Speed & Performance (10)
    "Processing your request, please wait. In the meanwhile did you know Arctic Terns have the longest migration of any bird at 44,000 miles annually? 🐦",
    "Analyzing your query, please wait. In the meanwhile did you know Peregrine Falcons are the fastest birds, diving at 240+ mph? 🦅",
    "Working on your data, please wait. In the meanwhile did you know Ruby-throated Hummingbirds have a heartbeat of 1,260 BPM? 💓",
    "Examining your request, please wait. In the meanwhile did you know Hummingbirds beat their wings 80 times per second? 🌺",
    "Investigating your query, please wait. In the meanwhile did you know Woodpeckers can peck 20 times per second? 🔨",
    "Processing your analysis, please wait. In the meanwhile did you know Barn Swallows catch insects mid-flight with incredible precision? 🦟",
    "Computing your request, please wait. In the meanwhile did you know Roadrunners can run 20 mph and rarely fly? 🏃‍♂️",
    "Evaluating your data, please wait. In the meanwhile did you know Golden Eagles can dive at speeds over 150 mph? ⚡",
    "Reviewing your query, please wait. In the meanwhile did you know Giant Hummingbirds have the slowest wing beats at 10 per second? 🦋",
    "Calculating your metrics, please wait. In the meanwhile did you know Ostriches are the fastest running birds at 45 mph? 🏃‍♀️",
    
    # Vision & Precision (10)
    "Scanning your request, please wait. In the meanwhile did you know Eagles can spot a rabbit from 2 miles away? 👁️",
    "Searching through data, please wait. In the meanwhile did you know Owls have silent flight and asymmetrical ears for precise hunting? 🦉",
    "Focusing on your query, please wait. In the meanwhile did you know Hawks have vision 8 times better than humans? 🔍",
    "Examining your metrics, please wait. In the meanwhile did you know Vultures can see a 3-foot carcass from 4 miles up? 🦅",
    "Detecting patterns, please wait. In the meanwhile did you know Kestrels can see UV light to track rodent urine trails? 🌈",
    "Observing your data, please wait. In the meanwhile did you know Secretary Birds can see small prey from 100 feet away? 👀",
    "Tracking your request, please wait. In the meanwhile did you know Goshawks can navigate through dense forests at high speed? 🌲",
    "Monitoring progress, please wait. In the meanwhile did you know Kingfishers calculate light refraction when diving for fish? 🐟",
    "Watching for insights, please wait. In the meanwhile did you know Caracaras are among the smartest raptors and use tools? 🧠",
    "Surveying your query, please wait. In the meanwhile did you know Condors can soar at 15,000 feet altitude? ⛰️",
    
    # Intelligence & Memory (10)
    "Caching your request, please wait. In the meanwhile did you know Clark's Nutcrackers remember over 30,000 seed locations? 🥜",
    "Calculating results, please wait. In the meanwhile did you know African Grey Parrots can count and do basic math? 🧮",
    "Problem-solving your query, please wait. In the meanwhile did you know Crows make and use tools and can recognize human faces? 🔧",
    "Learning from your data, please wait. In the meanwhile did you know Mockingbirds can learn over 200 different songs? 🎵",
    "Remembering context, please wait. In the meanwhile did you know Pigeons can find their way home from 1,300 miles away? 🧭",
    "Strategizing analysis, please wait. In the meanwhile did you know Ravens can plan up to 3 steps ahead? ♟️",
    "Adapting to your request, please wait. In the meanwhile did you know Keas (New Zealand parrots) learned to remove car parts? 🚗",
    "Innovating solutions, please wait. In the meanwhile did you know Caledonian Crows craft hooks from twigs to extract insects? 🪝",
    "Communicating with systems, please wait. In the meanwhile did you know Prairie Dogs have specific calls for different predators? 📢",
    "Recognizing patterns, please wait. In the meanwhile did you know Magpies pass the mirror self-recognition test? 🪞",
    
    # Colors & Beauty (10)
    "Shimmering through data, please wait. In the meanwhile did you know Peacocks have over 200 eye spots on their tail feathers? 🦚",
    "Glowing with insights, please wait. In the meanwhile did you know Resplendent Quetzals have tail feathers up to 3 feet long? ✨",
    "Changing approach, please wait. In the meanwhile did you know Mallard Drakes have iridescent green heads during breeding season? 💚",
    "Sparkling with analysis, please wait. In the meanwhile did you know Sunbirds have metallic plumage that reflects light like jewels? 💎",
    "Flashing through queries, please wait. In the meanwhile did you know Cardinals get their bright red color from carotenoids in their diet? ❤️",
    "Displaying results, please wait. In the meanwhile did you know male Birds-of-Paradise have elaborate courtship dances? 💃",
    "Radiating progress, please wait. In the meanwhile did you know Goldfinches have bright yellow plumage in spring? 🌻",
    "Gleaming with data, please wait. In the meanwhile did you know Starlings have iridescent feathers with oil-slick colors? 🌈",
    "Blazing through metrics, please wait. In the meanwhile did you know male Scarlet Tanagers are brilliant red with black wings? 🔥",
    "Dazzling with insights, please wait. In the meanwhile did you know Wood Ducks are the most colorful North American waterfowl? 🎨",
    
    # Sounds & Communication (10)
    "Echoing your request, please wait. In the meanwhile did you know Canyon Wren songs cascade down rock walls like echoes? 🏔️",
    "Drumming up results, please wait. In the meanwhile did you know Woodpecker drumming can be heard up to a mile away? 🥁",
    "Singing through data, please wait. In the meanwhile did you know Nightingales can produce over 1,000 different sounds? 🎼",
    "Calling for insights, please wait. In the meanwhile did you know Loon calls carry across lakes for miles? 🌊",
    "Whistling through queries, please wait. In the meanwhile did you know White-throated Sparrows sing a clear 'Old Sam Peabody' song? 🎵",
    "Honking for attention, please wait. In the meanwhile did you know Canada Geese communicate during 1,000+ mile migrations? 📯",
    "Chattering with systems, please wait. In the meanwhile did you know Magpies are among the most vocal and social birds? 💬",
    "Trilling through analysis, please wait. In the meanwhile did you know Canaries have been bred for 400+ years for their beautiful songs? 🎤",
    "Booming with progress, please wait. In the meanwhile did you know male Bittern calls can be heard 3 miles away? 📢",
    "Mimicking your request, please wait. In the meanwhile did you know Lyrebirds can imitate chainsaws, camera shutters, and car alarms? 🎭",
    
    # Migration & Navigation (10)
    "Navigating your data, please wait. In the meanwhile did you know Bar-tailed Godwits fly 7,000 miles non-stop from Alaska to New Zealand? 🗺️",
    "Journeying through metrics, please wait. In the meanwhile did you know Ruby-throated Hummingbirds cross 500 miles of Gulf of Mexico? 🌊",
    "Traveling through queries, please wait. In the meanwhile did you know Sandhill Cranes use thermal currents to soar up to 13,000 feet? 🌡️",
    "Following your request, please wait. In the meanwhile did you know Swainson's Hawks make a 17,000 mile round trip migration? 🦋",
    "Crossing data boundaries, please wait. In the meanwhile did you know Red Knots fly from the Arctic all the way to Argentina? 🌎",
    "Using magnetic insights, please wait. In the meanwhile did you know Robins can actually see Earth's magnetic field? 🧲",
    "Timing your analysis, please wait. In the meanwhile did you know Swallows return to the same nesting site within days each year? ⏰",
    "Enduring the process, please wait. In the meanwhile did you know male Emperor Penguins incubate eggs in -40°F for 64 days? 🥶",
    "Persisting with queries, please wait. In the meanwhile did you know Albatrosses can fly for hours without flapping their wings? 🌬️",
    "Orienting to your needs, please wait. In the meanwhile did you know Indigo Buntings navigate using star patterns? ⭐",
    
    # Unique Behaviors (10)
    "Collecting your data, please wait. In the meanwhile did you know male Bowerbirds build elaborate displays to attract mates? 🏗️",
    "Gathering insights, please wait. In the meanwhile did you know Magpies are attracted to shiny objects and are very intelligent? ✨",
    "Organizing results, please wait. In the meanwhile did you know Weaver Birds create intricate hanging nests? 🪺",
    "Filtering your request, please wait. In the meanwhile did you know Flamingos filter 20 beaks of water per bite when feeding? 🦩",
    "Hunting for patterns, please wait. In the meanwhile did you know Great Blue Herons are masters of patience when hunting? 🎣",
    "Flocking to your query, please wait. In the meanwhile did you know Starling murmurations can have millions of birds? ✨",
    "Assembling analysis, please wait. In the meanwhile did you know Emperor Penguins huddle together in -40°F weather? 🐧",
    "Soaring through data, please wait. In the meanwhile did you know Albatrosses can glide for hours without flapping? 🌊",
    "Storing your request, please wait. In the meanwhile did you know Acorn Woodpeckers cache up to 50,000 acorns in trees? 🌰",
    "Cooperating with systems, please wait. In the meanwhile did you know Harris's Hawks hunt in coordinated packs? 🤝",
    
    # Size & Scale (10)
    "Towering over data, please wait. In the meanwhile did you know Shoebill Storks are 5 feet tall with massive bills? 🦆",
    "Tiny but mighty processing, please wait. In the meanwhile did you know Bee Hummingbirds are the world's smallest birds at only 2 inches long? 🐝",
    "Massive data analysis, please wait. In the meanwhile did you know Wandering Albatrosses have 11-foot wingspans, the largest of any bird? 🌊",
    "Compact query handling, please wait. In the meanwhile did you know Goldcrests are Europe's smallest birds and weigh less than a penny? 🪙",
    "Enormous request processing, please wait. In the meanwhile did you know California Condors have 9.5-foot wingspans and were nearly extinct? 🦅",
    "Petite but powerful, please wait. In the meanwhile did you know Vervain Hummingbirds weigh less than a dime? 💰",
    "Gigantic analysis underway, please wait. In the meanwhile did you know Dalmatian Pelicans can have 12-foot wingspans? 🦢",
    "Miniature miracles happening, please wait. In the meanwhile did you know Weebills are Australia's smallest birds? 🇦🇺",
    "Colossal computations running, please wait. In the meanwhile did you know Andean Condors are the heaviest flying birds in the Western Hemisphere? ⛰️",
    "Delicate data handling, please wait. In the meanwhile did you know Firecrests weigh only 4-7 grams? 🔥",
    
    # Feeding & Diet (10)
    "Nectar-sweet analysis, please wait. In the meanwhile did you know Hummingbirds visit over 1,000 flowers per day? 🌸",
    "Seed-cracking your query, please wait. In the meanwhile did you know Cardinals have powerful beaks that can crush tough seeds? 🌰",
    "Fish-catching insights, please wait. In the meanwhile did you know Kingfishers dive headfirst into water to catch fish? 🐟",
    "Insect-hunting for data, please wait. In the meanwhile did you know Flycatchers catch prey mid-air with incredible precision? 🦟",
    "Fruit-bearing results, please wait. In the meanwhile did you know Toucans help disperse seeds across rainforests? 🍓",
    "Meat-and-potatoes analysis, please wait. In the meanwhile did you know Vultures have stomach acid strong enough to kill bacteria? 🦴",
    "Nut-cracking your request, please wait. In the meanwhile did you know Nutcrackers can crack pine nuts with their specialized bills? 🥜",
    "Worm-hunting for answers, please wait. In the meanwhile did you know Robins can hear earthworms moving underground? 🪱",
    "Honey-sweet processing, please wait. In the meanwhile did you know Honeyguides lead humans to beehives? 🍯",
    "Plankton-filtering data, please wait. In the meanwhile did you know Flamingos have specialized bills that filter tiny organisms? 🦐",
    
    # Extreme Adaptations (10)
    "Diving deep into data, please wait. In the meanwhile did you know Emperor Penguins can dive 1,800 feet deep for 22 minutes? 🏊‍♂️",
    "Surviving the analysis, please wait. In the meanwhile did you know Snowy Owls hunt in Arctic temperatures down to -40°F? ❄️",
    "Climbing through queries, please wait. In the meanwhile did you know Woodpecker tail feathers act as a tripod for support when climbing? 🧗‍♂️",
    "Swimming through metrics, please wait. In the meanwhile did you know Penguins can 'fly' underwater at 22 mph? 🏊‍♀️",
    "Sleeping on your request... just kidding! In the meanwhile did you know Swifts can sleep while flying at altitude? 😴",
    "Hovering over data, please wait. In the meanwhile did you know Kestrels can remain stationary in strong winds by hovering? 🌪️",
    "Backwards-engineering insights, please wait. In the meanwhile did you know Hummingbirds are the only birds that can fly backwards? ⬅️",
    "Upside-down thinking, please wait. In the meanwhile did you know Nuthatches walk headfirst down tree trunks? 🙃",
    "Waterproofing your analysis, please wait. In the meanwhile did you know Ducks have oil glands that keep their feathers completely dry? 💧",
    "Camouflaging complexity, please wait. In the meanwhile did you know Potoos look exactly like broken tree branches for camouflage? 🌳"
]

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
                    command = parsed_data.get("command", [""])[0]

                    if command in ["/agno-metrics", "/agno", "/agno-help"]:
                        text = parsed_data.get("text", [""])[0]
                        user_id = parsed_data.get("user_id", [""])[0]
                        channel_id = parsed_data.get("channel_id", [""])[0]
                        response_url = parsed_data.get("response_url", [""])[0]
                        if command == "/birdwatcher":
                            if not text:
                                query_text = (
                                    "How can I help you analyze your organization data?"
                                )
                            else:
                                query_text = text
                        else:
                            query_text = text or "How can I help you?"

                        response = {
                            "response_type": "in_channel",
                            "text": random.choice(THINKING_MESSAGES),
                        }

                        self._send_response_safely(
                            200,
                            "application/json",
                            json.dumps(response).encode("utf-8"),
                        )

                        def process_slash_command():
                            try:
                                response_text = self._process_with_agno(
                                    query_text, user_id, channel_id
                                )

                                if response_url:
                                    self._send_followup_response(
                                        response_url, response_text
                                    )
                            except Exception as e:
                                print(f"Error processing slash command: {e}")
                                if response_url:
                                    self._send_followup_response(
                                        response_url,
                                        f"Sorry, I encountered an error: {str(e)}",
                                    )

                        try:
                            self._executor.submit(process_slash_command)
                        except Exception as e:
                            print(f"Error submitting slash command to executor: {e}")
                            thread = threading.Thread(target=process_slash_command)
                            thread.daemon = True
                            thread.start()
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

                    response = self._process_with_agno(
                        user_message, user, channel, reply_thread_ts
                    )

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

    def _process_with_agno(
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
                        tinybird_host=os.getenv("TINYBIRD_HOST"),
                        tinybird_api_key=os.getenv("TINYBIRD_API_KEY"),
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
