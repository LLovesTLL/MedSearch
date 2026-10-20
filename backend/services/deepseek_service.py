import json
import logging
import re

import requests

from config import Config
from utils.call_logger import Timer, log_call, log_content_warning

logger = logging.getLogger("medsearch.deepseek")

_MAX_ATTEMPTS = 2
_MAX_CONTENT_CHARS = 8000


class DeepSeekError(Exception):
    """DeepSeek 调用失败/超时/返回格式不符。"""


def _parse_json_content(content: str) -> dict:
    """解析 AI 返回的 JSON，支持剥离 ```json 代码块包裹。"""
    if not content or not content.strip():
        raise ValueError("AI 返回内容为空")

    if len(content) > _MAX_CONTENT_CHARS:
        log_content_warning("deepseek-parse", f"内容超长: {len(content)} chars")

    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI 返回内容不是合法 JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("AI 返回内容不是 JSON 对象")
    return data


def chat_json(messages: list[dict], timeout: int, operation: str) -> dict:
    """调用 DeepSeek Chat Completions 并解析 JSON 输出，失败自动重试 1 次。

    返回解析后的 dict；最终失败抛出 DeepSeekError。
    """
    headers = {
        "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": Config.DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    last_error = ""
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            with Timer() as timer:
                resp = requests.post(
                    Config.DEEPSEEK_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
            elapsed_ms = timer.elapsed_ms

            if resp.status_code != 200:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                log_call("deepseek", operation, "chat_completions", elapsed_ms, f"failure({resp.status_code})")
                continue

            body = resp.json()
            content = body["choices"][0]["message"]["content"]
            try:
                data = _parse_json_content(content)
            except ValueError as e:
                last_error = str(e)
                log_content_warning(operation, str(e))
                log_call("deepseek", operation, "chat_completions", elapsed_ms, "failure(bad_content)")
                continue

            log_call("deepseek", operation, "chat_completions", elapsed_ms, "success")
            return data
        except requests.exceptions.Timeout:
            last_error = "请求超时"
            log_call("deepseek", operation, "chat_completions", timeout * 1000, "failure(timeout)")
        except requests.exceptions.RequestException as e:
            last_error = f"网络异常: {e}"
            log_call("deepseek", operation, "chat_completions", 0, "failure(network)")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            last_error = f"响应结构异常: {e}"
            log_content_warning(operation, last_error)
            log_call("deepseek", operation, "chat_completions", 0, "failure(bad_response)")

        if attempt < _MAX_ATTEMPTS:
            logger.info("[deepseek] operation=%s 第 %d 次失败，准备重试: %s", operation, attempt, last_error)

    raise DeepSeekError(f"DeepSeek 调用失败（operation={operation}）: {last_error}")