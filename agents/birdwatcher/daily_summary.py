import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from birdwatcher import create_agno_agent
from prompts import ECOMMERCE_DAILY_SUMMARY_PROMPT

def get_resend_tool(agent):
    for tool in getattr(agent, 'tools', []):
        if hasattr(tool, 'send_email'):
            return tool
    return None

async def generate_daily_summary():
    load_dotenv()
    tinybird_api_key = os.getenv("TINYBIRD_TOKEN")
    if not tinybird_api_key:
        raise ValueError("TINYBIRD_TOKEN is not set")
    tinybird_host = os.getenv("TINYBIRD_HOST")

    # Create the agent using the shared function
    agent, mcp_tools, _ = await create_agno_agent(
        system_prompt=ECOMMERCE_DAILY_SUMMARY_PROMPT,
        tinybird_host=tinybird_host,
        tinybird_api_key=tinybird_api_key,
        role="Ecommerce Analytics Agent",
    )

    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    prompt = f"""
    Generate a daily summary of ecommerce metrics for the period:
    From: {start_date.strftime('%Y-%m-%d %H:%M:%S')}
    To: {end_date.strftime('%Y-%m-%d %H:%M:%S')}
    Please analyze:
    1. Overall performance metrics
    2. Top performing products
    3. Customer behavior patterns
    4. Any anomalies or notable changes
    5. Recommendations for improvement
    """

    async with mcp_tools:
        try:
            # Generate the summary
            response = await agent.agenerate_response(
                prompt,
                stream=True,
                show_full_reasoning=True,
            )
            # Send email with the summary (using ResendTools if available)
            resend_tool = get_resend_tool(agent)
            if resend_tool:
                await resend_tool.send_email(
                    to_email=os.getenv("NOTIFICATION_EMAIL"),
                    subject=f"Ecommerce Daily Summary - {end_date.strftime('%Y-%m-%d')}",
                    html_content=response
                )
                print("✅ Daily summary generated and sent successfully")
            else:
                print("⚠️ ResendTools not found in agent tools. Email not sent.")
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(generate_daily_summary()) 