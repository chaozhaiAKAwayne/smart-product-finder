"""
日志配置模块
提供统一的日志配置和可观测性功能
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "smart_product_finder",
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        log_level: 日志级别
        console_output: 是否输出到控制台

    Returns:
        配置好的日志记录器
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # 清除现有的handlers
    logger.handlers.clear()

    # 定义日志格式
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件handler - 所有日志
    log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 错误日志单独记录
    error_log_file = log_path / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # 控制台handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # 控制台使用更简洁的格式
        console_formatter = logging.Formatter(
            fmt='%(levelname)-8s | %(name)-20s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 防止日志传播到root logger
    logger.propagate = False

    return logger


class MetricsCollector:
    """指标收集器 - 收集系统运行指标"""

    def __init__(self):
        self.metrics = {
            'searches_total': 0,
            'searches_success': 0,
            'searches_failed': 0,
            'products_found': 0,
            'platforms_queried': {'jd': 0, 'taobao': 0, 'pdd': 0},
            'average_search_time': 0.0,
            'search_times': []
        }

    def record_search(self, success: bool, duration: float, products_count: int, platform: str):
        """记录搜索指标"""
        self.metrics['searches_total'] += 1

        if success:
            self.metrics['searches_success'] += 1
            self.metrics['products_found'] += products_count
        else:
            self.metrics['searches_failed'] += 1

        if platform in self.metrics['platforms_queried']:
            self.metrics['platforms_queried'][platform] += 1

        self.metrics['search_times'].append(duration)
        self.metrics['average_search_time'] = sum(self.metrics['search_times']) / len(self.metrics['search_times'])

    def get_metrics(self) -> dict:
        """获取所有指标"""
        return self.metrics.copy()

    def get_summary(self) -> str:
        """获取指标摘要"""
        success_rate = (
            self.metrics['searches_success'] / self.metrics['searches_total'] * 100
            if self.metrics['searches_total'] > 0
            else 0
        )

        return f"""
        Metrics Summary:
        ================
        Total Searches: {self.metrics['searches_total']}
        Successful: {self.metrics['searches_success']} ({success_rate:.1f}%)
        Failed: {self.metrics['searches_failed']}
        Products Found: {self.metrics['products_found']}
        Avg Search Time: {self.metrics['average_search_time']:.2f}s

        Platform Queries:
        - JD: {self.metrics['platforms_queried']['jd']}
        - Taobao: {self.metrics['platforms_queried']['taobao']}
        - PDD: {self.metrics['platforms_queried']['pdd']}
        """
