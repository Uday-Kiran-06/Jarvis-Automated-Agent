import asyncio
import os
from automation.browser import run_web_task

async def test():
    print("Testing browser automation...")
    try:
        # Test content extraction
        content = await run_web_task("https://example.com", task_type="content")
        print(f"Content length: {len(content)}")
        if "Example Domain" in content:
            print("Successfully extracted content from example.com")
        else:
            print("Failed to find 'Example Domain' in content.")
            
        # Test screenshot
        screenshot_path = await run_web_task("https://example.com", task_type="screenshot", filename="test_screenshot.png")
        print(f"Screenshot result: {screenshot_path}")
        
        # Test system automation
        from automation.system import get_directory_summary
        summary = get_directory_summary(".")
        print(f"Directory Summary: {summary}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
