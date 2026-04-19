""" 全局错误配置中心 - 仅保留逻辑与文案 """
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ErrorTemplate:
    icon: str
    title: str
    suggestion: str

class ErrorConfig:
    # 错误模板库，移除颜色配置，由前端决定展示样式
    ERROR_TEMPLATES: Dict[str, ErrorTemplate] = {
        "api_error": ErrorTemplate("🔌", "AI 服务连接失败", "请检查 API Key 或网络连接"),
        "timeout": ErrorTemplate("⏰", "请求超时", "AI 服务响应过慢，请稍后重试"),
        "rate_limit": ErrorTemplate("🚦", "请求频率过高", "请稍等片刻再试"),
        "unknown": ErrorTemplate("⚠️", "系统异常", "请联系管理员或重试")
    }

    ERROR_KEYWORDS = {
        "api_error": ['api', 'auth', 'key', '401', '403'],
        "timeout": ['timeout', 'timed out'],
        "rate_limit": ['rate limit', '429', 'too many'],
    }

    @classmethod
    def classify_error(cls, exception: Exception) -> str:
        """根据异常信息识别错误分类"""
        msg = str(exception).lower()
        for err_type, keywords in cls.ERROR_KEYWORDS.items():
            if any(k in msg for k in keywords):
                return err_type
        return "unknown"

    @classmethod
    def get_friendly_message(cls, exception: Exception) -> tuple:
        """获取友好的错误消息"""
        error_type = cls.classify_error(exception)
        template = cls.ERROR_TEMPLATES.get(error_type, cls.ERROR_TEMPLATES["unknown"])
        return template.title, str(exception)