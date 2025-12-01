"""
拼多多搜索 Agent
专门负责在拼多多平台搜索产品
"""

import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent
from tools.browser_tool import BrowserTool
from tools.product_extractor import ProductExtractor


class PDDSearchAgent(BaseAgent):
    """拼多多搜索Agent"""

    def __init__(self, browser_tool: BrowserTool, extractor: ProductExtractor, logger=None):
        super().__init__("PDD_Search_Agent", logger)
        self.browser_tool = browser_tool
        self.extractor = extractor
        self.base_url = "https://mobile.yangkeduo.com/search_result.html"

    def build_search_url(self, search_criteria: Dict[str, Any]) -> str:
        """构建拼多多搜索URL"""
        brand = search_criteria.get('brand', '')
        model = search_criteria.get('model', '')
        keyword = f"{brand} {model}".strip()

        url = f"{self.base_url}?search_key={keyword}"
        self.logger.info(f"Built PDD search URL: {url}")
        return url

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行拼多多搜索任务

        Args:
            task: {
                'search_criteria': {
                    'brand': str,
                    'model': str,
                    'max_price': float
                },
                'max_results': int
            }

        Returns:
            {
                'status': str,
                'platform': str,
                'products': List[Dict],
                'count': int
            }
        """
        search_criteria = task.get('search_criteria', {})
        max_results = task.get('max_results', 10)

        self.logger.info(f"Starting PDD search for {search_criteria}")

        page = None
        try:
            # 创建浏览器页面
            page = await self.browser_tool.create_page()

            # 构建并访问搜索URL
            search_url = self.build_search_url(search_criteria)
            success = await self.browser_tool.navigate(page, search_url)

            if not success:
                return {
                    'status': 'error',
                    'platform': 'pdd',
                    'products': [],
                    'count': 0,
                    'error': 'Failed to navigate to PDD'
                }

            # 等待搜索结果加载
            await asyncio.sleep(4)

            # 滚动页面加载更多结果
            await self.browser_tool.scroll_page(page, scrolls=2)

            # 提取HTML
            html = await self.browser_tool.extract_html(page)

            # 使用LLM提取产品信息
            products = await self.extractor.extract_products(
                html=html,
                search_criteria=search_criteria,
                platform='pdd'
            )

            # 验证和过滤产品
            validated_products = []
            for product in products[:max_results]:
                if self.extractor.validate_product_match(product, search_criteria):
                    validated_products.append(product)

            self.logger.info(f"PDD search completed: found {len(validated_products)} products")

            return {
                'status': 'success',
                'platform': 'pdd',
                'products': validated_products,
                'count': len(validated_products)
            }

        except Exception as e:
            self.logger.error(f"PDD search failed: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'platform': 'pdd',
                'products': [],
                'count': 0,
                'error': str(e)
            }
        finally:
            if page:
                await page.close()
