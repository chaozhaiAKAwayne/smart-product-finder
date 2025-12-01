"""
智能商品搜索系统 - 主入口
Multi-Agent AI System for E-commerce Product Search
"""

import asyncio
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from logger_config import setup_logger, MetricsCollector
from tools.browser_tool import BrowserTool
from tools.product_extractor import ProductExtractor
from tools.price_validator import PriceValidator
from agents.jd_search_agent import JDSearchAgent
from agents.taobao_search_agent import TaobaoSearchAgent
from agents.pdd_search_agent import PDDSearchAgent
from agents.filter_agent import FilterAgent
from agents.coordinator_agent import CoordinatorAgent
from memory.session_manager import SessionManager
from memory.search_history import SearchHistory


class SmartProductFinder:
    """智能商品搜索系统"""

    def __init__(self, config_path: str = "config.yaml"):
        # 加载配置
        self.config = self.load_config(config_path)

        # 设置日志
        self.logger = setup_logger(
            name="SmartProductFinder",
            log_level=self.config.get('log_level', 'INFO')
        )

        # 初始化指标收集器
        self.metrics = MetricsCollector()

        # 初始化会话和历史管理
        self.session_manager = SessionManager()
        self.search_history = SearchHistory()

        # 初始化工具
        self.browser_tool = None
        self.extractor = None
        self.price_validator = None

        # 初始化agents
        self.coordinator = None

        self.logger.info("=" * 60)
        self.logger.info("Smart Product Finder initialized")
        self.logger.info("=" * 60)

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    async def initialize_components(self):
        """初始化所有组件"""
        self.logger.info("Initializing components...")

        # 获取配置
        claude_config = self.config.get('claude', {})
        browser_config = self.config.get('browser', {})

        # 初始化工具
        self.browser_tool = BrowserTool(
            headless=browser_config.get('headless', False),
            timeout=browser_config.get('timeout', 30000)
        )
        await self.browser_tool.initialize()

        self.extractor = ProductExtractor(
            api_key=claude_config.get('api_key'),
            model=claude_config.get('model', 'claude-sonnet-4-5-20250929')
        )

        self.price_validator = PriceValidator()

        # 初始化agents
        jd_agent = JDSearchAgent(self.browser_tool, self.extractor, self.logger)
        taobao_agent = TaobaoSearchAgent(self.browser_tool, self.extractor, self.logger)
        pdd_agent = PDDSearchAgent(self.browser_tool, self.extractor, self.logger)
        filter_agent = FilterAgent(self.price_validator, self.logger)

        self.coordinator = CoordinatorAgent(
            jd_agent=jd_agent,
            taobao_agent=taobao_agent,
            pdd_agent=pdd_agent,
            filter_agent=filter_agent,
            logger=self.logger
        )

        self.logger.info("All components initialized successfully")

    async def search(
        self,
        brand: str,
        model: str,
        max_price: float,
        platforms: list = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        执行产品搜索

        Args:
            brand: 品牌名称
            model: 型号
            max_price: 最高价格
            platforms: 搜索平台列表 (默认: ['jd', 'taobao', 'pdd'])
            session_id: 会话ID（可选）

        Returns:
            搜索结果
        """
        start_time = datetime.now()

        # 创建或获取会话
        if not session_id:
            session_id = f"session_{start_time.strftime('%Y%m%d_%H%M%S')}"
            self.session_manager.create_session(session_id)

        self.logger.info(f"Starting search in session: {session_id}")
        self.logger.info(f"Criteria: Brand={brand}, Model={model}, MaxPrice={max_price}")

        # 获取平台列表
        if platforms is None:
            platforms = self.config.get('search', {}).get('platforms', ['jd', 'taobao', 'pdd'])

        # 准备搜索任务
        search_criteria = {
            'brand': brand,
            'model': model,
            'max_price': max_price
        }

        task = {
            'search_criteria': search_criteria,
            'platforms': platforms,
            'max_results_per_platform': self.config.get('search', {}).get('max_results_per_platform', 10),
            'parallel': True  # 使用并行搜索
        }

        # 执行搜索
        try:
            result = await self.coordinator.run(task)

            # 记录搜索历史
            search_id = self.search_history.add_search(
                search_criteria=search_criteria,
                results=result,
                session_id=session_id
            )

            # 更新会话状态
            self.session_manager.increment_search_count(session_id)
            self.session_manager.update_session_state(session_id, {
                'last_search_id': search_id,
                'last_search_time': datetime.now().isoformat()
            })

            # 记录指标
            duration = (datetime.now() - start_time).total_seconds()
            success = result.get('status') == 'success'
            products_count = len(result.get('filtered_products', []))

            for platform in platforms:
                self.metrics.record_search(success, duration, products_count, platform)

            # 添加执行时间到结果
            result['execution_time'] = duration
            result['session_id'] = session_id
            result['search_id'] = search_id

            self.logger.info(f"Search completed in {duration:.2f}s")
            self.logger.info(f"Found {products_count} products after filtering")

            return result

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'session_id': session_id
            }

    def display_results(self, result: Dict[str, Any]):
        """显示搜索结果"""
        print("\n" + "=" * 80)
        print("搜索结果 | SEARCH RESULTS")
        print("=" * 80)

        if result.get('status') != 'success':
            print(f"\n❌ 搜索失败: {result.get('error', 'Unknown error')}")
            return

        summary = result.get('summary', {})
        print(f"\n📊 摘要:")
        print(f"   搜索关键词: {summary.get('search_query', 'N/A')}")
        print(f"   最高价格: ¥{summary.get('max_price', 0)}")
        print(f"   搜索平台: {', '.join(summary.get('successful_platforms', []))}")
        print(f"   找到产品: {summary.get('total_products_found', 0)}")
        print(f"   过滤后: {summary.get('after_filtering', 0)}")
        print(f"   执行时间: {result.get('execution_time', 0):.2f}秒")

        # 价格分析
        price_analysis = result.get('price_analysis', {})
        if price_analysis.get('count', 0) > 0:
            print(f"\n💰 价格分析:")
            print(f"   最低价: ¥{price_analysis.get('min', 0):.2f}")
            print(f"   最高价: ¥{price_analysis.get('max', 0):.2f}")
            print(f"   平均价: ¥{price_analysis.get('average', 0):.2f}")
            print(f"   中位价: ¥{price_analysis.get('median', 0):.2f}")

        # 最优惠产品
        best_deals = result.get('best_deals', [])
        if best_deals:
            print(f"\n🎯 最优惠产品 TOP {len(best_deals)}:")
            for i, product in enumerate(best_deals, 1):
                print(f"\n   {i}. {product.get('title', 'N/A')[:60]}")
                print(f"      💵 价格: ¥{product.get('price', 0):.2f}")
                print(f"      🏪 平台: {product.get('platform', 'N/A').upper()}")
                print(f"      🏷️  品牌: {product.get('brand', 'N/A')}")
                print(f"      📦 型号: {product.get('model', 'N/A')}")
                if product.get('shop'):
                    print(f"      🏬 店铺: {product.get('shop', 'N/A')}")

        print("\n" + "=" * 80 + "\n")

    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up resources...")
        if self.browser_tool:
            await self.browser_tool.close()
        self.logger.info("Cleanup completed")

    def show_metrics(self):
        """显示系统指标"""
        print(self.metrics.get_summary())

    def show_history(self, session_id: str = None, limit: int = 5):
        """显示搜索历史"""
        history = self.search_history.get_history(session_id, limit)

        print("\n" + "=" * 80)
        print("搜索历史 | SEARCH HISTORY")
        print("=" * 80)

        if not history:
            print("\n没有搜索历史记录")
            return

        for i, record in enumerate(history, 1):
            criteria = record.get('search_criteria', {})
            summary = record.get('summary', {})

            print(f"\n{i}. {record.get('timestamp', 'N/A')}")
            print(f"   关键词: {criteria.get('brand', '')} {criteria.get('model', '')}")
            print(f"   最高价: ¥{criteria.get('max_price', 0)}")
            print(f"   结果数: {summary.get('after_filtering', 0)}")
            print(f"   最低价: ¥{summary.get('best_price', 'N/A')}")

        print("\n" + "=" * 80 + "\n")


async def main():
    """主函数 - 示例用法"""
    finder = SmartProductFinder()

    try:
        # 初始化组件
        await finder.initialize_components()

        # 示例搜索 1: iPhone
        print("\n🔍 搜索示例 1: iPhone 15 Pro")
        result1 = await finder.search(
            brand="Apple",
            model="iPhone 15 Pro",
            max_price=8999.0,
            platforms=['jd', 'taobao']
        )
        finder.display_results(result1)

        # 示例搜索 2: 小米手机
        print("\n🔍 搜索示例 2: 小米14")
        result2 = await finder.search(
            brand="小米",
            model="小米14",
            max_price=3999.0,
            platforms=['jd', 'pdd']
        )
        finder.display_results(result2)

        # 显示历史记录
        finder.show_history()

        # 显示系统指标
        finder.show_metrics()

    finally:
        # 清理资源
        await finder.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
