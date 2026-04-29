import asyncio
from playwright.async_api import async_playwright
import os

class BrowserManager:
    """Handles browser automation tasks using Playwright."""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self, headless=True):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url):
        if not self.page:
            await self.start()
        if not url.startswith("http"):
            url = "https://" + url
        await self.page.goto(url, wait_until="networkidle")
        return f"Navigated to {url}"

    async def click(self, selector):
        await self.page.click(selector)
        return f"Clicked {selector}"

    async def type(self, selector, text):
        await self.page.fill(selector, text)
        return f"Typed '{text}' into {selector}"

    async def get_content(self):
        return await self.page.content()

    async def screenshot(self, filename="automation_screenshot.png"):
        path = os.path.join(os.getcwd(), "automation", filename)
        await self.page.screenshot(path=path)
        return f"Screenshot saved to {path}"

    async def extract_text(self):
        return await self.page.inner_text("body")

async def run_web_task(url, task_type="content", **kwargs):
    """Utility function to run a quick web task."""
    manager = BrowserManager()
    try:
        await manager.start()
        await manager.navigate(url)
        
        if task_type == "content":
            return await manager.extract_text()
        elif task_type == "screenshot":
            return await manager.screenshot(kwargs.get("filename", "screenshot.png"))
        elif task_type == "search":
            # Example: search on google
            await manager.type('input[name="q"]', kwargs.get("query", ""))
            await manager.page.press('input[name="q"]', "Enter")
            await manager.page.wait_for_load_state("networkidle")
            return await manager.extract_text()
        
    finally:
        await manager.stop()
