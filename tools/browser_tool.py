"""
Browser Tool - 浏览器自动化工具
使用Playwright进行网页抓取
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext


class BrowserTool:
    """浏览器自动化工具"""

    def __init__(self, headless: bool = False, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """初始化浏览器"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            self.logger.info("Browser initialized successfully")

    async def create_page(self) -> Page:
        """创建新页面"""
        await self.initialize()
        page = await self.context.new_page()
        page.set_default_timeout(self.timeout)
        return page

    async def navigate(self, page: Page, url: str, wait_for: str = 'networkidle') -> bool:
        """
        导航到指定URL

        Args:
            page: 页面对象
            url: 目标URL
            wait_for: 等待条件 ('load', 'domcontentloaded', 'networkidle')

        Returns:
            是否成功
        """
        try:
            await page.goto(url, wait_until=wait_for)
            await asyncio.sleep(2)  # 额外等待动态内容加载
            self.logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {str(e)}")
            return False

    async def extract_html(self, page: Page) -> str:
        """提取页面HTML"""
        try:
            html = await page.content()
            return html
        except Exception as e:
            self.logger.error(f"Failed to extract HTML: {str(e)}")
            return ""

    async def scroll_page(self, page: Page, scrolls: int = 3):
        """滚动页面以加载动态内容"""
        try:
            for i in range(scrolls):
                await page.evaluate('window.scrollBy(0, window.innerHeight)')
                await asyncio.sleep(1)
            self.logger.info(f"Scrolled page {scrolls} times")
        except Exception as e:
            self.logger.error(f"Failed to scroll page: {str(e)}")

    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("Browser closed")
