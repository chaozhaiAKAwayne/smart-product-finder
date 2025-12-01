"""
协调 Agent
负责协调多个搜索agent并行工作，汇总结果
"""

import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .jd_search_agent import JDSearchAgent
from .taobao_search_agent import TaobaoSearchAgent
from .pdd_search_agent import PDDSearchAgent
from .filter_agent import FilterAgent


class CoordinatorAgent(BaseAgent):
    """协调Agent - 管理多个搜索agent并行执行"""

    def __init__(
        self,
        jd_agent: JDSearchAgent,
        taobao_agent: TaobaoSearchAgent,
        pdd_agent: PDDSearchAgent,
        filter_agent: FilterAgent,
        logger=None
    ):
        super().__init__("Coordinator_Agent", logger)
        self.jd_agent = jd_agent
        self.taobao_agent = taobao_agent
        self.pdd_agent = pdd_agent
        self.filter_agent = filter_agent

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行协调任务

        Args:
            task: {
                'search_criteria': {
                    'brand': str,
                    'model': str,
                    'max_price': float
                },
                'platforms': List[str],  # ['jd', 'taobao', 'pdd']
                'max_results_per_platform': int,
                'parallel': bool  # 是否并行搜索
            }

        Returns:
            {
                'status': str,
                'search_criteria': Dict,
                'results_by_platform': Dict[str, Dict],
                'all_products': List[Dict],
                'filtered_products': List[Dict],
                'best_deals': List[Dict],
                'price_analysis': Dict,
                'summary': Dict
            }
        """
        search_criteria = task.get('search_criteria', {})
        platforms = task.get('platforms', ['jd', 'taobao', 'pdd'])
        max_results = task.get('max_results_per_platform', 10)
        parallel = task.get('parallel', True)

        self.logger.info(
            f"Coordinator starting search: {search_criteria} "
            f"on platforms: {platforms} "
            f"(parallel={parallel})"
        )

        try:
            # 准备搜索任务
            search_tasks = []
            agent_map = {
                'jd': self.jd_agent,
                'taobao': self.taobao_agent,
                'pdd': self.pdd_agent
            }

            search_task_params = {
                'search_criteria': search_criteria,
                'max_results': max_results
            }

            # 创建搜索任务
            for platform in platforms:
                if platform in agent_map:
                    agent = agent_map[platform]
                    search_tasks.append((platform, agent.run(search_task_params)))

            # 执行搜索（并行或顺序）
            if parallel:
                self.logger.info("Executing parallel search across platforms")
                results = await asyncio.gather(*[task for _, task in search_tasks])
            else:
                self.logger.info("Executing sequential search across platforms")
                results = []
                for platform, task in search_tasks:
                    result = await task
                    results.append(result)
                    self.logger.info(f"Completed search for {platform}")

            # 汇总结果
            results_by_platform = {}
            all_products = []

            for i, (platform, _) in enumerate(search_tasks):
                result = results[i]
                results_by_platform[platform] = result

                if result.get('status') == 'success':
                    products = result.get('products', [])
                    all_products.extend(products)
                    self.logger.info(
                        f"Platform {platform}: {len(products)} products"
                    )
                else:
                    self.logger.warning(
                        f"Platform {platform} failed: {result.get('error', 'Unknown error')}"
                    )

            # 使用FilterAgent过滤和分析结果
            filter_task = {
                'products': all_products,
                'search_criteria': search_criteria,
                'filter_duplicates': True,
                'sort_by': 'price'
            }

            filter_result = await self.filter_agent.run(filter_task)

            # 生成摘要
            summary = self.generate_summary(
                search_criteria,
                results_by_platform,
                filter_result
            )

            self.logger.info(f"Coordinator completed: {summary}")

            return {
                'status': 'success',
                'search_criteria': search_criteria,
                'results_by_platform': results_by_platform,
                'all_products': all_products,
                'filtered_products': filter_result.get('filtered_products', []),
                'best_deals': filter_result.get('best_deals', []),
                'price_analysis': filter_result.get('price_analysis', {}),
                'summary': summary
            }

        except Exception as e:
            self.logger.error(f"Coordinator failed: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'search_criteria': search_criteria
            }

    def generate_summary(
        self,
        search_criteria: Dict[str, Any],
        results_by_platform: Dict[str, Dict],
        filter_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成搜索摘要"""
        total_found = sum(
            r.get('count', 0)
            for r in results_by_platform.values()
            if r.get('status') == 'success'
        )

        successful_platforms = [
            p for p, r in results_by_platform.items()
            if r.get('status') == 'success'
        ]

        failed_platforms = [
            p for p, r in results_by_platform.items()
            if r.get('status') != 'success'
        ]

        return {
            'total_products_found': total_found,
            'after_filtering': filter_result.get('filtered_count', 0),
            'successful_platforms': successful_platforms,
            'failed_platforms': failed_platforms,
            'search_query': f"{search_criteria.get('brand', '')} {search_criteria.get('model', '')}".strip(),
            'max_price': search_criteria.get('max_price', 0)
        }
