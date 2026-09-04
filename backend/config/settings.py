"""
全局配置模块 - 后端引擎专属版
"""
import io
import logging
import sys

# 🌟 全局网络超时配置 (单位: 秒)
# connect_timeout: 60秒, read_timeout: 120秒
NETWORK_TIMEOUT = (60, 120)

# 🌟 API 路由配置
API_BASE_URLS = {
    "自定义三方Gemini": "https://aigateway.edgecloudapp.com/v1/5087eed27d04cd00349d210e10fe620e/gemini-redbird",
    "OpenRouter": "https://openrouter.ai/api/v1",
    "阿里云通义千问": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "第三方 OpenAI (Responses)": "",
    "Google Gemini (OpenAI 兼容)": "https://generativelanguage.googleapis.com/v1beta/openai/"
}

# 🌟 模型选项配置
MODEL_OPTIONS = {
    "自定义三方Gemini": ["gemini-3.1-pro-preview"],
    "阿里云通义千问": ["qwen3-max", "qwen-plus", "qwen-turbo"],
    "Google Gemini": ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-3.1-pro-preview"],
    "OpenAI (GPT)": ["gpt-4o", "gpt-4.1", "gpt-5"],
    "第三方 OpenAI (Responses)": []
}

def setup_logger(name: str = "ScriptMaster", level: int = logging.INFO) -> logging.Logger:
    """标准化的日志输出，方便在控制台监控后端动向"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        stream = sys.stdout
        if hasattr(sys.stdout, 'buffer'):
            try:
                stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            except Exception:
                stream = sys.stdout
        console_handler = logging.StreamHandler(stream)
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
