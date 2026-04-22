<template>
  <div class="app-wrapper" :class="isDarkMode ? 'dark-theme' : 'light-theme'">
    <el-container class="main-container">
      <el-aside :width="sidebarCollapsed ? '80px' : '280px'" class="premium-sidebar">
        <div class="sidebar-header">
          <div class="logo-box" v-if="!sidebarCollapsed">S</div>
          <h2 v-if="!sidebarCollapsed">引擎控制台</h2>
          <div style="margin-left: auto; display: flex; align-items: center; gap: 12px">
            <el-switch
              v-model="isDarkMode"
              inline-prompt
              active-icon="Moon"
              inactive-icon="Sunny"
              style="--el-switch-on-color: #374151; --el-switch-off-color: #e3700d"
              v-if="!sidebarCollapsed"
            />
            <el-button
              type="text"
              :icon="sidebarCollapsed ? ArrowRight : ArrowLeft"
              @click="sidebarCollapsed = !sidebarCollapsed"
              class="sidebar-toggle-btn"
              :title="sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'"
            />
          </div>
        </div>

        <el-form label-position="top" class="premium-form" v-if="!sidebarCollapsed">
          <el-form-item label="🧠 核心驱动 (Provider)">
            <el-select v-model="config.provider">
              <el-option label="Mock (演示测试)" value="Mock (演示)" />
              <el-option label="Google Gemini" value="Google Gemini" />
              <el-option label="自定义三方Gemini" value="自定义三方Gemini" />
              <el-option label="OpenAI (GPT)" value="OpenAI (GPT)" />
              <el-option label="阿里云通义千问" value="阿里云通义千问" />
            </el-select>
            <el-alert
              v-if="config.provider === 'Mock (演示)'"
              title="当前为 Mock 演示模式，将调用本地后端的演示数据流程，不消耗真实模型额度，仅供功能演示与界面测试使用"
              type="warning"
              show-icon
              :closable="false"
              style="margin-top: 10px; line-height: 1.4; border-radius: 8px"
            />
          </el-form-item>

          <el-form-item label="🤖 模型代号 (Model)">
            <el-select
              v-model="config.modelName"
              filterable
              allow-create
              default-first-option
              placeholder="请选择或手动输入模型代号"
              style="width: 100%"
            >
              <el-option v-for="model in currentModelOptions" :key="model" :label="model" :value="model" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <template #label>
              <div class="flex-label">
                <span>🔑 访问秘钥 (API Key)</span>
                <el-checkbox v-model="rememberConfig" size="small" class="remember-chk">记住配置</el-checkbox>
              </div>
            </template>
            <el-input v-model="config.apiKey" type="password" show-password placeholder="输入你的专属 Key" />
          </el-form-item>

          <el-form-item label="🌐 神经网关 (Base URL)">
            <el-input v-model="config.baseUrl" placeholder="默认官方地址，代理必填" />
          </el-form-item>

          <el-button class="btn-ignite" @click="saveConfig" :loading="isSaving">
            <span v-if="!isSaving">⚡ 连通大模型引擎</span>
            <span v-else>正在建立连接...</span>
          </el-button>

          <!-- 使用说明部分 -->
          <div class="usage-guide">
            <el-collapse v-model="activeUsagePanel">
              <el-collapse-item title="📖 使用说明" name="1">
                <div class="guide-content">
                  <h4>文件格式要求：</h4>
                  <ul>
                    <li>上传Excel时，请确保包含章节标题和内容列</li>
                    <li>第1列: 章节标题</li>
                    <li>第2列: 章节内容</li>
                  </ul>
                  <h4>生成标准：</h4>
                  <ul>
                    <li>每集默认 ≥20 个镜头</li>
                    <li>画面描述: 中文</li>
                    <li>台词 & 音效: 英文</li>
                  </ul>
                </div>
              </el-collapse-item>
            </el-collapse>

            <!-- 打开说明书按钮 -->
            <el-button 
              type="primary" 
              plain 
              class="open-manual-btn"
              @click="openLocalManual"
              style="margin-top: 16px; width: 100%"
            >
              📄 打开本地使用说明书
            </el-button>
          </div>
        </el-form>
        <div class="collapsed-sidebar-content" v-else>
          <div class="collapsed-logo">S</div>
        </div>
      </el-aside>

      <el-main class="workspace">
        <div class="hero-banner">
          <div class="banner-content">
            <div class="ai-badge-wrapper">
              <svg class="ai-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="ai-label">AI驱动</span>
            </div>
            <h1 class="glow-text">ScriptMaster 小说引擎 <span class="badge-pro">V1.0 PRO</span></h1>
            <p class="subtitle-enhanced">基于大语言模型的智能小说分镜解析系统</p>
          </div>
          <div class="banner-decoration"></div>
        </div>

        <el-tabs v-model="activeTab" class="premium-tabs">
          <el-tab-pane label="📚 智能分镜流 (Novel Workflow)" name="novel">
            <NovelWorkflow />
          </el-tab-pane>
          <el-tab-pane label="🎭 剧本衍生流" name="script">
            <ScriptWorkflow />
          </el-tab-pane>
          <el-tab-pane label="🛠️ 提示词工坊" name="studio">
            <div class="content-frame"><PromptStudio /></div>
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { provide } from 'vue';
import { ref, reactive, watch, onMounted } from 'vue';
import NovelWorkflow from './components/NovelWorkflow.vue';
import ScriptWorkflow from './components/ScriptWorkflow.vue';
import PromptStudio from './components/PromptStudio.vue';
import { ElMessage } from 'element-plus';
import { Sunny, Moon, ArrowLeft, ArrowRight } from '@element-plus/icons-vue';
import axios from 'axios';
import { apiUrl } from './api/base';
const activeTab = ref('novel');
const isSaving = ref(false);
const activeUsagePanel = ref(['1']); // 默认展开使用说明
const isDarkMode = ref(false);
const rememberConfig = ref(false);
const sidebarCollapsed = ref(false);

