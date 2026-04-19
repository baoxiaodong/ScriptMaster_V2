import logging
import threading

logger = logging.getLogger("ScriptMaster.TaskManager")


class TaskManager:
    """全局大模型任务管控中心（FastAPI 异步安全版）"""
    _stop_flags = {}
    _lock = threading.Lock()

    @classmethod
    def start_task(cls, task_id: str):
        """在前端发起生成请求时调用，初始化任务状态"""
        with cls._lock:
            cls._stop_flags[task_id] = False
        logger.info(f"▶️ [TaskManager] 任务 {task_id} 开启新生成。")

    @classmethod
    def request_stop(cls, task_id: str):
        """在前端点击‘紧急停止’时调用，下发阻断指令"""
        with cls._lock:
            if task_id in cls._stop_flags:
                cls._stop_flags[task_id] = True
                logger.warning(f"🛑 [TaskManager] 任务 {task_id} 收到强行中断指令！")
            else:
                logger.warning(f"⚠️ [TaskManager] 试图停止不存在的任务 {task_id}")

    @classmethod
    def should_stop(cls, task_id: str) -> bool:
        """在大模型流式输出底层循环中持续检测"""
        with cls._lock:
            return cls._stop_flags.get(task_id, False)

    @classmethod
    def cleanup_task(cls, task_id: str):
        """任务完成后清理内存，保持系统轻量"""
        with cls._lock:
            if task_id in cls._stop_flags:
                del cls._stop_flags[task_id]
                logger.debug(f"🧹 [TaskManager] 任务 {task_id} 状态已清理。")
