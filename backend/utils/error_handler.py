"""
全局错误处理工具类 - 后端纯净版
职责：将 Python 异常转化为前端可识别的 JSON 数据
"""
import logging
import traceback
from typing import Callable, Dict

from config.error_config import ErrorConfig

logger = logging.getLogger("ScriptMaster.ErrorHandler")


class GlobalErrorHandler:
    """
    全局错误处理器
    """

    @staticmethod
    def parse_exception(exception: Exception, context: str = "Unknown") -> Dict:
        """
        解析异常，生成标准的错误数据结构 (用于 API 返回)
        """
        # 1. 记录详细日志（带堆栈信息，方便后台查 Bug）
        logger.error(f"❌ [{context}] 发生异常: {str(exception)}", exc_info=True)

        # 2. 调用配置中心进行分类
        error_type = ErrorConfig.classify_error(exception)
        error_title, error_detail = ErrorConfig.get_friendly_message(exception)

        # 3. 构建详细的技术信息供前端“查看详情”使用
        tech_info = traceback.format_exc()

        return {
            "status": "error",
            "error_type": error_type,
            "title": error_title,
            "message": error_detail,
            "context": context,
            "details": tech_info,
            "raw_msg": str(exception)
        }

    @staticmethod
    def safe_execute(func: Callable, *args, error_context: str = "执行操作", **kwargs):
        """
        安全执行函数封装
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 仅解析错误，不再尝试渲染 UI
            return GlobalErrorHandler.parse_exception(e, error_context)


# 创建全局实例
error_handler = GlobalErrorHandler()
