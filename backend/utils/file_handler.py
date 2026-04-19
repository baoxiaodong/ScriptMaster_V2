""" 文件处理模块 - 后端纯净版 """
import io
import re
import logging
from typing import Dict
import pandas as pd

logger = logging.getLogger("ScriptMaster.FileHandler")


class FileHandler:
    """文件处理器：负责 Excel/CSV 的读取、解析与导出"""

    @staticmethod
    def read_file(file_content: io.BytesIO, filename: str) -> pd.DataFrame:
        """读取上传的文件二进制流，自动识别表头"""
        try:
            if filename.endswith('.csv'):
                try:
                    df = pd.read_csv(file_content, encoding='utf-8-sig', header=None)
                except Exception:
                    file_content.seek(0)
                    df = pd.read_csv(file_content, encoding='gbk', header=None)
            else:
                df = pd.read_excel(file_content, header=None)

            df = df.dropna(how='all').reset_index(drop=True)
            if df.empty: return pd.DataFrame()

            # 🚀 智能表头识别逻辑 (保持原有的优秀算法)
            if len(df) > 0:
                first_row = df.iloc[0].astype(str).tolist()
                col1 = first_row[0].strip() if len(first_row) > 0 else ""
                pure_header_keywords = ['标题', '章节', 'chapter', 'title', 'content', '正文', '内容']

                is_header = any(kw in col1.lower() for kw in pure_header_keywords)
                if is_header:
                    df = df.iloc[1:].reset_index(drop=True)

            df = df.iloc[:, :2].copy()
            df = df.fillna("")
            return df
        except Exception as e:
            logger.error(f"解析文件出错: {e}")
            return pd.DataFrame()

    @staticmethod
    def export_to_excel(results: Dict[str, pd.DataFrame]) -> bytes:
        """将结果字典导出为多 Sheet 的 Excel 二进制流"""
        if not results: return b""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            def extract_sort_key(x):
                match = re.search(r'\d+', str(x))
                return int(match.group()) if match else 999

            for key in sorted(results.keys(), key=extract_sort_key):
                df = results[key]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    sheet_name = re.sub(r'[\[\]\:\*\?\/\\]', '_', str(key))[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        return output.getvalue()