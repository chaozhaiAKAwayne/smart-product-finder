"""
Product Extractor Tool - 产品信息提取工具
使用LLM从HTML中提取结构化产品信息
"""

import json
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from anthropic import Anthropic


class ProductExtractor:
    """产品信息提取工具"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

    def clean_html(self, html: str, max_length: int = 50000) -> str:
        """清理和简化HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 移除script和style标签
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()

            # 获取文本内容
            text = soup.get_text(separator='\n', strip=True)

            # 限制长度
            if len(text) > max_length:
                text = text[:max_length] + "..."

            return text
        except Exception as e:
            self.logger.error(f"Error cleaning HTML: {str(e)}")
            return html[:max_length]

    async def extract_products(
        self,
        html: str,
        search_criteria: Dict[str, Any],
        platform: str
    ) -> List[Dict[str, Any]]:
        """
        从HTML中提取产品信息

        Args:
            html: 页面HTML
            search_criteria: 搜索条件（品牌、型号、最高价等）
            platform: 平台名称（jd/taobao/pdd）

        Returns:
            产品列表
        """
        try:
            cleaned_html = self.clean_html(html)

            prompt = f"""你是一个专业的电商产品信息提取助手。请从以下{platform}搜索结果页面中提取产品信息。

搜索条件：
- 品牌：{search_criteria.get('brand', 'N/A')}
- 型号：{search_criteria.get('model', 'N/A')}
- 最高价格：{search_criteria.get('max_price', 'N/A')}元

页面内容：
{cleaned_html}

请提取所有符合条件的产品，并返回JSON格式的列表。每个产品应包含：
- title: 产品标题（完整）
- price: 价格（数字，单位：元）
- brand: 品牌
- model: 型号
- url: 产品链接（如果有）
- shop: 店铺名称（如果有）
- platform: 平台名称

重要要求：
1. 只提取完全符合品牌和型号的产品，不要相似产品
2. 价格必须在最高价格范围内
3. 如果信息不完整或不确定，不要包含该产品
4. 品牌和型号必须精确匹配，不接受近似匹配

请直接返回JSON数组，不要其他解释：
[
  {{
    "title": "...",
    "price": 999.00,
    "brand": "...",
    "model": "...",
    "url": "...",
    "shop": "...",
    "platform": "{platform}"
  }}
]"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text.strip()

            # 尝试解析JSON
            # 提取JSON部分（可能包含在```json...```中）
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            products = json.loads(response_text)

            self.logger.info(f"Extracted {len(products)} products from {platform}")
            return products

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            self.logger.debug(f"Response text: {response_text}")
            return []
        except Exception as e:
            self.logger.error(f"Error extracting products: {str(e)}")
            return []

    def validate_product_match(
        self,
        product: Dict[str, Any],
        search_criteria: Dict[str, Any]
    ) -> bool:
        """
        验证产品是否精确匹配搜索条件

        Args:
            product: 产品信息
            search_criteria: 搜索条件

        Returns:
            是否匹配
        """
        # 检查品牌
        if 'brand' in search_criteria:
            product_brand = product.get('brand', '').lower().strip()
            expected_brand = search_criteria['brand'].lower().strip()
            if expected_brand not in product_brand and product_brand not in expected_brand:
                return False

        # 检查型号
        if 'model' in search_criteria:
            product_model = product.get('model', '').lower().strip()
            expected_model = search_criteria['model'].lower().strip()
            if expected_model not in product_model and product_model not in expected_model:
                return False

        # 检查价格
        if 'max_price' in search_criteria:
            product_price = product.get('price', float('inf'))
            if product_price > search_criteria['max_price']:
                return False

        return True
