"""
Price Validator Tool - 价格验证工具
验证产品价格是否在预算范围内，并提供价格分析
"""

import logging
from typing import List, Dict, Any


class PriceValidator:
    """价格验证和分析工具"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_price(self, price: float, max_price: float) -> bool:
        """
        验证价格是否在预算内

        Args:
            price: 产品价格
            max_price: 最高可接受价格

        Returns:
            是否在预算内
        """
        try:
            return 0 < price <= max_price
        except (TypeError, ValueError):
            self.logger.warning(f"Invalid price value: {price}")
            return False

    def filter_by_price(
        self,
        products: List[Dict[str, Any]],
        max_price: float
    ) -> List[Dict[str, Any]]:
        """
        按价格过滤产品列表

        Args:
            products: 产品列表
            max_price: 最高价格

        Returns:
            过滤后的产品列表
        """
        filtered = []
        for product in products:
            price = product.get('price', 0)
            if self.validate_price(price, max_price):
                filtered.append(product)
            else:
                self.logger.debug(
                    f"Filtered out product: {product.get('title', 'Unknown')} "
                    f"(Price: {price}, Max: {max_price})"
                )

        self.logger.info(f"Price filter: {len(products)} -> {len(filtered)} products")
        return filtered

    def analyze_prices(
        self,
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析产品价格分布

        Args:
            products: 产品列表

        Returns:
            价格分析结果
        """
        if not products:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'average': 0,
                'median': 0
            }

        prices = [p.get('price', 0) for p in products if p.get('price', 0) > 0]

        if not prices:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'average': 0,
                'median': 0
            }

        prices.sort()
        count = len(prices)
        median = prices[count // 2] if count % 2 == 1 else (prices[count // 2 - 1] + prices[count // 2]) / 2

        analysis = {
            'count': count,
            'min': min(prices),
            'max': max(prices),
            'average': sum(prices) / count,
            'median': median,
            'by_platform': {}
        }

        # 按平台分析
        for product in products:
            platform = product.get('platform', 'unknown')
            price = product.get('price', 0)

            if price > 0:
                if platform not in analysis['by_platform']:
                    analysis['by_platform'][platform] = []
                analysis['by_platform'][platform].append(price)

        # 计算每个平台的平均价格
        for platform, prices in analysis['by_platform'].items():
            analysis['by_platform'][platform] = {
                'count': len(prices),
                'average': sum(prices) / len(prices),
                'min': min(prices),
                'max': max(prices)
            }

        return analysis

    def find_best_deals(
        self,
        products: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        找出最优惠的产品

        Args:
            products: 产品列表
            top_n: 返回前N个最便宜的

        Returns:
            最优惠的产品列表
        """
        if not products:
            return []

        # 按价格排序
        sorted_products = sorted(
            products,
            key=lambda x: x.get('price', float('inf'))
        )

        best_deals = sorted_products[:top_n]

        self.logger.info(f"Found {len(best_deals)} best deals")
        return best_deals
