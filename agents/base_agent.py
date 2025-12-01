"""
Base Agent Class
所有专门化agent的基类，提供通用功能
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime


class BaseAgent(ABC):
    """所有agent的基类"""

    def __init__(self, name: str, logger: logging.Logger = None):
        self.name = name
        self.logger = logger or logging.getLogger(name)
        self.created_at = datetime.now()
        self.execution_count = 0

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行agent的主要任务

        Args:
            task: 任务参数字典

        Returns:
            执行结果字典
        """
        pass

    def log_execution(self, task: Dict[str, Any], result: Dict[str, Any], duration: float):
        """记录执行日志"""
        self.execution_count += 1
        self.logger.info(
            f"Agent: {self.name} | "
            f"Execution #{self.execution_count} | "
            f"Duration: {duration:.2f}s | "
            f"Task: {task.get('type', 'unknown')} | "
            f"Status: {result.get('status', 'unknown')}"
        )

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务并记录日志"""
        start_time = datetime.now()
        self.logger.info(f"Starting task: {task}")

        try:
            result = await self.execute(task)
            duration = (datetime.now() - start_time).total_seconds()
            self.log_execution(task, result, duration)
            return result
        except Exception as e:
            self.logger.error(f"Error in {self.name}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'agent': self.name
            }
