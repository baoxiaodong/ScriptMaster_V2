import axios from 'axios';
import { apiUrl } from './base';

const API_BASE = apiUrl('/api');
const getConfigSignature = (config = {}) => JSON.stringify({
  provider: config.provider || '',
  apiKey: config.apiKey || '',
  modelName: config.modelName || '',
  baseUrl: config.baseUrl || '',
});

export const engine = {
  lastVerifiedConfigSignature: '',
  // 1. 验证配置
  async verifyConfig(config) {
    console.log('🔧 [API] 开始验证配置:', config);
    
    const formData = new FormData();
    Object.keys(config).forEach((key) => formData.append(key, config[key]));
    try {
      const response = await axios.post(`${API_BASE}/config/verify`, formData);
      console.log('✅ [API] 配置验证成功:', response.data);
      if (response.data?.status === 'success') {
        this.lastVerifiedConfigSignature = getConfigSignature(config);
      }
      return response;
    } catch (error) {
      console.error('❌ [API] 配置验证失败:', error);
      throw error;
    }
  },

  // 2. 紧急停止 (物理拔线)
  async stopTask(taskId) {
    console.log('🛑 [API] 请求停止任务:', taskId);
    
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
    this.isMockMode = config.provider === 'Mock (演示)';

    const nextConfigSignature = getConfigSignature(config);
    if (config.provider && nextConfigSignature !== this.lastVerifiedConfigSignature) {
      try {
        await this.verifyConfig(config);
      } catch (err) {
        if (onError) onError(err.message || '配置同步失败');
        return;
      }
    }

    // 所有模式统一走后端，避免前端 Mock 与后端 Mock 双份数据源发生偏差
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

            let data;
            try {
              data = JSON.parse(jsonStr);
            } catch (jsonError) {
              console.warn('⚠️ [API] 忽略一段无法解析的流数据:', jsonStr);
              continue;
            }

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
          }
        }
      }
    } catch (err) {
      console.error('💥 [API] 流式请求异常:', err);
      if (onError) onError(err.message);
    }
  },
};
