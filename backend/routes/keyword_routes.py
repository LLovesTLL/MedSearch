import logging

from flask import Blueprint, jsonify, request

from config import Config
from services.deepseek_service import DeepSeekError, chat_json
from utils.call_logger import log_content_warning

logger = logging.getLogger("medsearch.keyword")

keyword_bp = Blueprint("keywords", __name__)

_KEYWORD_SYSTEM_PROMPT = (
    "你是医学文献检索专家。根据用户输入的疾病、病理或研究方向描述，"
    "提取恰好 3 个中文检索关键词。关键词应为专业医学核心术语，"
    "每个关键词 2-10 个汉字，互不重复，适合用于 PubMed 检索。"
    '仅输出 JSON，格式为 {"keywords": ["关键词1", "关键词2", "关键词3"]}。'
)


@keyword_bp.post("/api/keywords/generate")
def generate_keywords():
    payload = request.get_json(silent=True) or {}
    description = str(payload.get("description", "")).strip()

    if len(description) < 10 or len(description) > 300:
        return jsonify({"code": 1001, "message": "请输入 10-300 字符的疾病描述", "data": None}), 400

    messages = [
        {"role": "system", "content": _KEYWORD_SYSTEM_PROMPT},
        {"role": "user", "content": f"疾病/病理/研究方向描述：{description}"},
    ]

    try:
        data = chat_json(messages, Config.KEYWORD_TIMEOUT, "keyword-generate")
    except DeepSeekError as e:
        logger.warning("[keyword] 生成失败: %s", e)
        return jsonify({"code": 2001, "message": "关键词生成失败，请稍后重试", "data": None}), 200

    keywords = data.get("keywords")
    valid = (
        isinstance(keywords, list)
        and len(keywords) == Config.KEYWORD_COUNT
        and all(isinstance(k, str) and k.strip() for k in keywords)
    )
    if not valid:
        log_content_warning("keyword-generate", f"keywords 数量或格式不符: {keywords}")
        return jsonify({"code": 2001, "message": "关键词生成失败，请稍后重试", "data": None}), 200

    return jsonify(
        {
            "code": 0,
            "message": "ok",
            "data": {"keywords": [k.strip() for k in keywords]},
        }
    )