const config = reactive({
  provider: 'Mock (演示)',
  modelName: 'mock-model',
  apiKey: '',
  baseUrl: '',
});

// 提供全局配置
provide('config', config);

const API_BASE_URLS = {
  自定义三方Gemini: 'https://aigateway.edgecloudapp.com/v1/5087eed27d04cd00349d210e10fe620e/gemini-redbird',
  OpenRouter: 'https://openrouter.ai/api/v1',
  阿里云通义千问: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  'Google Gemini': '',
  'OpenAI (GPT)': '',
  'Mock (演示)': '',
};

// 🚀 严格按照你后台截图重写的模型列表
const MODEL_DICT = {
  'Mock (演示)': ['mock-model'],
  自定义三方Gemini: ['gemini-3.1-pro-preview'],
  阿里云通义千问: ['qwen3-max', 'qwen-plus', 'qwen-turbo'],
  'Google Gemini': ['gemini-3-flash-preview', 'gemini-3-pro-preview', 'gemini-3.1-pro-preview'],
  'OpenAI (GPT)': ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
};

const currentModelOptions = ref([]);

onMounted(() => {
  const savedConfig = localStorage.getItem('scriptMasterConfig');
  if (savedConfig) {
    const parsed = JSON.parse(savedConfig);
    // 解密API密钥
    if (parsed.config.apiKey) {
      parsed.config.apiKey = decryptApiKey(parsed.config.apiKey);
    }
    Object.assign(config, parsed.config);
    rememberConfig.value = parsed.remember;
  }
  currentModelOptions.value = MODEL_DICT[config.provider] || [];
  if (!config.modelName && currentModelOptions.value.length > 0) {
    config.modelName = currentModelOptions.value[0];
  }
});

