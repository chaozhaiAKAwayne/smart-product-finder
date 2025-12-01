"""
搜索历史记录
存储和检索历史搜索记录
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class SearchHistory:
    """搜索历史记录管理"""

    def __init__(self, history_file: str = "logs/search_history.json"):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        self.load_history()

    def add_search(
        self,
        search_criteria: Dict[str, Any],
        results: Dict[str, Any],
        session_id: str = None
    ) -> str:
        """
        添加搜索记录

        Args:
            search_criteria: 搜索条件
            results: 搜索结果
            session_id: 会话ID

        Returns:
            搜索记录ID
        """
        search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        record = {
            'id': search_id,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'search_criteria': search_criteria,
            'summary': {
                'total_found': results.get('summary', {}).get('total_products_found', 0),
                'after_filtering': results.get('summary', {}).get('after_filtering', 0),
                'platforms_searched': results.get('summary', {}).get('successful_platforms', []),
                'best_price': self._get_best_price(results)
            },
            'status': results.get('status', 'unknown')
        }

        self.history.append(record)
        self.save_history()
        self.logger.info(f"Added search record: {search_id}")
        return search_id

    def _get_best_price(self, results: Dict[str, Any]) -> Optional[float]:
        """获取最低价格"""
        best_deals = results.get('best_deals', [])
        if best_deals and len(best_deals) > 0:
            return best_deals[0].get('price')
        return None

    def get_history(
        self,
        session_id: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取搜索历史

        Args:
            session_id: 会话ID（可选，用于过滤）
            limit: 返回记录数量限制

        Returns:
            搜索历史记录列表
        """
        history = self.history

        if session_id:
            history = [h for h in history if h.get('session_id') == session_id]

        # 按时间倒序排序
        history = sorted(
            history,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )

        return history[:limit]

    def get_search_by_id(self, search_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取搜索记录"""
        for record in self.history:
            if record.get('id') == search_id:
                return record
        return None

    def get_search_statistics(self, session_id: str = None) -> Dict[str, Any]:
        """
        获取搜索统计信息

        Args:
            session_id: 会话ID（可选）

        Returns:
            统计信息
        """
        history = self.history
        if session_id:
            history = [h for h in history if h.get('session_id') == session_id]

        if not history:
            return {
                'total_searches': 0,
                'successful_searches': 0,
                'failed_searches': 0,
                'most_searched_brand': None,
                'average_results': 0
            }

        successful = [h for h in history if h.get('status') == 'success']
        failed = [h for h in history if h.get('status') != 'success']

        # 统计品牌
        brand_counts = {}
        total_results = 0

        for record in successful:
            brand = record.get('search_criteria', {}).get('brand', 'Unknown')
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
            total_results += record.get('summary', {}).get('after_filtering', 0)

        most_searched_brand = max(brand_counts.items(), key=lambda x: x[1])[0] if brand_counts else None

        return {
            'total_searches': len(history),
            'successful_searches': len(successful),
            'failed_searches': len(failed),
            'most_searched_brand': most_searched_brand,
            'average_results': total_results / len(successful) if successful else 0,
            'brand_distribution': brand_counts
        }

    def save_history(self):
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save history: {str(e)}")

    def load_history(self):
        """从文件加载历史记录"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                self.logger.info(f"Loaded {len(self.history)} search records")
        except Exception as e:
            self.logger.error(f"Failed to load history: {str(e)}")
            self.history = []

    def clear_history(self, session_id: str = None):
        """
        清除历史记录

        Args:
            session_id: 如果提供，只清除该会话的记录
        """
        if session_id:
            self.history = [h for h in self.history if h.get('session_id') != session_id]
            self.logger.info(f"Cleared history for session: {session_id}")
        else:
            self.history = []
            self.logger.info("Cleared all history")

        self.save_history()
