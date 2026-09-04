"""
LLM服务模块 - 封装所有大模型调用 (FastAPI 纯净版)
"""
import concurrent.futures
import json
import logging
import queue
import threading
import time
from typing import Generator

from config.settings import NETWORK_TIMEOUT
from core.task_manager import TaskManager

# 🚀 毒瘤已摘除：彻底删除了 streamlit.runtime.scriptrunner 的导入

logger = logging.getLogger("ScriptMaster.LLM")


def _friendly_error(raw: str) -> str:
    """把技术性 API 异常翻译成客户友好的中文提示"""
    r = raw.lower()
    if "401" in raw or "auth_failed" in r or "api key" in r or "apikey" in r or "invalid api key" in r:
        return "API Key 无效或已过期，请检查系统配置"
    if "403" in raw or "forbidden" in r or "permission" in r:
        return "API Key 权限不足，请确认该 Key 已开通对应服务"
    if "429" in raw or "rate limit" in r or "too many requests" in r or "请求过于频繁" in raw:
        return "请求过于频繁，请稍后再试（建议间隔30秒以上）"
    if "timeout" in r or "timed out" in r or "连接超时" in raw:
        return "连接超时，请检查网络或更换 API 地址"
    if "connection" in r or "network" in r or "连接" in raw or "网络" in raw:
        return "网络连接失败，请检查网络或更换 API 地址"
    if "quota" in r or "额度" in raw or "余额" in raw or "limit" in r and "rate" not in r:
        return "API 额度不足或已达限额，请充值后重试"
    if "model" in r and ("not found" in r or "does not exist" in r or "不存在" in raw):
        return "模型不存在，请尝试更换其他模型"
    return raw[:120] if len(raw) > 120 else raw


def _normalize_openai_base_url(base_url: str = "") -> str:
    """规范化 OpenAI 兼容网关地址，允许用户填写域名或完整的 /v1 地址。"""
    normalized = (base_url or "").strip().rstrip("/")
    if not normalized:
        return ""

    # 用户填入 https://example.com 时，OpenAI SDK 需要以 /v1 为 API 根路径。
    from urllib.parse import urlparse
    parsed = urlparse(normalized)
    if parsed.scheme and parsed.netloc and parsed.path in ("", "/"):
        normalized = f"{normalized}/v1"
    return normalized


# 可选依赖
try:
    from google import genai
except ImportError:
    genai = None
try:
    import openai
except ImportError:
    openai = None
try:
    import anthropic
except ImportError:
    anthropic = None