// 监听服务商切换联动
watch(
  () => config.provider,
  (newProvider, oldProvider) => {
    if (newProvider === oldProvider) return; // 防止初始化覆盖
    if (API_BASE_URLS[newProvider] !== undefined) {
      config.baseUrl = API_BASE_URLS[newProvider];
    } else {
      config.baseUrl = '';
    }

    currentModelOptions.value = MODEL_DICT[newProvider] || [];

    if (currentModelOptions.value.length > 0) {
      config.modelName = currentModelOptions.value[0];
    } else {
      config.modelName = '';
    }

    // 切换大模型时清空 API Key
    config.apiKey = '';
  }
);

// 简单的加密函数，用于保护API密钥
const encryptApiKey = (apiKey) => {
  if (!apiKey) return '';
  // 使用简单的Base64编码作为基本保护
  return btoa(unescape(encodeURIComponent(apiKey)));
};

// 解密函数
const decryptApiKey = (encryptedKey) => {
  if (!encryptedKey) return '';
  try {
    return decodeURIComponent(escape(atob(encryptedKey)));
  } catch {
    return '';
  }
};

const saveConfig = async () => {
  if (config.provider !== 'Mock (演示)' && !config.apiKey) {
    ElMessage.warning('请提供有效的 API Key 进行鉴权！');
    return;
  }
  isSaving.value = true;
  try {
    const formData = new FormData();
    formData.append('provider', config.provider);
    formData.append('api_key', config.apiKey);
    formData.append('model_name', config.modelName);
    formData.append('base_url', config.baseUrl);
    const res = await axios.post(apiUrl('/api/config/verify'), formData);
    if (res.data.status === 'success') {
      ElMessage.success('🎉 引擎点火成功！AI 核心已上线！');
      // 只有在连接成功后才保存配置
      if (rememberConfig.value) {
        // 加密存储API密钥
        const encryptedConfig = {
          ...config,
          apiKey: encryptApiKey(config.apiKey)
        };
        localStorage.setItem('scriptMasterConfig', JSON.stringify({ config: encryptedConfig, remember: true }));
      } else {
        localStorage.removeItem('scriptMasterConfig');
      }
    } else {
      ElMessage.error(`连接失败: ${res.data.message}`);
    }
  } catch (err) {
    ElMessage.error('系统离线：请检查后端服务是否启动');
  } finally {
    isSaving.value = false;
  }
};

// 打开本地使用说明书
const openLocalManual = () => {
  // 在Electron环境中，使用shell.openPath打开本地文件
  if (window.electron) {
    window.electron.openLocalFile('用户说明手册.md');
  } else {
    // 在Web环境中，提示用户手动打开
    ElMessage.info('请在安装目录中找到并打开 "用户说明手册.md" 文件');
  }
};
</script>
<style scoped> 
/* 🌍 核心魔法：双主题 CSS 变量切换 */

.light-theme {
  --hermes-primary: #e3700d;
  --hermes-hover: #f28933;
  --bg-color: #f8f9fa;
  --panel-bg: #ffffff;
  --text-main: #2c3e50;
  --text-sub: #8e9bae;
  --border-color: #eaecef;
  --input-bg: #f5f7fa;
  --banner-bg: #2c3e50;
}

.dark-theme {
  --hermes-primary: #f97316;
  --hermes-hover: #fb923c;
  --bg-color: #111827;
  --panel-bg: #1f2937;
  --text-main: #ffffff;
  --text-sub: #d1d5db;
  --border-color: #374151;
  --input-bg: #374151;
  --banner-bg: linear-gradient(135deg, #1f2937 0%, #111827 100%);
}

body {
  margin: 0;
  background-color: var(--bg-color);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: var(--text-main);
  transition:
    background-color 0.3s ease,
    color 0.3s ease;
}

.app-wrapper {
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-color);
  transition: all 0.3s ease;
}
.main-container {
  height: 100%;
}

.premium-sidebar {
  background: var(--panel-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.05);
  z-index: 10;
  transition: all 0.3s ease;
}

.sidebar-header {
  padding: 30px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-color);
}
.logo-box {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--hermes-primary), #ff9800);
  border-radius: 10px;
  color: white;
  font-size: 24px;
  font-weight: 900;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
}
.sidebar-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  max-width: 160px;
}
.premium-form {
  padding: 24px;
}
.premium-form .el-form-item__label {
  font-weight: 600;
  padding-bottom: 4px;
  color: var(--text-main) !important;
  width: 100%;
}

