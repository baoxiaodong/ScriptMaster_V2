import argparse
import asyncio
import io
import logging
import json
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import pandas as pd
import math
import concurrent.futures
import time
import threading
import re
from config.settings import setup_logger
from core.llm_service import LLMService
from core.task_manager import TaskManager
from core.processor import NovelModeProcessor
from utils.file_handler import FileHandler
from utils.error_handler import error_handler
from core.prompt_manager import PromptManager, PromptKeys
from core.parser import ScriptParser
from core.prompts import PromptTemplates
logger = setup_logger("ScriptMaster.Main")
app = FastAPI(title="ScriptMaster V2.0 Engine")

# 配置 CORS 中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()

# =============================================================================
# 基础接口
# =============================================================================

@app.get("/")
async def root():
    """根路径 - 检查后端服务是否正常运行"""
    return {"message": "ScriptMaster 后端正在运行"}

@app.post("/api/config/verify")
def verify_config(
        provider: str = Form(...), api_key: str = Form(...),
        model_name: str = Form(...), base_url: str = Form("")
):
    """验证 API 配置
    参数:
        provider: 模型提供商 (OpenAI/Anthropic等)
        api_key: API 密钥
        model_name: 模型名称
        base_url: 自定义 API 地址 (可选)
    返回:
        验证成功或失败的状态信息
    """
    # 日志中不显示明文API密钥
    logger.info(f"🔧 [POST] /api/config/verify - provider: {provider}, model: {model_name}, base_url: {base_url}")
    try:
        llm_service.configure(provider, api_key, model_name, base_url)
        test_res = llm_service.generate("Hi", "Say OK")
        if "❌" in test_res:
            logger.warning(f"❌ [配置验证] 失败: {test_res}")
            return {"status": "error", "message": test_res}
        logger.info("✅ [配置验证] 成功")
        return {"status": "success", "message": "API 配置验证通过！"}
    except Exception as e:
        logger.error(f"💥 [配置验证] 异常: {e}")
        return error_handler.parse_exception(e, "配置验证")

@app.post("/api/stop_task")
def stop_task(task_id: str = Form(...)):
    """停止正在运行的任务
    参数:
        task_id: 任务唯一标识
    返回:
        停止成功的状态信息
    """
    logger.info(f"🛑 [POST] /api/stop_task - task_id: {task_id}")
    TaskManager.request_stop(task_id)
    logger.info(f"✅ [停止任务] 已请求停止任务: {task_id}")
    return {"status": "success"}

# =============================================================================
# 小说模式接口
# =============================================================================

@app.post("/api/upload_novel")
async def upload_novel(file: UploadFile = File(...)):
    """上传小说源文件 (Excel/CSV 格式)
    参数:
        file: 上传的文件对象
    返回:
        文件名、列名、预览数据 (前10行)、完整数据的 JSON
    """
    logger.info(f"📁 [POST] /api/upload_novel - 文件: {file.filename}")
    try:
        logger.info(f"📄 [文件上传] 开始处理文件: {file.filename}")
        content = await file.read()
        df = FileHandler.read_file(io.BytesIO(content), file.filename)
        if df.empty:
            logger.warning(f"❌ [文件上传] 文件内容为空: {file.filename}")
            raise HTTPException(status_code=400, detail="文件内容为空或格式不支持")
        logger.info(f"✅ [文件上传] 成功，行数: {len(df)}, 列数: {len(df.columns)}")
        return {
            "status": "success", "filename": file.filename, "columns": df.columns.tolist(),
            "preview": df.head(10).values.tolist(), "full_data_json": df.to_json(orient='split'),
            "total_rows": len(df)
        }
    except Exception as e:
        logger.error(f"💥 [文件上传] 异常: {e}")
        return error_handler.parse_exception(e, "文件上传")

