import axios from 'axios';
import { apiUrl } from './base';

const API_BASE = apiUrl('/api');

// Mock数据
const mockData = {
  generate_outline: {
    progress: [
      { msg: '正在分析小说结构...', value: 10 },
      { msg: '提取关键情节和人物...', value: 30 },
      { msg: '构建分集大纲框架...', value: 50 },
      { msg: '优化大纲内容...', value: 70 },
      { msg: '生成最终大纲...', value: 90 },
    ],
    result: '第一集：第一章 相遇\n第二集：第二章 冲突\n第三集：第三章 解决'
  },
  generate_storyboard: {
    progress: [
      { msg: '正在分析大纲...', value: 10 },
      { msg: '提取场景和镜头...', value: 30 },
      { msg: '生成画面描述...', value: 50 },
      { msg: '添加台词和音效...', value: 70 },
      { msg: '优化分镜内容...', value: 90 },
    ],
    result: {
      '第一集': '镜号,场景,画面内容 (Visual),台词 (Dialogue) & 音效 (SFX)\n1,办公室,男主角坐在办公桌前，眉头紧锁,男主角："这个项目必须在月底完成！"\n2,会议室,团队成员围坐在一起，讨论项目进展,女主角："我们需要更多的资源支持。"\n3,咖啡厅,男主角和女主角在咖啡厅见面,男主角："谢谢你的帮助，我真的很感激。"'
    }
  }
};

export const engine = {
  // 1. 验证配置
  async verifyConfig(config) {
    console.log('🔧 [API] 开始验证配置:', config);
    
    // Mock模式下直接返回成功
    if (config.provider === 'Mock (演示)') {
      console.log('✅ [API] Mock模式：配置验证成功');
      return { data: { status: 'success', message: 'Mock模式配置验证成功' } };
    }
    
    const formData = new FormData();
    Object.keys(config).forEach((key) => formData.append(key, config[key]));
    try {
      const response = await axios.post(`${API_BASE}/config/verify`, formData);
      console.log('✅ [API] 配置验证成功:', response.data);
      return response;
    } catch (error) {
      console.error('❌ [API] 配置验证失败:', error);
      throw error;
    }
  },

  // 2. 紧急停止 (物理拔线)
  async stopTask(taskId) {
    console.log('🛑 [API] 请求停止任务:', taskId);
    
    // Mock模式下直接返回成功
    if (this.isMockMode) {
      console.log('✅ [API] Mock模式：任务停止成功');
      return { data: { status: 'success', message: 'Mock模式任务停止成功' } };
    }
    
    const formData = new FormData();
    formData.append('task_id', taskId);
    try {
      const response = await axios.post(`${API_BASE}/stop_task`, formData);
      console.log('✅ [API] 任务停止成功:', response.data);
      return response;
    } catch (error) {
      console.error('❌ [API] 任务停止失败:', error);
      throw error;
    }
  },

  // 3. 流式读取接口 (关键！)
  async fetchStream(endpoint, payload, onChunk, onProgress, onDone, onError, config = {}) {
    // 检查是否为Mock模式
    const isMockMode = config.provider === 'Mock (演示)';
    this.isMockMode = isMockMode;
    
    if (isMockMode) {
      console.log('🚀 [API] Mock模式：开始模拟请求:', { endpoint, payload });
      
      // 模拟进度更新
      const mockProgress = mockData[endpoint]?.progress || [];
      for (const progress of mockProgress) {
        if (onProgress) {
          onProgress(progress.msg, progress.value);
        }
        // 模拟延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // 模拟完成
      if (onDone) {
        const mockResult = mockData[endpoint]?.result;
        onDone(mockResult);
      }
      
      console.log('🏁 [API] Mock模式：请求完成');
      return;
    }
    
    // 真实模式下向后端发送请求
    const fullUrl = `${API_BASE}/${endpoint}`;
    console.log('🚀 [API] 开始流式请求:', { url: fullUrl, payload });
    
    const formData = new FormData();
    Object.keys(payload).forEach((key) => formData.append(key, payload[key]));

    try {
      const response = await fetch(fullUrl, {
        method: 'POST',
        body: formData,
      });
      
      console.log('📡 [API] 收到响应，状态码:', response.status);
      
      if (!response.ok) {
        const errorMsg = `后端请求失败，状态码: ${response.status}`;
        console.error('❌ [API]', errorMsg);
        throw new Error(errorMsg);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let chunkCount = 0;
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          console.log('🏁 [API] 流传输完成');
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();

        for (const part of parts) {
          if (part.startsWith('data: ')) {
            const jsonStr = part.replace('data: ', '').trim();
            chunkCount++;
            
            console.log(`📦 [API] 收到第 ${chunkCount} 个数据块:`, jsonStr.substring(0, 200) + (jsonStr.length > 200 ? '...' : ''));

            if (jsonStr === '[DONE]') {
              console.log('✅ [API] 收到 DONE 信号');
              if (onDone) onDone();
              return;
            }

            try {
              const data = JSON.parse(jsonStr);
              console.log('🔍 [API] 解析数据:', data);

              if (data.type === 'chunk' && onChunk) {
                console.log('📝 [API] 处理文本块');
                onChunk(data.content);
              }
              if (data.type === 'progress' && onProgress) {
                console.log('📊 [API] 处理进度:', data.msg, data.value + '%');
                onProgress(data.msg, data.value);
              }
              if (data.type === 'error') {
                console.error('❌ [API] 收到错误:', data.content);
                throw new Error(data.content);
              }
              if (data.type === 'done' && onDone) {
                console.log('🎉 [API] 任务完成，结果:', data.results ? Object.keys(data.results) : '无结果');
                onDone(data.results);
                return;
              }
            } catch (jsonError) {
              console.warn('⚠️ [API] 忽略一段异常的流数据:', jsonStr);
            }
          }
        }
      }
    } catch (err) {
      console.error('💥 [API] 流式请求异常:', err);
      if (onError) onError(err.message);
    }
  },
};