.flex-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
.remember-chk {
  margin-right: 0 !important;
  color: var(--text-sub) !important;
  font-weight: normal;
}

.premium-form .el-input__wrapper,
.premium-form .el-select__wrapper {
  background-color: var(--input-bg);
  border-radius: 8px;
  box-shadow: none !important;
  border: 1px solid var(--border-color);
  transition: all 0.3s;
}
.dark-theme .el-input__inner {
  color: #f9fafb !important;
}
.dark-theme .el-input__inner::placeholder {
  color: #9ca3af !important;
}
.premium-form .el-input__wrapper:hover,
.premium-form .el-input__wrapper.is-focus {
  border-color: var(--hermes-primary);
  box-shadow: 0 0 0 2px rgba(227, 112, 13, 0.1) !important;
}

.btn-ignite {
  width: 100%;
  margin-top: 20px;
  height: 44px;
  background: var(--text-main);
  color: var(--bg-color);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.3s;
}
.dark-theme .btn-ignite {
  background: var(--hermes-primary);
  color: white;
}
.dark-theme .btn-ignite:hover {
  filter: brightness(1.1);
  box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);
}
.light-theme .btn-ignite:hover {
  background: var(--hermes-primary);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(227, 112, 13, 0.3);
}

/* 使用说明部分样式 */
.usage-guide {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.guide-content {
  padding: 16px;
  background: var(--input-bg);
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.guide-content h4 {
  margin-top: 0;
  margin-bottom: 12px;
  color: var(--text-main);
  font-size: 14px;
  font-weight: 600;
}

.guide-content ul {
  margin: 0 0 16px 0;
  padding-left: 20px;
  color: var(--text-sub);
}

.guide-content li {
  margin-bottom: 6px;
}

.open-manual-btn {
  margin-top: 16px;
  width: 100%;
}

/* 侧边栏伸缩按钮 */
.sidebar-toggle-btn {
  color: var(--text-main);
  transition: all 0.3s ease;
  border-radius: 6px;
  padding: 6px;
}

.sidebar-toggle-btn:hover {
  background: rgba(227, 112, 13, 0.1);
  color: var(--hermes-primary);
  transform: scale(1.1);
}

/* 收起状态的侧边栏内容 */
.collapsed-sidebar-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px 0;
}

.collapsed-logo {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--hermes-primary), #ff9800);
  border-radius: 10px;
  color: white;
  font-size: 24px;
  font-weight: 900;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
  margin-bottom: 20px;
}

/* 侧边栏过渡动画 */
.premium-sidebar {
  transition: width 0.3s ease;
}

.sidebar-header {
  transition: all 0.3s ease;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .premium-sidebar {
    width: 240px !important;
  }
  .premium-sidebar.collapsed {
    width: 60px !important;
  }
  .workspace {
    padding: 16px 20px;
  }
  .hero-banner {
    padding: 16px 20px;
  }
}

.workspace {
  padding: 24px 32px;
  background: transparent;
  overflow-y: auto;
}
.hero-banner {
  background: var(--banner-bg);
  border-radius: 16px;
  padding: 24px 32px;
  position: relative;
  overflow: hidden;
  margin-bottom: 24px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}
.banner-content {
  position: relative;
  z-index: 2;
}
.glow-text {
  margin: 0;
  font-size: 32px;
  color: white;
  font-weight: 800;
  letter-spacing: -0.5px;
}
.dark-theme .glow-text {
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
}
.badge-pro {
  background: linear-gradient(135deg, var(--hermes-primary), #ff9800);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 20px;
  vertical-align: middle;
  margin-left: 12px;
  font-weight: 700;
  color: white;
}
.dark-theme .badge-pro {
  color: #000;
  box-shadow: 0 0 15px rgba(255, 90, 0, 0.4);
}
/* AI徽章样式 */
.ai-badge-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 20px;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
}

