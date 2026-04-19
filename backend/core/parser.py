import csv
import io
import logging
import re
import pandas as pd

logger = logging.getLogger("ScriptMaster.Parser")


class ScriptParser:
    @staticmethod
    def parse_csv(csv_text: str, task_id: str = "unknown") -> pd.DataFrame:
        """
        解析大模型返回的文本为结构化 DataFrame
        已移除集数占位符，彻底解决 UI 渲染多出一行的 Bug
        """
        if not csv_text or not isinstance(csv_text, str):
            return pd.DataFrame()

        # 1. 基础清洗：移除 Markdown 标识符
        text = csv_text.replace('```', '').strip()

        # 💡 策略：为了防止 CSV 解析混乱，先统一处理全角逗号和竖线
        # 但要注意：Markdown 表格通常以 | 开头和结尾
        text = text.replace('，', ',')

        logger.info(f"🧹 [Task:{task_id}] 开始解析文本，总长度: {len(text)}")

        lines = text.split('\n')
        parsed_data = []
        rejected_count = 0

        # 2. 定位有效数据起始位置（寻找表头）
        csv_start_idx = 0
        for idx, line in enumerate(lines):
            # 兼容中英文表头
            if any(kw in line for kw in ["镜号", "Shot", "场景", "Scene"]):
                csv_start_idx = idx
                logger.debug(f"📍 [Task:{task_id}] 找到数据起始行：第 {idx} 行")
                break

        # 3. 逐行解析
        for idx in range(csv_start_idx, len(lines)):
            line = lines[idx].strip()
            if not line:
                continue

            # 🚀 核心修复：不再主动将“第X集”插入 parsed_data
            # 仅作为日志参考或直接跳过，防止 UI 渲染出多余的“集数卡片”
            if re.search(r'(?:第|Episode)\s*\d+\s*(?:集|Chapter)', line, re.IGNORECASE):
                logger.debug(f"ℹ️ [Task:{task_id}] 跳过集数声明行: {line}")
                continue

            # 跳过只有分隔符的行
            if re.match(r'^[-:,\s|]+$', line):
                continue

            # 尝试解析行内容
            parts = []
            # 优先处理 Markdown 格式的竖线分隔
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                # 移除 Markdown 表格首尾可能存在的空元素
                if parts and not parts[0]: parts.pop(0)
                if parts and not parts[-1]: parts.pop()
            else:
                # 使用标准 CSV 模块处理带引号的复杂内容
                row_io = io.StringIO(line)
                try:
                    reader = csv.reader(row_io)
                    parts = next(reader)
                except:
                    parts = [p.strip() for p in line.split(',')]

            if not parts:
                rejected_count += 1
                continue

            # 4. 识别有效镜头行
            first_col = str(parts[0]).strip()
            shot_num_match = re.search(r'\d+', first_col)
            non_empty_parts = [p for p in parts if p.strip()]

            # 只有当第一列含有数字（镜号），或者内容列数足够时才认为是有效镜头
            if shot_num_match or len(non_empty_parts) >= 3:
                clean_shot = shot_num_match.group(0) if shot_num_match else first_col

                # 强制规范为 4 列结构
                row_data = [""] * 4
                row_data[0] = clean_shot  # 镜号

                # 填充后续列 (场景、画面、台词)
                for i in range(1, min(len(parts), 4)):
                    row_data[i] = str(parts[i]).strip()

                # 如果内容超出了 4 列，尝试合并到最后一列（台词/音效）
                if len(parts) > 4:
                    row_data[3] = (row_data[3] + " " + " ".join(parts[4:])).strip()

                parsed_data.append(row_data)
            else:
                rejected_count += 1
                if rejected_count <= 5:
                    logger.warning(f"⚠️ [Task:{task_id}] 行 {idx} 被过滤 (无效格式): {line[:50]}...")

        # 5. 封装为 DataFrame
        if not parsed_data:
            logger.error(f"❌ [Task:{task_id}] 全文遍历结束，未提取到任何有效分镜数据！")
            return pd.DataFrame()

        final_cols = ['镜号', '场景', '画面内容 (Visual)', '台词 (Dialogue) & 音效 (SFX)']
        df = pd.DataFrame(parsed_data, columns=final_cols)

        # 6. 最后的清洗：确保台词只有英文（移除中文字符）
        if not df.empty:
            def clean_to_english(row):
                dialogue = str(row.get('台词 (Dialogue) & 音效 (SFX)', ''))
                if dialogue:
                    # 🚨 仅移除中文字符，保留标点和英文
                    clean_text = re.sub(r'[\u4e00-\u9fa5]+', '', dialogue).strip()
                    row['台词 (Dialogue) & 音效 (SFX)'] = re.sub(r'\s+', ' ', clean_text).strip()
                return row

            df = df.apply(clean_to_english, axis=1)

        logger.info(f"✅ [Task:{task_id}] 解析完成，成功提取 {len(df)} 个镜头")
        return df