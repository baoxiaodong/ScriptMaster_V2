"""
小说模式处理器 - 业务逻辑大脑 (FastAPI 纯净版)
"""
import concurrent.futures
import logging
import re
import time
import math
from threading import Lock
from typing import Callable, Dict, Optional, Generator

import pandas as pd

from core.llm_service import LLMService
from core.parser import ScriptParser
from core.prompt_manager import PromptManager, PromptKeys
from core.task_manager import TaskManager

logger = logging.getLogger("ScriptMaster.Processor")

class NovelModeProcessor:
    def __init__(self, llm_service: LLMService, total_episodes: int = 20):
        self.llm_service = llm_service
        self.results_lock = Lock()
        self.parser = ScriptParser()
        self.total_episodes = total_episodes
        self.system_prompt = PromptManager.get(PromptKeys.SCRIPT_SYSTEM)
        self.user_template = PromptManager.get(PromptKeys.BATCH_SCRIPT_PROMPT)

    def _combine_chapters(self, df: pd.DataFrame) -> str:
        contents = []
        for row in df.itertuples(index=False):
            title = str(row[0]) if pd.notna(row[0]) else ""
            content = str(row[1]) if pd.notna(row[1]) else ""
            if content.strip():
                label = title if title else f"章节{len(contents) + 1}"
                contents.append(f"【{label}】\n{content}")
        return "\n\n".join(contents)

    def generate_outline_stream(self, df: pd.DataFrame, task_id: str) -> Generator[str, None, None]:
        """流式生成小说大纲"""
        full_text = self._combine_chapters(df)
        text_length = len(full_text)
        logger.info(f"📝 [Task:{task_id}] 文本总长度: {text_length}")

        try:
            MAX_CHUNK_SIZE = 30000
            if text_length <= MAX_CHUNK_SIZE:
                yield from self._generate_outline_from_text_stream(full_text, task_id)
            else:
                yield from self._generate_outline_from_long_text_stream(full_text, text_length, task_id)
        except Exception as e:
            logger.error(f"❌ [Task:{task_id}] 大纲生成异常: {str(e)}", exc_info=True)
            yield f"❌ 大纲生成失败: {str(e)}"

    def _generate_outline_from_text_stream(self, text: str, task_id: str) -> Generator[str, None, None]:
        """单次调用流式生成大纲"""
        prompt = PromptManager.get(PromptKeys.OUTLINE_TASK).format(
            total_episodes=self.total_episodes,
            user_choice=text
        )

        for chunk in self.llm_service.generate_stream(
                PromptManager.get(PromptKeys.OUTLINE_SYSTEM),
                prompt,
                task_id=task_id
        ):
            if TaskManager.should_stop(task_id):
                yield f"❌ 任务已被手动停止"
                return
            yield chunk

    def _generate_outline_from_long_text_stream(self, full_text: str, original_length: int,
                                         task_id: str) -> Generator[str, None, None]:
        """超长文本摘要合并 - 流式输出 (带前端播报)"""
        MAX_CHUNK_SIZE = 30000
        chunks = [full_text[i:i + MAX_CHUNK_SIZE] for i in range(0, len(full_text), MAX_CHUNK_SIZE)]
        total_chunks = len(chunks)

        summaries = [None] * total_chunks
        progress_lock = Lock()
        completed = 0

        # 🚀 给前端发送第一条安抚广播！
        yield f"【系统提示】原著达 {original_length} 字，正在启动 AI 剧情提炼 (共{total_chunks}部分)，请耐心等待..."

        def _summarize_chunk(idx, chunk):
            if TaskManager.should_stop(task_id):
                return idx, f"STOP_SIGNAL:{task_id}"

            summary_prompt = f"请简要总结以下小说内容的主要情节（500字以内）：\n\n{chunk}"
            summary = ""
            for chunk_str in self.llm_service.generate_stream(
                    "你是一个专业的小说编辑。",
                    summary_prompt,
                    task_id=task_id
            ):
                if TaskManager.should_stop(task_id):
                    return idx, f"STOP_SIGNAL:{task_id}"
                summary += chunk_str
            return idx, f"【段落{idx + 1}】\n{summary}"

        # 🚀 降低并发到 2，保护代理网关不被挤爆！
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_idx = {executor.submit(_summarize_chunk, idx, chunk): idx
                             for idx, chunk in enumerate(chunks)}

            for future in concurrent.futures.as_completed(future_to_idx):
                idx, summary = future.result()
                if "STOP_SIGNAL" in str(summary):
                    yield f"❌ 任务已被手动停止"
                    return

                summaries[idx] = summary
                with progress_lock:
                    completed += 1
                    logger.info(f"📝 正在分析大纲进度 {completed}/{total_chunks}...")
                    # 🚀 每完成一块，给前端发送一条进度广播！
                    yield f"【系统提示】剧情提炼进度: {completed}/{total_chunks} 部分已压缩完毕..."

        combined_summaries = "\n\n".join(summaries)
        yield f"【系统提示】全书提炼完成！正在生成最终分集大纲...\n\n"
        yield from self._generate_outline_from_text_stream(combined_summaries, task_id)

    def _split_batches(self, df: pd.DataFrame, start_ep: int, end_ep: int) -> Dict[str, pd.DataFrame]:
        results = {}
        if df.empty: return {f"第{i}集": pd.DataFrame() for i in range(start_ep, end_ep + 1)}

        current_ep = None
        ep_num = start_ep - 1
        temp_rows = []
        prev_shot = 0

        for _, row in df.iterrows():
            val = str(row.get('镜号', '')).strip()
            ep_match = re.search(r'第\s*(\d+)\s*集', val)
            if ep_match:
                if current_ep and temp_rows:
                    results[current_ep] = pd.DataFrame(temp_rows, columns=df.columns)
                ep_num = int(ep_match.group(1))
                current_ep = val
                temp_rows = []
                prev_shot = 0
                continue

            shot_match = re.search(r'\d+', val)
            if not shot_match: continue
            shot_num = int(shot_match.group(0))

            if shot_num <= 3 and temp_rows and shot_num < prev_shot:
                results[current_ep] = pd.DataFrame(temp_rows, columns=df.columns)
                ep_num += 1
                current_ep = f"第{ep_num}集"
                temp_rows = []
                prev_shot = 0

            if not current_ep:
                current_ep = f"第{ep_num + 1}集"
                ep_num += 1

            temp_rows.append(row.tolist())
            prev_shot = shot_num

        if current_ep and temp_rows:
            results[current_ep] = pd.DataFrame(temp_rows, columns=df.columns)

        for i in range(start_ep, end_ep + 1):
            key = f"第{i}集"
            if key not in results:
                results[key] = pd.DataFrame(columns=df.columns)

        return results

    def process(self, task_id: str, df: pd.DataFrame = None, on_progress: Optional[Callable] = None,
                existing_results: Optional[Dict[str, pd.DataFrame]] = None,
                full_text: str = None) -> Dict[str, pd.DataFrame]:
        import math
        if full_text is None: full_text = self._combine_chapters(df)

        final_results = {}
        TOTAL_EPISODES = self.total_episodes
        EPISODES_PER_BATCH = 3
        total_batches_count = math.ceil(TOTAL_EPISODES / EPISODES_PER_BATCH)

        batches = []
        for i in range(total_batches_count):
            s = i * EPISODES_PER_BATCH + 1
            e = min(s + EPISODES_PER_BATCH - 1, TOTAL_EPISODES)
            batches.append((s, e))

        completed = 0
        total_batches = len(batches)

        def _worker(start, end):
            logger.info(f"\n▶️ [线程启动] 正在接单：开始处理第 {start}-{end} 集的内容...")
            time.sleep((start // EPISODES_PER_BATCH) * 0.5)

            prompt = self.user_template.format(
                start_ep=start, end_ep=end, content=full_text, total_episodes=TOTAL_EPISODES
            )

            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    raw_text = ""
                    for chunk in self.llm_service.generate_stream(self.system_prompt, prompt, task_id=task_id):
                        if TaskManager.should_stop(task_id):
                            raise Exception("手动中止")
                        raw_text += chunk

                    logger.info(f"🔍 [批次{start}-{end}] AI原始返回前200字符:\n{raw_text[:200]}")
                    if raw_text.startswith("❌"): raise Exception(raw_text)

                    batch_df = self.parser.parse_csv(raw_text)
                    if batch_df.empty: raise Exception("解析失败：触发自动重试！")
                    return self._split_batches(batch_df, start, end)
                except Exception as e:
                    if "手动中止" in str(e):
                        return {f"第{i}集": "❌ 已被您紧急叫停，未扣除额度" for i in range(start, end + 1)}
                    if attempt < max_retries:
                        time.sleep((attempt + 1) * 3)
                        continue
                    return {f"第{i}集": f"❌ Error: {str(e)}" for i in range(start, end + 1)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {executor.submit(_worker, s, e): (s, e) for s, e in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                s, e = future_to_batch[future]
                try:
                    res = future.result()
                    with self.results_lock:
                        final_results.update(res)
                    completed += 1
                    completed_episodes = min(completed * EPISODES_PER_BATCH, TOTAL_EPISODES)
                    if on_progress:
                        on_progress(f"已完成 {completed_episodes}/{TOTAL_EPISODES} 集",
                                    int(completed / total_batches * 100))
                except Exception as e:
                    with self.results_lock:
                        for i in range(s, e + 1):
                            final_results[f"第{i}集"] = f"❌ Fatal: {str(e)}"

        if existing_results:
            existing_results.update(final_results)
            return existing_results
        return final_results