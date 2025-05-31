import asyncio
import os
import random
import time
from dotenv import load_dotenv
from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from playwright_stealth import stealth_async
from playwright.async_api import async_playwright
import json

load_dotenv()

# Human-like interaction delays
MIN_DELAY = 3.0
MAX_DELAY = 3.0
TYPING_DELAY = 0.5

def random_delay():
    """Generate a random delay between actions."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

def human_like_typing(text):
    """Simulate human-like typing with random delays."""
    for char in text:
        time.sleep(random.uniform(0.05, 0.15))
    random_delay()

async def setup_stealth_browser():
    """Set up a stealth browser with human-like properties."""
    p = await async_playwright().start()
    
    # Launch browser in visible mode with realistic viewport
    browser = await p.chromium.launch(
        headless=False,
        args=[
            '--start-maximized',
            '--disable-blink-features=AutomationControlled'
        ]
    )
    
    # Create context with realistic properties
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        locale='en-US',
        timezone_id='America/New_York',
        geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
        permissions=['geolocation'],
        color_scheme='light',
        device_scale_factor=1,
        is_mobile=False,
        has_touch=False
    )
    
    # Create new page and apply stealth
    page = await context.new_page()
    await stealth_async(page)
    
    # Add human-like mouse movement
    await page.mouse.move(
        random.randint(0, 1920),
        random.randint(0, 1080),
        steps=random.randint(10, 20)
    )
    
    return p, browser, context, page

def run_browser_agent(prompt: str):
    """
    Run the browser agent with the given prompt using Gemini LLM.
    Includes stealth configurations and human-like interactions.
    
    Args:
        prompt (str): The natural language prompt for the browser agent
        
    Returns:
        str: The result of the browser automation
    """
    async def _run():
        # Set up stealth browser
        playwright, browser, context, page = await setup_stealth_browser()
        try:
            # Configure agent with stealth browser
            agent = Agent(
                task=prompt,
                llm=ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                ),
                enable_memory=False  # Disable memory features to avoid serialization issues
            )
            
            # Add custom interaction handlers
            async def handle_captcha():
                if await page.is_visible('iframe[src*="captcha"]'):
                    print("CAPTCHA detected! Please solve it manually...")
                    await page.wait_for_selector('iframe[src*="captcha"]', state='hidden', timeout=3000000000)
                    random_delay()
            
            try:
                result = await agent.run()
                await handle_captcha()
                
                # Convert result to string if it's not already
                if not isinstance(result, str):
                    try:
                        result = json.dumps(result)
                    except:
                        result = str(result)
                
                return result
            except Exception as agent_exc:
                # Handle browser context closed or agent errors
                if 'closed' in str(agent_exc).lower():
                    return "Error: Browser context or page was closed unexpectedly. Please try again."
                return f"Error: {str(agent_exc)}"
        finally:
            # Clean up browser context
            try:
                await context.close()
            except Exception as e:
                pass  # Context may already be closed
            try:
                await browser.close()
            except Exception as e:
                pass  # Browser may already be closed
            try:
                await playwright.stop()
            except Exception as e:
                pass  # Playwright may already be stopped
    return asyncio.run(_run()) 