@app.post("/api/generate_outline")
def generate_outline(
        task_id: str = Form(...), novel_data_json: str = Form(...), total_episodes: int = Form(20)
):
    """小说模式：根据上传的小说数据生成分集大纲
    参数:
        task_id: 任务唯一标识
        novel_data_json: 上传的小说数据 JSON (split 格式)
        total_episodes: 总集数 (默认20集)
    返回:
        SSE 流式响应，包含大纲文本、进度信息
    """
    logger.info(f"📝 [POST] /api/generate_outline - task_id: {task_id}, 总集数: {total_episodes}")
    TaskManager.start_task(task_id)

    try:
        df = pd.read_json(io.StringIO(novel_data_json), orient='split')
        logger.info(f"📊 [生成大纲] 数据加载成功，行数: {len(df)}")
        processor = NovelModeProcessor(llm_service, total_episodes=total_episodes)

        def event_generator():
            try:
                logger.info(f"🚀 [生成大纲] 开始生成...")
                yield f"data: {json.dumps({'type': 'status', 'content': '开始分析原著...'}, ensure_ascii=False)}\n\n"
                
                for chunk in processor.generate_outline_stream(df, task_id=task_id):
                    if TaskManager.should_stop(task_id):
                        logger.info(f"⏹️ [生成大纲] 任务被手动停止")
                        yield f"data: {json.dumps({'type': 'error', 'content': '任务已被手动停止'}, ensure_ascii=False)}\n\n"
                        break
                    
                    if chunk.startswith("【系统提示】"):
                        msg = chunk.replace("【系统提示】", "")
                        yield f"data: {json.dumps({'type': 'progress', 'msg': msg, 'value': 40}, ensure_ascii=False)}\n\n"
                        continue

                    safe_chunk_json = json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)
                    yield f"data: {safe_chunk_json}\n\n"

                logger.info(f"✅ [生成大纲] 完成")
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            except Exception as e:
                logger.error(f"💥 [生成大纲] 异常: {e}")
                yield f"data: {json.dumps({'type': 'error', 'content': f'生成大纲失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            finally:
                TaskManager.cleanup_task(task_id)

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"💥 [生成大纲] 初始化异常: {e}")
        TaskManager.cleanup_task(task_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_storyboard")
def generate_storyboard(
        task_id: str = Form(...), outline_text: str = Form(...), total_episodes: int = Form(20), episodes_per_batch: int = Form(3)
):
    """小说模式：根据大纲生成剧本分镜
    参数:
        task_id: 任务唯一标识
        outline_text: 分集大纲文本
        total_episodes: 总集数 (默认20集)
        episodes_per_batch: 每批处理的集数 (默认3集)
    返回:
        SSE 流式响应，包含分镜 CSV 数据
    """
    logger.info(f"🎬 [POST] /api/generate_storyboard - task_id: {task_id}, 总集数: {total_episodes}, 每批: {episodes_per_batch}")
    TaskManager.start_task(task_id)
    processor = NovelModeProcessor(llm_service, total_episodes=total_episodes)

    def storyboard_generator():
        try:
            logger.info(f"🚀 [生成小说分镜] 开始...")
            yield f"data: {json.dumps({'type': 'progress', 'msg': '分镜引擎正在初始化...', 'value': 0}, ensure_ascii=False)}\n\n"
            
            # 使用队列来传递进度信息
            from queue import Queue
            progress_queue = Queue()
            
            def on_progress(msg, value):
                print(f"进度: {msg} {value}%")
                progress_queue.put((msg, value))
            
            # 启动分镜生成线程
            import threading
            results = {}
            error = None
            
            def generate_storyboard():
                nonlocal results, error
                try:
                    results = processor.process(
                        task_id=task_id, full_text=outline_text,
                        on_progress=on_progress
                    )
                except Exception as e:
                    nonlocal error
                    error = e
            
            thread = threading.Thread(target=generate_storyboard)
            thread.start()
            
            # 实时处理进度信息
            while thread.is_alive() or not progress_queue.empty():
                try:
                    msg, value = progress_queue.get(block=False)
                    yield f"data: {json.dumps({'type': 'progress', 'msg': msg, 'value': value}, ensure_ascii=False)}\n\n"
                except:
                    import time
                    time.sleep(0.1)  # 避免忙等
            
            # 检查是否有错误
            if error:
                raise error
            
            final_data = {}
            for ep, df in results.items():
                final_data[ep] = df.to_csv(index=False) if isinstance(df, pd.DataFrame) else str(df)
            
            logger.info(f"✅ [生成小说分镜] 完成，集数: {len(final_data)}")
            yield f"data: {json.dumps({'type': 'done', 'results': final_data})}\n\n"
        except Exception as e:
            logger.error(f"💥 [生成小说分镜] 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        finally:
            TaskManager.cleanup_task(task_id)

    return StreamingResponse(storyboard_generator(), media_type="text/event-stream")

# =============================================================================
# 剧本衍生模式接口
# =============================================================================

@app.get("/api/script/default_creative")
def get_default_creative():
    """获取后台预设的默认创意 (供用户参考)"""
    logger.info("📄 [GET] /api/script/default_creative")
    return {"creative": "【默认创意：低画质人生】\n2099年，人类视觉成为订阅服务。穷人只能忍受144p的低画质滤镜。主角凯意外获得高清芯片后，发现了被政府滤镜掩盖的恐怖真相..."}

@app.post("/api/script/generate_acts")
def script_generate_acts(task_id: str = Form(...), idea: str = Form(...)):
    """剧本模式：根据创意生成三幕式结构 (3选1)
    参数:
        task_id: 任务唯一标识
        idea: 用户输入的创意/点子
    返回:
        SSE 流式响应，包含3个版本的三幕式结构
    """
    logger.info(f"🎭 [POST] /api/script/generate_acts - task_id: {task_id}, 创意长度: {len(idea)}")
    TaskManager.start_task(task_id)
    def event_generator():
        try:
            logger.info(f"🚀 [生成三幕式] 开始...")
            system_p = PromptManager.get(PromptKeys.ACT_GEN_SYSTEM)
            task_p = PromptManager.get(PromptKeys.ACT_GEN_TASK).format(original_idea=idea)
            
            for chunk in llm_service.generate_stream(system_p, task_p, task_id=task_id):
                if TaskManager.should_stop(task_id):
                    logger.info(f"⏹️ [生成三幕式] 任务被手动阻断")
                    yield f"data: {json.dumps({'type': 'error', 'content': '任务已被手动阻断'}, ensure_ascii=False)}\n\n"
                    break
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            logger.info(f"✅ [生成三幕式] 完成")
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"💥 [生成三幕式] 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'生成失败: {str(e)}'}, ensure_ascii=False)}\n\n"
        finally:
            TaskManager.cleanup_task(task_id)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/script/generate_outline")
def script_generate_outline(task_id: str = Form(...), act_structure: str = Form(...), total_episodes: int = Form(...)):
    """剧本模式：根据三幕式结构生成动态集数大纲
    参数:
        task_id: 任务唯一标识
        act_structure: 用户选择的三幕式结构文本
        total_episodes: 总集数
    返回:
        SSE 流式响应，包含分集大纲文本
    """
    logger.info(f"📋 [POST] /api/script/generate_outline - task_id: {task_id}, 总集数: {total_episodes}, 结构长度: {len(act_structure)}")
    TaskManager.start_task(task_id)
    def event_generator():
        try:
            logger.info(f"🚀 [生成剧本大纲] 开始...")
            system_p = PromptManager.get(PromptKeys.OUTLINE_SYSTEM)
            task_p = PromptManager.get(PromptKeys.OUTLINE_TASK).format(total_episodes=total_episodes, user_choice=act_structure)
            
            for chunk in llm_service.generate_stream(system_p, task_p, task_id=task_id):
                if TaskManager.should_stop(task_id):
                    logger.info(f"⏹️ [生成剧本大纲] 任务被手动阻断")
                    yield f"data: {json.dumps({'type': 'error', 'content': '任务已被手动阻断'}, ensure_ascii=False)}\n\n"
                    break
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
            
            logger.info(f"✅ [生成剧本大纲] 完成")
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"💥 [生成剧本大纲] 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'大纲生成失败: {str(e)}'}, ensure_ascii=False)}\n\n"
        finally:
            TaskManager.cleanup_task(task_id)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/script/generate_storyboard")
def script_generate_storyboard(task_id: str = Form(...), outline_text: str = Form(...), total_episodes: int = Form(...)):
    """剧本模式：根据大纲生成剧本分镜 (单批次 + 智能切集算法)
    参数:
        task_id: 任务唯一标识
        outline_text: 分集大纲文本
        total_episodes: 总集数
    返回:
        SSE 流式响应，包含分镜 CSV 数据
    特点:
        - 一次性生成所有集数的分镜
        - 使用智能切集算法：根据镜号重置判断集数边界
    """
    logger.info(f"🎬 [POST] /api/script/generate_storyboard - task_id: {task_id}, 总集数: {total_episodes}, 大纲长度: {len(outline_text)}")
    TaskManager.start_task(task_id)
    def storyboard_generator():
        try:
            logger.info(f"🚀 [生成剧本分镜] 开始...")
            yield f"data: {json.dumps({'type': 'progress', 'msg': 'AI 正在全速渲染分镜矩阵...', 'value': 40}, ensure_ascii=False)}\n\n"
            
            system_p = PromptManager.get(PromptKeys.SCRIPT_SYSTEM)
            task_p = PromptManager.get(PromptKeys.SCRIPT_TASK_TEMPLATE).format(
                episode_range=f"1-{total_episodes}", 
                outline=outline_text, 
                total_episodes=total_episodes
            )
            
            raw_text = ""
            for chunk in llm_service.generate_stream(system_p, task_p, task_id=task_id):
                if TaskManager.should_stop(task_id):
                    logger.info(f"⏹️ [生成剧本分镜] 任务被手动阻断")
                    raise Exception("任务已被手动阻断")
                raw_text += chunk
            
            logger.info(f"📊 [生成剧本分镜] 开始解析，原始文本长度: {len(raw_text)}")
            parser = ScriptParser()
            df = parser.parse_csv(raw_text, task_id)
            
            final_data = {}
            if not df.empty:
                logger.info(f"📊 [生成剧本分镜] 解析成功，行数: {len(df)}")
                current_ep = "第1集"
                ep_num = 1
                temp_rows = []
                prev_shot = 0
                
                for _, row in df.iterrows():
                    val = str(row.get('镜号', '')).strip()
                    shot_match = re.search(r'\d+', val)
                    if shot_match:
                        shot_num = int(shot_match.group(0))
                        if shot_num <= 3 and temp_rows and shot_num < prev_shot:
                            final_data[current_ep] = pd.DataFrame(temp_rows, columns=df.columns).to_csv(index=False)
                            ep_num += 1
                            current_ep = f"第{ep_num}集"
                            temp_rows = []
                        prev_shot = shot_num
                    temp_rows.append(row.tolist())
                    
                if temp_rows:
                    final_data[current_ep] = pd.DataFrame(temp_rows, columns=df.columns).to_csv(index=False)
                
                logger.info(f"✅ [生成剧本分镜] 切集完成，集数: {len(final_data)}")
            
            yield f"data: {json.dumps({'type': 'done', 'results': final_data}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"💥 [生成剧本分镜] 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            TaskManager.cleanup_task(task_id)
            
    return StreamingResponse(storyboard_generator(), media_type="text/event-stream")
# =============================================================================
# 提示词工坊接口 (Prompt Studio)
# =============================================================================


@app.get("/api/script/prompts/{key}")
def get_prompt_detail(key: str):
    """获取指定模块的官方与用户自定义提示词"""
    logger.info(f"📝 [GET] /api/script/prompts/{key}")
    try:
        if key not in PromptKeys.__members__:
            logger.warning(f"⚠️ [PromptStudio] 未知资产 key: {key}")
            return {
                "status": "error",
                "message": "未找到对应的提示词资产",
                "official_prompt": "",
                "user_prompt": ""
            }

        official = getattr(PromptTemplates, key, "")
        current = PromptManager.get(key)
        return {
            "status": "success",
            "official_prompt": official,
            "user_prompt": current
        }
    except Exception as e:
        logger.error(f"🚨 [获取提示词] 异常: {e}")
        return {
            "status": "error",
            "message": "资产加载失败，请检查提示词配置",
            "official_prompt": "",
            "user_prompt": ""
        }

@app.post("/api/script/prompts/update")
def update_prompt(key: str = Form(...), content: str = Form(...)):
    """热更新提示词并记录操作日志"""
    logger.info(f"🚀 [POST] /api/script/prompts/update - 更新模块: {key}")
    try:
        PromptManager.update(key, content)
        return {"status": "success", "message": f"模块 {key} 已热部署"}
    except Exception as e:
        logger.error(f"💥 [更新提示词] 异常: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/script/prompts/reset/{key}")
def reset_prompt(key: str):
    """还原指定模块至系统出厂设定"""
    logger.info(f"🔄 [POST] /api/script/prompts/reset/{key} - 还原模块")
    try:
        PromptManager.reset(key)
        return {"status": "success", "message": "已还原官方配置"}
    except Exception as e:
        logger.error(f"💥 [还原提示词] 异常: {e}")
        return {"status": "error", "message": str(e)}
# =============================================================================
# 提示词工坊 A/B 测试流式接口
# =============================================================================

@app.post("/api/script/prompts/test_stream")
async def test_prompt_stream(
    system_prompt: str = Form(...),
    user_prompt: str = Form(...),
    task_id: str = Form(...)
):
    """
    实验室 A/B 测试专用流式接口。
    支持前端双轨并发调用，严格接入 TaskManager 熔断机制。
    """
    logger.info(f"🧪 [提示词演练] 启动任务: {task_id}")
    TaskManager.start_task(task_id)

    async def event_stream():
        try:
            # 使用 LLMService 的流式生成能力
            # 这里的 generate_stream 需要确保你的 llm_service.py 中已实现逻辑
            for chunk in llm_service.generate_stream(system_prompt, user_prompt, task_id=task_id):
                
                # 🚨 核心熔断检查：每一块数据输出前都检测前端是否发出了停止指令
                if TaskManager.should_stop(task_id):
                    logger.warning(f"🛑 [提示词演练] 任务 {task_id} 已被物理熔断")
                    yield f"data: {json.dumps({'type': 'chunk', 'content': ' ⛔ [引擎已被物理熔断]'}, ensure_ascii=False)}\n\n"
                    break
                
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            logger.error(f"💥 [提示词演练] 异常: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            yield "data: [DONE]\n\n"
            TaskManager.cleanup_task(task_id)
            logger.info(f"🏁 [提示词演练] 任务 {task_id} 资源已释放")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
# =============================================================================
# 启动服务
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ScriptMaster backend server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, reload=False)