class LLMService:
    """大模型服务类"""

    DEFAULT_TIMEOUT = 6000

    def __init__(self):
        self.provider: str = "Mock (演示)"
        self.api_key: str = ""
        self.model_name: str = ""
        self.base_url: str = ""
        self._client_cache = {}
        self.timeout: int = self.DEFAULT_TIMEOUT

    def configure(self, provider: str, api_key: str, model_name: str, base_url: str = ""):
        """配置 LLM 服务"""
        self.provider = provider
        if provider == "Mock (演示)":
            # Mock模式下，清空所有真实API相关配置
            self.api_key = ""
            self.model_name = "mock-model"
            self.base_url = ""
            self.client = None
            return
        # 非Mock模式下，存储真实配置
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url

        client_params = {
            "api_key": api_key,
            "timeout": NETWORK_TIMEOUT
        }

        if base_url:
            client_params["base_url"] = _normalize_openai_base_url(base_url)

        self.client = openai.OpenAI(**client_params)

    def _create_openai_client(self, base_url: str = None, timeout=None):
        """创建 OpenAI 及第三方 Responses 客户端。"""
        if timeout is None:
            timeout = NETWORK_TIMEOUT
        params = {
            "api_key": self.api_key,
            "timeout": timeout
        }
        if base_url:
            params["base_url"] = _normalize_openai_base_url(base_url)
        return openai.OpenAI(**params)

    def list_models(self, provider: str, api_key: str, base_url: str = "") -> list:
        """读取 OpenAI 兼容网关提供的模型列表，不保存密钥或临时配置。"""
        import requests

        normalized_url = _normalize_openai_base_url(base_url)
        if not normalized_url:
            normalized_url = "https://api.openai.com/v1"
        models_url = f"{normalized_url}/models"
        response = requests.get(
            models_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=NETWORK_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", []) if isinstance(payload, dict) else []
        model_ids = [
            str(item.get("id"))
            for item in data
            if isinstance(item, dict) and item.get("id")
        ]
        return sorted(set(model_ids), key=str.casefold)

    def _chat_completion_with_messages(self, client, system_prompt: str, user_prompt: str, max_tokens: int = 8192,
                                       extra_body: dict = None) -> str:
        """兼容旧版 Chat Completions 协议的平台调用方法。"""
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=max_tokens,
            **(extra_body or {})
        )
        return response.choices[0].message.content

    @staticmethod
    def _response_event_value(event, key: str, default=None):
        """同时读取 OpenAI SDK 对象和第三方返回的字典事件。"""
        if isinstance(event, dict):
            return event.get(key, default)
        return getattr(event, key, default)

    @staticmethod
    def _decode_json_response(response):
        """按 JSON 原始字节解析，避免第三方网关错误 charset 导致中文乱码。"""
        try:
            # JSON 标准响应通常使用 UTF-8；直接传入 bytes 可绕过 requests 的错误编码推断。
            return json.loads(response.content)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
            # 非标准网关响应时保留 requests 的兼容回退行为。
            return response.json()

    def _extract_responses_text(self, response) -> str:
        """提取 Responses API 的文本，兼容 SDK 对象和第三方对象。"""
        output_text = self._response_event_value(response, "output_text")
        if output_text:
            return str(output_text)

        output = self._response_event_value(response, "output", []) or []
        text_parts = []
        for item in output:
            content = self._response_event_value(item, "content", []) or []
            for part in content:
                text = self._response_event_value(part, "text")
                if text:
                    text_parts.append(str(text))
                    continue
                value = self._response_event_value(part, "value")
                if value:
                    text_parts.append(str(value))
        return "".join(text_parts)

    def _responses_create(self, client, system_prompt: str, user_prompt: str,
                          max_output_tokens: int = 8192, stream: bool = False):
        """调用 OpenAI Responses 协议，不发送 Chat Completions 字段。"""
        return client.responses.create(
            model=self.model_name,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=max_output_tokens,
            stream=stream,
        )

    def _responses_with_prompts(self, client, system_prompt: str, user_prompt: str,
                                max_output_tokens: int = 8192) -> str:
        """读取 OpenAI SDK Responses 响应中的文本。"""
        response = self._responses_create(
            client,
            system_prompt,
            user_prompt,
            max_output_tokens=max_output_tokens,
        )
        text = self._extract_responses_text(response)
        if not text:
            raise RuntimeError("Responses API 返回中没有可读取的文本")
        return text

    def _responses_http_url(self, base_url: str = "") -> str:
        normalized = _normalize_openai_base_url(base_url)
        if not normalized:
            normalized = "https://api.openai.com/v1"
        if normalized.endswith("/responses"):
            return normalized
        return f"{normalized}/responses"

    def _responses_http_request(self, system_prompt: str, user_prompt: str,
                                max_output_tokens: int = 8192) -> str:
        """使用普通 HTTP 请求调用第三方 Responses，规避网关拦截 SDK 请求特征。"""
        import requests

        response = requests.post(
            self._responses_http_url(self.base_url),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "instructions": system_prompt,
                "input": user_prompt,
                "max_output_tokens": max_output_tokens,
            },
            timeout=NETWORK_TIMEOUT,
        )
        response.raise_for_status()
        text = self._extract_responses_text(self._decode_json_response(response))
        if not text:
            raise RuntimeError("Responses API 返回中没有可读取的文本")
        return text

    def _responses_http_stream(self, system_prompt: str, user_prompt: str,
                               max_output_tokens: int = 8192) -> Generator[str, None, None]:
        """解析第三方 Responses 的 SSE 流式响应。"""
        import requests

        with requests.post(
            self._responses_http_url(self.base_url),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
            },
            json={
                "model": self.model_name,
                "instructions": system_prompt,
                "input": user_prompt,
                "max_output_tokens": max_output_tokens,
                "stream": True,
            },
            timeout=NETWORK_TIMEOUT,
            stream=True,
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=False):
                if not raw_line:
                    continue
                # 不使用 requests 根据响应头推断的编码，避免网关错误 charset 破坏中文。
                line = raw_line.decode("utf-8", errors="replace")
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    return
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if self._response_event_value(event, "type", "") == "response.output_text.delta":
                    delta = self._response_event_value(event, "delta", "")
                    if delta:
                        yield str(delta)


    def generate(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """同步生成文本 - 增强超时与重试机制"""
        if self.provider == "Mock (演示)":
            return self._mock_generate(system_prompt, user_prompt)

        logger.info(f"🚀 [LLM] 正在请求 {self.provider} ({self.model_name})...")

        last_error = None
        for attempt in range(max_retries):
            try:
                if self.provider in {"OpenAI (GPT)", "第三方 OpenAI (Responses)"}:
                    response_text = self._call_openai_responses(
                        system_prompt,
                        user_prompt,
                        timeout=(60, 120),
                    )
                else:
                    # 保持非 Responses 平台的既有专用协议处理。
                    handler = self._get_handler()
                    response_text = handler(system_prompt, user_prompt, (60, 120))

                if not response_text:
                    raise RuntimeError("API 响应为空")
                logger.info(f"✅ [LLM] 请求成功，返回 {len(response_text)} 字")
                return response_text.strip()

            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ [LLM] 第 {attempt + 1} 次请求失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                continue

        return f"❌ API 请求失败（已重试 {max_retries} 次）: {str(last_error)}"

    def generate_with_timeout(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        """生成内容（可指定超时）"""
        if timeout is None:
            timeout = self.timeout

        if self.provider == "Mock (演示)":
            return self._mock_generate(system_prompt, user_prompt)

        if not self.api_key:
            return "❌ 错误：请在配置中填写 API Key"

        try:
            handler = self._get_handler()
            raw_result = handler(system_prompt, user_prompt, timeout)
            if raw_result is None:
                return "❌ API 响应为空（可能被拦截或手动中止）"
            if isinstance(raw_result, str):
                clean_result = raw_result.replace('```', '').strip()
                return clean_result
            return str(raw_result) if raw_result else "❌ 发生未知解析异常"
        except Exception as e:
            return f"❌ API 调用异常: {_friendly_error(str(e))}"

    def generate_stream(self, system_prompt: str, user_prompt: str, timeout: int = None, task_id: str = None) -> \
    Generator[str, None, None]:
        """
        流式生成内容（实时返回），带超时保护（默认120秒）
        Yields: 生成的文本片段
        """
        if timeout is None:
            timeout = self.timeout

        if self.provider == "Mock (演示)":
            result = self._mock_generate(system_prompt, user_prompt)
            for char in result.split('\n'):
                yield char + '\n'
                time.sleep(0.02)
            return

        if not self.api_key:
            yield "❌ 错误：请在配置中填写 API Key"
            return

        result_queue = queue.Queue()
        exception_info = [None]

        def target():
            try:
                handler = self._get_handler_stream()
                for chunk in handler(system_prompt, user_prompt):
                    # 🚀 核心修改：带上 task_id 去询问大脑是否需要停止！
                    if task_id and TaskManager.should_stop(task_id):
                        logger.warning(f"🛑 [LLMService] 检测到前台停止信号，任务 {task_id} 已被强行掐断！")
                        break
                    result_queue.put(('chunk', chunk))
            except Exception as e:
                exception_info[0] = e
            finally:
                result_queue.put(('done', None))

        # 🚀 毒瘤已摘除：去掉了 get_script_run_ctx() 和 add_script_run_ctx()
        # 现在的线程是纯净的 Python 线程，极其轻量、健壮
        t = threading.Thread(target=target, daemon=True)
        t.start()

        start_time = time.time()
        while True:
            try:
                item = result_queue.get(timeout=timeout)
            except queue.Empty:
                yield "❌ 生成超时（" + str(timeout) + "秒），请检查网络或更换模型"
                return
            kind, val = item
            if kind == 'done':
                if exception_info[0]:
                    yield f"❌ API 调用异常: {_friendly_error(str(exception_info[0]))}"
                return
            yield val

    def _get_handler(self):
        """获取对应提供商的处理函数（阻塞模式）"""
        handlers = {
            "Google Gemini": self._call_gemini,
            "自定义三方Gemini": self._call_custom_gemini,
            "OpenAI (GPT)": self._call_openai,
            "第三方 OpenAI (Responses)": self._call_openai_responses,
            "Anthropic (Claude)": self._call_claude,
            "OpenRouter": self._call_openrouter,
            "阿里云通义千问": self._call_alitongyi
        }
        return handlers.get(self.provider, lambda s, u, t: "❌ 未知模型提供商")

    def _get_handler_stream(self):
        """获取对应提供商的处理函数（流式模式）"""
        handlers = {
            "Google Gemini": self._call_gemini_stream,
            "自定义三方Gemini": self._call_custom_gemini_stream,
            "OpenAI (GPT)": self._call_openai_stream,
            "第三方 OpenAI (Responses)": self._call_openai_responses_stream,
            "Anthropic (Claude)": self._call_claude_stream,
            "OpenRouter": self._call_openrouter_stream,
            "阿里云通义千问": self._call_alitongyi_stream
        }
        return handlers.get(self.provider, lambda s, u: iter([f"❌ {self.provider} 暂不支持流式输出"]))

    def _call_gemini(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        if not genai:
            return "❌ pip install google-genai"
        client = genai.Client(api_key=self.api_key, timeout=timeout)
        response = client.models.generate_content(
            model=self.model_name,
            contents=[{"parts": [{"text": user_prompt}]}],
            config={"system_instruction": system_prompt}
        )
        return response.text

    def _call_custom_gemini(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        if not openai:
            return "❌ pip install openai"
        base_url = self.base_url or "[https://generativelanguage.googleapis.com/v1beta/openai/](https://generativelanguage.googleapis.com/v1beta/openai/)"
        client = openai.OpenAI(
            base_url=base_url,
            api_key=self.api_key,
            timeout=timeout
        )
        logger.info(f"🚀 [网络请求] 正在向三方 Gemini ({self.model_name}) 发送请求...")
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=8192
            )
            raw_content = response.choices[0].message.content
            logger.info("✅ 请求成功！")
            return raw_content
        except Exception as e:
            logger.error("\n" + "!" * 20 + " API 请求直接报错了 " + "!" * 20)
            logger.error(f"错误详情: {repr(e)}")
            if hasattr(e, 'response'):
                logger.error(f"HTTP 状态码: {e.response.status_code}")
                logger.error(f"网关返回内容: {e.response.text}")
            logger.error("!" * 60 + "\n")
            raise e

    def _call_openai(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        """官方 OpenAI 统一使用 Responses API。"""
        return self._call_openai_responses(system_prompt, user_prompt, timeout)

    def _call_openai_responses(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        if not openai:
            return "❌ pip install openai"
        if self.provider == "第三方 OpenAI (Responses)":
            logger.info(f"🚀 [Responses HTTP] 正在请求 {self.model_name}...")
            return self._responses_http_request(system_prompt, user_prompt, max_output_tokens=8192)
        client = self._create_openai_client(base_url=self.base_url or None, timeout=timeout)
        logger.info(f"🚀 [Responses] 正在请求 {self.provider} ({self.model_name})...")
        return self._responses_with_prompts(client, system_prompt, user_prompt, max_output_tokens=8192)

    def _call_claude(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        if not anthropic:
            return "❌ pip install anthropic"
        client = anthropic.Anthropic(api_key=self.api_key, timeout=timeout)
        response = client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text

    def _call_openrouter(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        if not openai:
            return "❌ pip install openai"
        client = self._create_openai_client(base_url="[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)",
                                            timeout=timeout)
        return self._chat_completion_with_messages(client, system_prompt, user_prompt,
                                                   extra_body={"reasoning": {"enabled": True}})

    def _call_alitongyi(self, system_prompt: str, user_prompt: str, timeout: int = None) -> str:
        if not openai:
            return "❌ pip install openai"
        base_url = self.base_url or "[https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)"
        client = self._create_openai_client(base_url=base_url, timeout=timeout)
        return self._chat_completion_with_messages(client, system_prompt, user_prompt)

    # ============ 流式输出方法 ============
    def _stream_responses(self, client, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        """解析 Responses API 的标准增量事件。"""
        response = self._responses_create(
            client,
            system_prompt,
            user_prompt,
            max_output_tokens=8192,
            stream=True,
        )
        for event in response:
            event_type = self._response_event_value(event, "type", "")
            if event_type == "response.output_text.delta":
                delta = self._response_event_value(event, "delta", "")
                if delta:
                    yield str(delta)

    def _stream_chat_completion(self, client, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        """兼容旧版 Chat Completions 流式协议的平台调用方法。"""
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _call_custom_gemini_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not openai:
            yield "❌ pip install openai"
            return
        logger.info(f"🚀 [流式请求] 正在向三方 Gemini ({self.model_name}) 发送流式请求...")
        client = self._create_openai_client(base_url=self.base_url)
        logger.info("⏳ [流式请求] 连接成功，开始接收内容...")
        yield from self._stream_chat_completion(client, system_prompt, user_prompt)
        logger.info("✅ [流式请求] 流式输出完成！")

    def _call_openai_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        """官方 OpenAI 的流式输出统一使用 Responses API。"""
        yield from self._call_openai_responses_stream(system_prompt, user_prompt)

    def _call_openai_responses_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not openai:
            yield "❌ pip install openai"
            return
        if self.provider == "第三方 OpenAI (Responses)":
            logger.info(f"🚀 [Responses HTTP 流式请求] 正在请求 {self.model_name}...")
            yield from self._responses_http_stream(system_prompt, user_prompt, max_output_tokens=8192)
            return
        logger.info(f"🚀 [Responses 流式请求] 正在请求 {self.provider} ({self.model_name})...")
        client = self._create_openai_client(base_url=self.base_url or None)
        logger.info("⏳ [Responses 流式请求] 连接成功，开始接收内容...")
        yield from self._stream_responses(client, system_prompt, user_prompt)
        logger.info("✅ [Responses 流式请求] 流式输出完成！")

    def _call_openrouter_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not openai:
            yield "❌ pip install openai"
            return
        logger.info(f"🚀 [流式请求] 正在向 OpenRouter ({self.model_name}) 发送流式请求...")
        client = self._create_openai_client(base_url="[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)")
        logger.info("⏳ [流式请求] 连接成功，开始接收内容...")
        yield from self._stream_chat_completion(client, system_prompt, user_prompt)
        logger.info("✅ [流式请求] 流式输出完成！")

    def _call_alitongyi_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not openai:
            yield "❌ pip install openai"
            return
        base_url = self.base_url or "[https://dashscope.aliyuncs.com/compatible-mode/v1](https://dashscope.aliyuncs.com/compatible-mode/v1)"
        logger.info(f"🚀 [流式请求] 正在向通义千问 ({self.model_name}) 发送流式请求...")
        client = self._create_openai_client(base_url=base_url)
        logger.info("⏳ [流式请求] 连接成功，开始接收内容...")
        yield from self._stream_chat_completion(client, system_prompt, user_prompt)
        logger.info("✅ [流式请求] 流式输出完成！")

    def _call_gemini_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not genai:
            yield "❌ pip install google-genai"
            return
        client = genai.Client(api_key=self.api_key, timeout=self.timeout)
        response = client.models.generate_content(
            model=self.model_name,
            contents=[{"parts": [{"text": user_prompt}]}],
            config={"system_instruction": system_prompt, "streaming": True}
        )
        for chunk in response.candidates[0].content.parts:
            if chunk.text:
                yield chunk.text

    def _call_claude_stream(self, system_prompt: str, user_prompt: str) -> Generator[str, None, None]:
        if not anthropic:
            yield "❌ pip install anthropic"
            return
        client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
        with client.messages.stream(
                model=self.model_name,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text

    def generate_parallel(
            self,
            requests: list,
            max_workers: int = 3,
            start_callback: callable = None,
            result_callback: callable = None
    ) -> list:

        results = [None] * len(requests)

        def call_one(index: int, system: str, user: str):
            if start_callback:
                start_callback(index)
            try:
                result = self.generate(system, user)
                return index, result, None
            except Exception as e:
                return index, None, str(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(call_one, i, sys_p, usr_p): i
                for i, (sys_p, usr_p) in enumerate(requests)
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    idx, result, err = future.result(timeout=self.timeout)
                except concurrent.futures.TimeoutError:
                    idx = futures[future]
                    err = f"批次 {idx + 1} 调用超时（{self.timeout}s）"
                    result = None

                if err is None and isinstance(result, str) and result.startswith("❌"):
                    err = result[1:].strip()
                final_result = f"ERR:{err}" if err else result
                results[idx] = final_result
                if result_callback:
                    result_callback(idx, final_result)

        return results

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        """Mock模式返回示例数据"""
        time.sleep(0.5)
        combined_prompt = (system_prompt + user_prompt).replace(" ", "")
        # 根据 system_prompt 的关键词判断任务类型
        if "三幕式创意" in system_prompt or "36种戏剧模型" in system_prompt:
            return """
**方案 A：全球冰封：安全屋**
类型：末世/重生

第一幕：主角重生回末日前30天，疯狂囤积物资，打造末日堡垒。

第二幕：冰封降临，极寒笼罩全城。前世的仇人带着武装团伙试图攻破安全屋，主角在温暖的屋内享受红酒牛排，透过窗户欣赏仇人被冻僵。

第三幕：主角主动出击，利用安全屋的黑科技陷阱团灭仇人，正式在这个新世界称王。

---

**方案 B：低画质人生**
类型：赛博朋克/惊悚

第一幕：2099年，穷人的世界只有144p马赛克画质。主角凯为看清病危母亲的遗容，购买了黑市违禁的高清芯片。

第二幕：芯片激活瞬间，世界变成4K高清。凯发现所谓的"上流社会"全是食人的外星怪物，人类不过是它们的肉食储备。

第三幕：凯潜入中央服务器，上传"高清病毒"，强制全人类看到真相，掀起觉醒革命。

---

**方案 C：豪门假千金**
类型：逆袭/打脸爽文

第一幕：真千金回归，主角被赶出豪门，流落街头，靠捡垃圾为生。

第二幕：主角在街头偶遇神秘老人，展现惊人商业天赋，老人临终前将顶级财阀的继承权转让给她。

第三幕：主角创立公司反向收购养父集团，真相大白——她其实是更顶级财阀的遗珠，狠狠打脸所有人。
            """
        elif "分集大纲" in system_prompt or "30集" in system_prompt:
            return """
**第1集：低画质觉醒**

悬念：宴会上，主角嘲笑一位乞丐，下一秒她的视野突然崩溃。

剧情：贝拉是高层精英，享受着8K HDR的完美世界。突然她的视觉订阅到期，视野跌落到144p。她惊恐地发现，那个"乞丐"在高清模式下是一头血肉模糊的怪物。

结尾：安保将尖叫的她拖走，她死死盯着怪物消失的方向。

**第2集：跌落底层**

悬念：醒来时，贝拉发现自己躺在垃圾堆里。

剧情：她被公司开除，视觉订阅也被强制降级到最差的144p经济模式。她遇到黑客马库斯，对方递给她一块越狱芯片。

结尾：芯片植入过程剧痛难忍，贝拉停止了呼吸。

**第3集：高清之眼**

悬念：再次睁眼时，世界变得前所未有的清晰。

剧情：马库斯用急救术救回贝拉。她发现高清世界里，路人都在瑟瑟发抖——他们都在饿着肚子，而她看到的"繁华"不过是AI生成的幻觉滤镜。

结尾：贝拉的视觉系统被高清病毒感染，她第一次看到了这座城市真正的样子——一座巨大的农场，人类是饲料。
            """
        else:
            # 默认返回分镜脚本
            return """镜号,场景,画面内容 (Visual),台词 (Dialogue) & 音效 (SFX)
1,宴会厅,"贝拉站在聚光灯下，高举酒杯，眼神轻蔑地扫视全场。",旁白：在这个时代，视野决定阶层。
2,宴会厅,"突然，所有高清屏幕同时闪烁雪花，全场陷入混乱。",SFX：系统崩溃的电子音效。
3,宴会厅,"贝拉惊恐地揉眼睛，她的视野开始从8K跌落到720p、480p，最终定格在144p。",贝拉：我的……视野？不！
4,宴会厅外,"贝拉被两名安保架着拖出宴会厅，她拼命挣扎尖叫。",贝拉：放开我！那个怪物是真的！那些怪物是真的！
5,贫民窟,"贝拉从垃圾堆中醒来，周围的世界全是模糊的色块。",SFX：风声混入电子杂音。
6,贫民窟街道,"贝拉跌跌撞撞地走在街上，每个人在她眼中都是马赛克。",贝拉（独白）：这就是144p的世界……我曾经的"下等人"邻居们。
7,黑客据点,"昏暗的房间内，马库斯递过一块冒着蓝光的芯片。",马库斯：越狱芯片，能破解视觉订阅。想看真实的世界吗？
8,芯片手术台,"马库斯手持工具，芯片缓缓植入贝拉后颈。",SFX：尖锐的手术工具声，贝拉痛苦呻吟。
9,芯片手术台,"贝拉的身体剧烈抽搐，监视器显示心率为零。",马库斯：该死……又来了。
            """
