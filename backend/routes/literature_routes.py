import logging

from flask import Blueprint, jsonify, request

from config import Config
from services.search_orchestrator import SearchOrchestrationError, search_literature

logger = logging.getLogger("medsearch.literature")

literature_bp = Blueprint("literature", __name__)


@literature_bp.post("/api/literature/search")
def search():
    payload = request.get_json(silent=True) or {}
    keywords = payload.get("keywords")
    page = payload.get("page", 1)

    if not isinstance(page, int) or page < 1:
        return jsonify({"code": 1002, "message": "页码参数不合法", "data": None}), 400

    valid = (
        isinstance(keywords, list)
        and 1 <= len(keywords) <= Config.MAX_KEYWORDS
        and all(isinstance(k, str) and k.strip() for k in keywords)
        and len({k.strip() for k in keywords}) == len(keywords)
    )
    if not valid:
        return jsonify({"code": 1002, "message": "请先生成或添加关键词", "data": None}), 400

    try:
        data = search_literature([k.strip() for k in keywords], page)
    except SearchOrchestrationError as e:
        logger.warning("[literature] 检索失败: %s", e)
        return jsonify({"code": 2002, "message": "检索失败，请稍后重试", "data": None}), 200

    return jsonify({"code": 0, "message": "ok", "data": data})