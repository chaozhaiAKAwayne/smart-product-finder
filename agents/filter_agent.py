"""
过滤 Agent
负责过滤和排序产品结果
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from tools.price_validator import PriceValidator


class FilterAgent(BaseAgent):
    """过滤Agent"""

    def __init__(self, price_validator: PriceValidator, logger=None):
        super().__init__("Filter_Agent", logger)
        self.price_validator = price_validator

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行过滤任务

        Args:
            task: {
                'products': List[Dict],
                'search_criteria': Dict,
                'filter_duplicates': bool,
                'sort_by': str  # 'price', 'platform', etc.
            }

        Returns:
            {
                'status': str,
                'filtered_products': List[Dict],
                'original_count': int,
                'filtered_count': int,
                'price_analysis': Dict
            }
        """
        products = task.get('products', [])
        search_criteria = task.get('search_criteria', {})
        filter_duplicates = task.get('filter_duplicates', True)
        sort_by = task.get('sort_by', 'price')

        self.logger.info(f"Starting filter task with {len(products)} products")

        try:
            original_count = len(products)

            # 1. 价格过滤
            max_price = search_criteria.get('max_price')
            if max_price:
                products = self.price_validator.filter_by_price(products, max_price)
                self.logger.info(f"After price filter: {len(products)} products")

            # 2. 去重（基于标题和价格的相似度）
            if filter_duplicates:
                products = self.remove_duplicates(products)
                self.logger.info(f"After deduplication: {len(products)} products")

            # 3. 排序
            products = self.sort_products(products, sort_by)
            self.logger.info(f"Products sorted by: {sort_by}")

            # 4. 价格分析
            price_analysis = self.price_validator.analyze_prices(products)

            # 5. 找出最优惠的产品
            best_deals = self.price_validator.find_best_deals(products, top_n=5)

            return {
                'status': 'success',
                'filtered_products': products,
                'original_count': original_count,
                'filtered_count': len(products),
                'price_analysis': price_analysis,
                'best_deals': best_deals
            }

        except Exception as e:
            self.logger.error(f"Filter failed: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'filtered_products': [],
                'original_count': len(products),
                'filtered_count': 0,
                'error': str(e)
            }

    def remove_duplicates(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去除重复产品

        Args:
            products: 产品列表

        Returns:
            去重后的产品列表
        """
        seen = set()
        unique_products = []

        for product in products:
            # 使用标题和价格作为唯一标识
            title = product.get('title', '').lower().strip()
            price = product.get('price', 0)
            key = f"{title}_{price}"

            if key not in seen:
                seen.add(key)
                unique_products.append(product)
            else:
                self.logger.debug(f"Duplicate found: {title[:50]}...")

        removed = len(products) - len(unique_products)
        if removed > 0:
            self.logger.info(f"Removed {removed} duplicate products")

        return unique_products

    def sort_products(
        self,
        products: List[Dict[str, Any]],
        sort_by: str = 'price'
    ) -> List[Dict[str, Any]]:
        """
        排序产品列表

        Args:
            products: 产品列表
            sort_by: 排序字段 ('price', 'platform', 'title')

        Returns:
            排序后的产品列表
        """
        if sort_by == 'price':
            return sorted(products, key=lambda x: x.get('price', float('inf')))
        elif sort_by == 'platform':
            return sorted(products, key=lambda x: x.get('platform', ''))
        elif sort_by == 'title':
            return sorted(products, key=lambda x: x.get('title', ''))
        else:
            return products
