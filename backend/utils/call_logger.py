import logging
import threading
import time
from collections import defaultdict

logger = logging.getLogger("medsearch.call_logger")

_stats_lock = threading.Lock()
_stats = defaultdict(lambda: {"count": 0, "total_ms": 0, "success": 0, "failure": 0})


def log_call(service: str, operation: str, summary: str, elapsed_ms: int, status: str) -> None:
    """记录一次外部服务调用：目标服务、请求摘要、耗时、结果状态。"""
    logger.info(
        "[call] service=%s operation=%s status=%s elapsed_ms=%d summary=%s",
        service,
        operation,
        status,
        elapsed_ms,
        summary,
    )
    with _stats_lock:
        bucket = _stats[f"{operation}-{status}"]
        bucket["count"] += 1
        bucket["total_ms"] += elapsed_ms
        if status == "success":
            bucket["success"] += 1
        else:
            bucket["failure"] += 1


def log_content_warning(operation: str, reason: str) -> None:
    """AI 返回内容异常（空结果/超长/格式不符）时记录告警日志。"""
    logger.warning("[content-warning] operation=%s reason=%s", operation, reason)


def get_stats() -> list[dict]:
    """按 操作类型-结果状态-耗时 维度输出统计，用于核心流程成功率分析。"""
    with _stats_lock:
        result = []
        for key, bucket in _stats.items():
            operation, _, status = key.rpartition("-")
            avg_ms = bucket["total_ms"] / bucket["count"] if bucket["count"] else 0
            result.append(
                {
                    "operation": operation,
                    "status": status,
                    "count": bucket["count"],
                    "avg_ms": round(avg_ms, 1),
                    "success": bucket["success"],
                    "failure": bucket["failure"],
                }
            )
        return result


def reset_stats() -> None:
    with _stats_lock:
        _stats.clear()


class Timer:
    """耗时计时上下文，返回毫秒。"""

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args) -> None:
        self.elapsed_ms = int((time.perf_counter() - self._start) * 1000)