.ai-icon {
  width: 20px;
  height: 20px;
  color: #6366f1;
  animation: float 3s ease-in-out infinite;
}

.ai-label {
  font-size: 13px;
  font-weight: 700;
  color: #6366f1;
  letter-spacing: 0.5px;
}

.dark-theme .ai-badge-wrapper {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.4);
}

.dark-theme .ai-icon,
.dark-theme .ai-label {
  color: #818cf8;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-5px);
  }
}

.subtitle-enhanced {
  color: #a0aabf;
  margin: 10px 0 0 0;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.dark-theme .subtitle-enhanced {
  color: #d1d5db;
}

.banner-content p {
  color: #a0aabf;
  margin: 10px 0 0 0;
  font-size: 15px;
}
.banner-decoration {
  position: absolute;
  right: -50px;
  top: -100px;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(227, 112, 13, 0.15) 0%, rgba(255, 255, 255, 0) 70%);
  border-radius: 50%;
}

.premium-tabs .el-tabs__nav-wrap::after {
  display: none;
}
.premium-tabs .el-tabs__item {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-sub);
  padding: 0 24px !important;
  height: 48px;
}
.premium-tabs .el-tabs__item.is-active {
  color: var(--hermes-primary);
}
.premium-tabs .el-tabs__active-bar {
  background-color: var(--hermes-primary);
  height: 3px;
  border-radius: 3px;
}

.dark-theme .glass-card {
  background: var(--panel-bg);
  border-color: var(--border-color);
  color: var(--text-main);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}
.dark-theme .premium-steps {
  background: var(--panel-bg);
  border: 1px solid var(--border-color);
}
.dark-theme .box-header {
  color: #f9fafb;
}

.dark-theme .premium-upload-container {
  background: #374151;
  border-color: var(--border-color);
}
.dark-theme .premium-upload-container:hover {
  border-color: var(--hermes-primary);
  background: #1f2937;
}
.dark-theme .upload-icon-wrapper {
  background: #1f2937;
}
.dark-theme .file-name-badge {
  background: #374151;
  color: #f9fafb;
  border-color: var(--border-color);
}
.dark-theme .upload-title {
  color: #f9fafb;
}

.dark-theme .el-table {
  --el-table-bg-color: #1f2937;
  --el-table-tr-bg-color: #1f2937;
  --el-table-header-bg-color: #374151;
  --el-table-border-color: var(--border-color);
  --el-table-text-color: #e5e7eb;
  --el-table-header-text-color: #f9fafb;
}
.dark-theme .el-table td,
.dark-theme .el-table th.is-leaf {
  border-bottom: 1px solid var(--border-color);
}
.dark-theme .el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background-color: #111827;
}

.dark-theme .el-textarea__inner {
  background-color: #111827 !important;
  border-color: var(--border-color) !important;
  color: #f9fafb !important;
}
.dark-theme .el-textarea__inner::placeholder {
  color: #9ca3af !important;
}

.dark-theme .script-paper {
  background: #111827;
  border-color: var(--border-color);
}
.dark-theme .script-paper pre {
  color: #e5e7eb;
}
.dark-theme .estimate-box {
  background: #374151;
  border-color: var(--border-color);
  color: var(--hermes-primary);
}
.dark-theme .rendering-status {
  background: #1f2937;
  border-color: var(--border-color);
}
.dark-theme .el-tabs--border-card {
  background: var(--panel-bg);
  border-color: var(--border-color);
}
.dark-theme .el-tabs--border-card > .el-tabs__header {
  background-color: #111827;
  border-bottom-color: var(--border-color);
}
.dark-theme .el-tabs--border-card > .el-tabs__header .el-tabs__item.is-active {
  background-color: var(--panel-bg);
  border-right-color: var(--border-color);
  border-left-color: var(--border-color);
  color: var(--hermes-primary);
}

.dark-theme .el-dialog {
  background: var(--panel-bg);
}
.dark-theme .el-dialog__title {
  color: #f9fafb;
}
.dark-theme .full-text-reader {
  background: #111827;
  color: #e5e7eb;
}
</style>

