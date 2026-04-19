<template>
  <div class="modern-studio-container fade-in">
    <aside class="modern-sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon"><el-icon><Cpu /></el-icon></div>
        <div class="brand-text">
          <h2>Prompt Studio</h2>
          <span>引擎逻辑调优台</span>
        </div>
      </div>

      <nav class="asset-nav">
        <div class="nav-label">核心资产模块</div>
        <div 
          v-for="(label, key) in assetMap" 
          :key="key" 
          class="nav-item" 
          :class="{ active: currentKey === key }"
          @click="switchAsset(key)"
        >
          <el-icon class="nav-icon"><component :is="getIcon(key)" /></el-icon>
          <div class="nav-info">
            <span class="title">{{ label }}</span>
            <span class="subtitle">{{ key }}</span>
          </div>
          <div v-if="currentKey === key" class="active-indicator"></div>
        </div>
      </nav>

      <div class="sidebar-actions">
        <el-tooltip :disabled="missingVars.length === 0" content="请修复缺失的变量槽后再部署" placement="top">
          <el-button class="action-btn deploy" @click="handleDeploy" :loading="isDeploying" :disabled="missingVars.length > 0">
            <el-icon><UploadFilled /></el-icon> 部署至生产
          </el-button>
        </el-tooltip>
        <el-button class="action-btn reset" plain @click="handleReset">
          <el-icon><RefreshLeft /></el-icon> 还原出厂设定
        </el-button>
      </div>
    </aside>

    <main class="modern-main">
      <header class="main-topbar">
        <div class="current-module-info">
          <span class="pulse-ring" :class="{'error-ring': missingVars.length > 0}"></span>
          <h3>正在编辑：{{ assetMap[currentKey] }}</h3>
        </div>
        
        <div class="glass-tabs">
          <button :class="{ active: activeTab === 'Edit' }" @click="activeTab = 'Edit'">
            <el-icon><EditPen /></el-icon> 创作台
          </button>
          <button :class="{ active: activeTab === 'Diff' }" @click="activeTab = 'Diff'">
            <el-icon><Connection /></el-icon> 版本审查
          </button>
          <button :class="{ active: activeTab === 'Playground' }" @click="activeTab = 'Playground'">
            <el-icon><DataAnalysis /></el-icon> A/B 实验室
          </button>
        </div>
      </header>

      <div class="workspace-area">
        
        <div v-show="activeTab === 'Edit'" class="workspace-panel edit-panel">
          <div class="editor-tools" :class="{ 'has-error': missingVars.length > 0 }">
            <div class="detected-vars">
              <el-icon><MagicStick /></el-icon> 必填变量补全栏：
              <el-tag 
                v-for="v in officialVars" 
                :key="v" 
                class="var-clickable-badge" 
                :class="{'is-missing': missingVars.includes(v)}"
                @click="insertVar(v)"
              >
                {{ getFriendlyVarName(v) }} {{"{" + v + "}"}}
              </el-tag>
            </div>
            
            <div class="tools-right">
              <span class="save-status" :class="{'is-saved': saveStatus.includes('已'), 'is-error': missingVars.length > 0}">
                <span class="pulse-dot" v-if="saveStatus === '正在保存...'"></span>
                <el-icon v-else-if="missingVars.length === 0" style="color: #10b981;"><CircleCheck /></el-icon>
                <el-icon v-else style="color: #ef4444;"><CircleClose /></el-icon>
                {{ missingVars.length > 0 ? '必备变量缺失' : saveStatus }}
              </span>
              <el-button class="fullscreen-btn" size="small" plain @click="isFullscreen = true">
                <el-icon><FullScreen /></el-icon> 全屏专注编写
              </el-button>
            </div>
          </div>

          <div class="mac-ide-wrapper" :class="{ 'error-border': missingVars.length > 0 }">
            <div class="mac-header">
              <div class="traffic-lights">
                <span class="light red"></span>
                <span class="light yellow"></span>
                <span class="light green"></span>
              </div>
              <div class="filename">{{ currentKey.toLowerCase() }}.prompt</div>
              <div class="copy-action" @click="copyToClipboard">
                <el-icon><CopyDocument /></el-icon>
              </div>
            </div>
            <div class="ide-body" style="position: relative;">
              <div class="line-numbers" ref="lineNumbersRef">
                <div v-for="n in lineCount" :key="n" class="num">{{ n }}</div>
              </div>
              <textarea 
                ref="textareaRef"
                v-model="editBuffer" 
                class="code-input" 
                wrap="off" 
                spellcheck="false"
                @scroll="syncScroll"
                @keydown.tab.prevent="handleTab"
                placeholder="在此编写提示词逻辑..."
              ></textarea>
            </div>
          </div>

          <el-collapse class="ref-collapse mt-15">
            <el-collapse-item name="1">
              <template #title>
                <div class="collapse-header"><el-icon><View /></el-icon> 参考：官方出厂默认配置</div>
              </template>
              <div class="ref-toolbar">
                <el-button link type="primary" size="small" @click="copyOfficial">
                  <el-icon><CopyDocument /></el-icon> 复制官方配置
                </el-button>
                <el-button link type="primary" size="small" @click="isOfficialFullscreen = true">
                  <el-icon><FullScreen /></el-icon> 全屏放大查看
                </el-button>
              </div>
              <pre class="readonly-bg">{{ officialPrompt }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div v-show="activeTab === 'Diff'" class="workspace-panel diff-panel">
          <div class="diff-header-toolbar">
            <div class="diff-legend">
              <span class="legend-item removed"><span class="sign">-</span> 官方删除内容</span>
              <span class="legend-item added"><span class="sign">+</span> 您的新增内容</span>
              <span class="legend-item inline-demo" style="margin-left: 10px; font-weight: normal; color: #6b7280;">
                ( 深色高亮框代表 <span style="background:#ff818266; padding:0 2px; color:#cf222e;">具体</span> / <span style="background:#abf2bc66; padding:0 2px; color:#116329;">修改字词</span> )
              </span>
            </div>
            <el-button size="small" plain @click="isDiffFullscreen = true" class="fullscreen-btn">
              <el-icon><FullScreen /></el-icon> 全屏审查模式
            </el-button>
          </div>
          <div class="diff-code-box" v-html="diffHtml"></div>
        </div>

        <div v-show="activeTab === 'Playground'" class="workspace-panel playground-panel">
          <div class="pg-sidebar">
            <h4><el-icon><Setting /></el-icon> 沙盒数据注入</h4>
            <div class="var-list">
              <div v-for="v in officialVars" :key="v" class="var-input-group">
                <div class="var-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                  <label style="margin: 0;">{{ v }} <span style="color: #ef4444; font-size: 1rem; font-weight: bold;">*</span> <span style="font-size: 0.75rem; color: #6b7280; font-family: sans-serif; font-weight: normal;">({{ getFriendlyVarName(v) }})</span></label>
                  <div style="display: flex; gap: 8px; align-items: center;">
                    <el-tooltip content="清空内容" placement="top">
                      <el-button link type="danger" size="small" @click="testInputs[v] = ''" v-if="testInputs[v]">
                        <el-icon><CircleClose /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <el-upload
                      v-if="(currentKey === 'OUTLINE_TASK' || currentKey === 'BATCH_SCRIPT_PROMPT') && (v === 'content' || v === 'user_choice')"
                      action=""
                      :auto-upload="false"
                      :show-file-list="false"
                      :on-change="(file) => handleImportFile(file, v)"
                      accept=".xlsx,.xls,.csv"
                    >
                      <el-button link type="primary" size="small"><el-icon><DocumentAdd /></el-icon>导入 Excel 小说</el-button>
                    </el-upload>

                    <el-upload
                      v-if="currentKey === 'SCRIPT_TASK_TEMPLATE' && v === 'outline'"
                      action=""
                      :auto-upload="false"
                      :show-file-list="false"
                      :on-change="(file) => handleImportFile(file, v)"
                      accept=".docx,.txt"
                    >
                      <el-button link type="primary" size="small"><el-icon><DocumentAdd /></el-icon>导入 Word 大纲</el-button>
                    </el-upload>
                  </div>
                </div>
                <el-input v-model="testInputs[v]" :type="['content', 'outline', 'original_idea', 'user_choice'].includes(v) ? 'textarea' : 'text'" :rows="['content', 'outline', 'user_choice'].includes(v) ? 5 : 1" :autosize="['content', 'outline', 'original_idea', 'user_choice'].includes(v) ? { minRows: 5, maxRows: 15 } : false" style="width: 100%" />
              </div>
            </div>
            <el-button class="battle-btn" @click="runABTest" :loading="isTesting" v-if="!isTesting" :disabled="missingVars.length > 0">
              <el-icon><Lightning /></el-icon> 开启双屏演练
            </el-button>
            <el-button type="danger" class="battle-btn" @click="stopTest" v-else>
              <el-icon><VideoPause /></el-icon> 紧急阻断渲染
            </el-button>
          </div>
          
          <div class="pg-screens">
              <div class="mock-screen">
                <div class="screen-head">
                  <div class="title-left">🏛️ 官方原版输出</div>
                  <div class="tools-right">
                    <el-button link class="tool-btn" @click="copyContent(testResults.official)" title="复制内容"><el-icon><CopyDocument /></el-icon></el-button>
                    <el-button link class="tool-btn" @click="exportPlaygroundWord(testResults.official, '官方原版')" title="导出 Word"><el-icon><Download /></el-icon></el-button>
                    <el-button link class="tool-btn" @click="openReader('官方原版输出', testResults.official)" title="全屏沉浸阅读"><el-icon><FullScreen /></el-icon></el-button>
                  </div>
                </div>
                <div class="screen-content script-reader" v-html="testResults.official"></div>
              </div>

              <div class="mock-screen active-monitor">
                <div class="screen-head glow">
                  <div class="title-left">🛠️ 当前调优版输出 <span class="live-dot" v-if="isTesting"></span></div>
                  <div class="tools-right">
                    <el-button link class="tool-btn" @click="copyContent(testResults.draft)" title="复制内容"><el-icon><CopyDocument /></el-icon></el-button>
                    <el-button link class="tool-btn" @click="exportPlaygroundWord(testResults.draft, '调优版')" title="导出 Word"><el-icon><Download /></el-icon></el-button>
                    <el-button link class="tool-btn" @click="openReader('当前调优版输出', testResults.draft)" title="全屏沉浸阅读"><el-icon><FullScreen /></el-icon></el-button>
                  </div>
                </div>
                <div class="screen-content script-reader" v-html="testResults.draft"></div>
              </div>
            </div>
        </div>

      </div>
    </main>

    <el-dialog v-model="isFullscreen" fullscreen :show-close="false" class="zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title">
          <el-icon><EditPen /></el-icon> 专注模式 - {{ assetMap[currentKey] }}
          <span class="save-status ml-4" style="font-size: 0.8rem; font-weight: normal; color:#9ca3af;">{{ saveStatus }}</span>
        </div>
        <el-button type="danger" plain @click="isFullscreen = false">退出专注模式</el-button>
      </div>
      <div class="mac-ide-wrapper zen-ide" :class="{ 'error-border': missingVars.length > 0 }">
        <div class="ide-body">
          <div class="line-numbers" ref="zenLineNumbersRef">
            <div v-for="n in lineCount" :key="n" class="num">{{ n }}</div>
          </div>
          <textarea 
            v-model="editBuffer" 
            class="code-input" 
            wrap="off" 
            spellcheck="false"
            @scroll="syncZenScroll"
          ></textarea>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="isOfficialFullscreen" fullscreen :show-close="false" class="zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title" style="color: #6b7280;"><el-icon><View /></el-icon> 官方配置全屏 (只读)</div>
        <div style="display: flex; gap: 12px;">
          <el-button type="primary" plain @click="copyOfficial"><el-icon><CopyDocument /></el-icon> 复制内容</el-button>
          <el-button type="danger" plain @click="isOfficialFullscreen = false">退出阅览</el-button>
        </div>
      </div>
      <div class="mac-ide-wrapper zen-ide">
        <div class="ide-body">
          <textarea readonly :value="officialPrompt" class="code-input readonly-fullscreen" wrap="off" spellcheck="false"></textarea>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="isDiffFullscreen" fullscreen :show-close="false" class="zen-dialog diff-zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title" style="color: #6b7280;"><el-icon><ZoomIn /></el-icon> 全屏版本比对</div>
        <el-button type="danger" plain @click="isDiffFullscreen = false">退出审查</el-button>
      </div>
      <div class="diff-code-box zen-diff-box" v-html="diffHtml"></div>
    </el-dialog>
    <el-dialog v-model="readerVisible" :title="`📖 沉浸阅读 - ${readerTitle}`" width="70%" center class="hermes-dialog">
      <div class="full-text-reader" v-html="readerContent"></div>
      <template #footer>
        <div class="dialog-footer-actions">
          <el-button @click="readerVisible = false" size="large">关闭预览</el-button>
          <el-button type="primary" style="background: #e3700d; border: none;" @click="exportPlaygroundWord(readerContent, readerTitle)" size="large">
            <el-icon style="margin-right: 8px"><Download /></el-icon> 导出此内容为 Word
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, inject } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { engine } from '../api/engine'
import * as XLSX from 'xlsx'
import JSZip from 'jszip'
import { throttle, isMockMode, createErrorMessage } from '../utils'
import { 
  Collection, VideoCamera, Memo, SetUp, MagicStick, User, Reading, 
  Upload, RefreshLeft, CopyDocument, Setting, Lightning, VideoPause, DocumentAdd, FullScreen, Download
} from '@element-plus/icons-vue'

// 注入全局配置
const config = inject('config', { provider: 'Mock (演示)' })

// API Key验证函数
const validateApiKey = () => {
  if (!config) return true;
  if (config.provider === 'Mock (演示)') return true;
  if (!config.apiKey || config.apiKey.trim() === '') {
    ElMessage.warning('请先在左侧配置并连接API Key！'); return false;
  }
  return true;
};

// 监听provider变化，从Mock模式切换到非Mock模式时清空testResults
watch(() => config.provider, (newProvider, oldProvider) => {
  if (oldProvider === 'Mock (演示)' && newProvider !== 'Mock (演示)') {
    // 从Mock模式切换到非Mock模式，清空之前的生成结果
    testResults.value = { official: "", draft: "" };
    isTesting.value = false;
  }
});

const assetMap = {
  "SCRIPT_SYSTEM": "导演全局人设",
  "OUTLINE_TASK": "小说大纲策略",
  "BATCH_SCRIPT_PROMPT": "小说分镜约束",
  "ACT_GEN_TASK": "剧本三幕式生成",
  "SCRIPT_TASK_TEMPLATE": "剧本分镜约束"
}

const friendlyVarMap = {
  "start_ep": "起始集数",
  "end_ep": "结束集数",
  "total_episodes": "总集数",
  "content": "分镜源文",
  "user_choice": "大纲源文",
  "outline": "分集大纲",
  "episode_range": "集数范围",
  "original_idea": "原始创意"
}
const getFriendlyVarName = (v) => friendlyVarMap[v] || "参数"
// 【新增】阅读器相关状态
const readerVisible = ref(false);
const readerTitle = ref("");
const readerContent = ref("");

// 【新增】一键复制内容
const copyContent = (text) => { 
  const cleanText = text.replace(/<[^>]*>?/gm, ''); // 简单去HTML标签
  navigator.clipboard.writeText(cleanText); 
  ElMessage.success("内容已复制！"); 
};

// 【新增】打开全屏阅读器
const openReader = (title, content) => {
  readerTitle.value = title;
  readerContent.value = content || '<p style="color:#999;text-align:center;">暂无内容生成</p>';
  readerVisible.value = true;
};

// 【新增】沙盒专用导出 Word
const exportPlaygroundWord = (content, suffix) => {
  if (!content || content.includes('火箭发射中')) return ElMessage.warning("没有可导出的有效内容");
  
  // 清理掉可能的HTML loading图标等，保留换行
  let cleanContent = content.replace(/<span class="rocket-spin">.*?<\/span>/g, '');
  
  const header = "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'></head><body>";
  const footer = '</body></html>';
  // 处理换行符
  const formattedContent = cleanContent.includes('<br') ? cleanContent : cleanContent.replace(/\n/g, '<br>');
  const sourceHTML = header + "<div style='font-family: Microsoft YaHei, sans-serif; line-height: 1.8; font-size: 14px;'>" + formattedContent + '</div>' + footer;
  
  const source = 'data:application/vnd.ms-word;charset=utf-8,' + encodeURIComponent(sourceHTML);
  const fileDownload = document.createElement('a');
  document.body.appendChild(fileDownload);
  fileDownload.href = source;
  fileDownload.download = `${assetMap[currentKey.value]}_${suffix}.doc`;
  fileDownload.click();
  document.body.removeChild(fileDownload);
  ElMessage.success(`🎉 ${suffix} Word文档已开始下载！`);
};
const currentKey = ref("BATCH_SCRIPT_PROMPT")
const activeTab = ref("Edit")
const editBuffer = ref("")
const officialPrompt = ref("")
const testInputs = ref({})
const isDeploying = ref(false)
const isTesting = ref(false)
const testResults = ref({ official: "", draft: "" })
const currentTaskId = ref("")


const isFullscreen = ref(false)
const isOfficialFullscreen = ref(false) 
const isDiffFullscreen = ref(false) 

const lineNumbersRef = ref(null)
const zenLineNumbersRef = ref(null)
const textareaRef = ref(null)

const saveStatus = ref("已与云端同步")
let saveTimeout = null
let lastValidText = "";
const getIcon = (key) => {
  if (key.includes('SYSTEM')) return User
  if (key.includes('OUTLINE')) return Reading
  if (key.includes('BATCH')) return MagicStick
  return Setting
}

// ✨ 手感增强：光标处插入变量
const insertVar = (v) => {
  const el = textareaRef.value;
  if (!el) return;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const content = editBuffer.value;
  const varStr = `{${v}}`;
  editBuffer.value = content.substring(0, start) + varStr + content.substring(end);
  // 插入后让光标停在变量后面
  nextTick(() => {
    el.focus();
    el.selectionStart = el.selectionEnd = start + varStr.length;
  });
}
// 🚨 物理锁定逻辑增强：检测到变量名受损即回滚 DOM 🚨
const enforceVariableLock = (e) => {
  const currentText = editBuffer.value;
  const requiredVarStrings = officialVars.value.map(v => `{${v}}`);
  const isBroken = requiredVarStrings.some(varStr => !currentText.includes(varStr));
  
  if (isBroken) {
    const el = e.target;
    editBuffer.value = lastValidText; // 数据回滚
    nextTick(() => { if (el) el.value = lastValidText; }); // 物理同步回滚 DOM
    ElMessage.error({ 
      message: "<span class='error-icon'>❌</span> 禁止修改或删除系统必备变量槽！", 
      grouping: true, 
      duration: 3000,
      customClass: 'friendly-error-message'
    });
  } else {
    lastValidText = currentText; // 记录新的合法快照
  }
}
// ✨ 手感增强：支持 Tab 键缩进
const handleTab = (e) => {
  const el = e.target;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  editBuffer.value = editBuffer.value.substring(0, start) + "    " + editBuffer.value.substring(end);
  nextTick(() => {
    el.selectionStart = el.selectionEnd = start + 4;
  });
}

// 🚨 修复核心：MissingVars 必须放在 computed 中实时侦听
const detectedVars = computed(() => {
  if (!editBuffer.value) return [];
  // 更宽松的正则表达式，匹配大括号内的任何内容
  const matches = editBuffer.value.match(/\{([^}]+)\}/g) || [];
  const vars = matches.map(m => m.replace(/[{}]/g, '').trim()).filter(v => v);
  console.log('检测到的变量:', vars);
  return [...new Set(vars)];
})
const officialVars = computed(() => {
  if (!officialPrompt.value) return [];
  // 更宽松的正则表达式，匹配大括号内的任何内容
  const matches = officialPrompt.value.match(/\{([^}]+)\}/g) || [];
  const vars = matches.map(m => m.replace(/[{}]/g, '').trim()).filter(v => v);
  console.log('官方变量:', vars);
  return [...new Set(vars)];
})
const missingVars = computed(() => {
  const official = officialVars.value;
  if (official.length === 0) {
    // 如果官方提示词不包含变量，就没有缺失的变量
    console.log('官方提示词不包含变量，无需检测');
    return [];
  }
  const detected = detectedVars.value;
  
  // 智能变量匹配：忽略变量名中的数字和错误
  const isVariablePresent = (officialVar, detectedVars) => {
    // 基本匹配
    if (detectedVars.includes(officialVar)) return true;
    
    // 智能匹配：忽略数字和特殊字符
    const officialVarBase = officialVar.replace(/\d/g, ''); // 移除数字
    return detectedVars.some(detectedVar => {
      const detectedVarBase = detectedVar.replace(/\d/g, ''); // 移除数字
      return detectedVarBase === officialVarBase;
    });
  };
  
  const missing = official.filter(v => !isVariablePresent(v, detected));
  console.log('缺失的变量:', missing);
  return missing;
})

watch(editBuffer, (newVal) => {
  if (!newVal) return;
  saveStatus.value = "正在保存...";
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    localStorage.setItem(`prompt_draft_${currentKey.value}`, newVal);
    saveStatus.value = "已保存在本地草稿";
  }, 500); 
})

const lineCount = computed(() => editBuffer.value ? editBuffer.value.split('\n').length : 1)
const syncScroll = (e) => { if (lineNumbersRef.value) lineNumbersRef.value.scrollTop = e.target.scrollTop }
const syncZenScroll = (e) => { if (zenLineNumbersRef.value) zenLineNumbersRef.value.scrollTop = e.target.scrollTop }

const handleImportFile = async (fileObj, varName) => {
  const file = fileObj.raw; if (!file) return;
  const fileName = file.name.toLowerCase();
  try {
    if (currentKey.value === 'OUTLINE_TASK' || currentKey.value === 'BATCH_SCRIPT_PROMPT') {
      if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls') && !fileName.endsWith('.csv')) {
        ElMessage.error({ 
          message: "<span class='error-icon'>❌</span> 格式错误：请导入 Excel/CSV 文件！", 
          grouping: true, 
          duration: 3000,
          customClass: 'friendly-error-message'
        }); return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          const json = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]], { header: 1 });
          let text = "";
          json.forEach((row, idx) => {
            if (idx === 0 && String(row[0] || '').includes('章节')) return;
            if (row[1]) text += `【${row[0] || `章节${idx}`}】\n${row[1]}\n\n`;
          });
          testInputs.value[varName] = text.trim();
          ElMessage.success(`🎉 小说解析成功！`);
        } catch (err) { 
          ElMessage.error({ 
            message: `<span class='error-icon'>❌</span> 解析失败：${err.message}`, 
            grouping: true, 
            duration: 3000,
            customClass: 'friendly-error-message'
          }); 
        }
      };
      reader.readAsArrayBuffer(file);
    } 
    else if (currentKey.value === 'SCRIPT_TASK_TEMPLATE') {
      if (!fileName.endsWith('.docx') && !fileName.endsWith('.txt')) { 
        ElMessage.error({ 
          message: "<span class='error-icon'>❌</span> 格式错误：请导入 Word/TXT 大纲文件！", 
          grouping: true, 
          duration: 3000,
          customClass: 'friendly-error-message'
        }); return; 
      }
      if (fileName.endsWith('.txt')) {
        const reader = new FileReader(); reader.onload = (e) => { testInputs.value[varName] = e.target.result; ElMessage.success(`🎉 TXT 导入成功！`); };
        reader.readAsText(file);
      } else if (fileName.endsWith('.docx')) {
        const zip = new JSZip(); const loadedZip = await zip.loadAsync(file);
        const xmlData = await loadedZip.file("word/document.xml").async("string");
        testInputs.value[varName] = xmlData.replace(/<w:p[^>]*>/gi, '\n').replace(/<[^>]+>/g, '').trim();
        ElMessage.success(`🎉 Word 大纲解析成功！`);
      }
    }
  } catch (error) { 
    ElMessage.error({ 
      message: `<span class='error-icon'>❌</span> 文件处理异常：${error.message}`, 
      grouping: true, 
      duration: 3000,
      customClass: 'friendly-error-message'
    }); 
  }
}

const escapeHtml = (unsafe) => (unsafe || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")

// LCS 算法保持极致精准
const diffHtml = computed(() => {
  const oldLines = officialPrompt.value.split('\n');
  const newLines = editBuffer.value.split('\n');
  const dp = Array(oldLines.length + 1).fill(null).map(() => Array(newLines.length + 1).fill(0));
  for (let i = 1; i <= oldLines.length; i++) {
    for (let j = 1; j <= newLines.length; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) dp[i][j] = dp[i - 1][j - 1] + 1;
      else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }
  let i = oldLines.length, j = newLines.length;
  const diff = [];
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) { diff.unshift({ type: 'unchanged', text: oldLines[i - 1] }); i--; j--; }
    else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) { diff.unshift({ type: 'added', text: newLines[j - 1] }); j--; }
    else if (i > 0 && (j === 0 || dp[i][j - 1] < dp[i - 1][j])) { diff.unshift({ type: 'removed', text: oldLines[i - 1] }); i--; }
  }
  let html = '';
  for (let k = 0; k < diff.length; k++) {
    const item = diff[k];
    if (item.type === 'removed' && k + 1 < diff.length && diff[k+1].type === 'added') {
      const textOld = item.text; const textNew = diff[k+1].text;
      const dpInline = Array(textOld.length + 1).fill(null).map(() => Array(textNew.length + 1).fill(0));
      for (let x = 1; x <= textOld.length; x++) {
        for (let y = 1; y <= textNew.length; y++) {
          if (textOld[x - 1] === textNew[y - 1]) dpInline[x][y] = dpInline[x - 1][y - 1] + 1;
          else dpInline[x][y] = Math.max(dpInline[x - 1][y], dpInline[x][y - 1]);
        }
      }
      let x = textOld.length, y = textNew.length;
      const dOld = [], dNew = [];
      while (x > 0 || y > 0) {
        if (x > 0 && y > 0 && textOld[x - 1] === textNew[y - 1]) { dOld.unshift({ char: textOld[x - 1], type: 'unchanged' }); dNew.unshift({ char: textNew[y - 1], type: 'unchanged' }); x--; y--; }
        else if (y > 0 && (x === 0 || dpInline[x][y - 1] >= dpInline[x - 1][y])) { dNew.unshift({ char: textNew[y - 1], type: 'added' }); y--; }
        else if (x > 0 && (y === 0 || dpInline[x][y - 1] < dpInline[x - 1][y])) { dOld.unshift({ char: textOld[x - 1], type: 'removed' }); x--; }
      }
      const renderInline = (arr, tC) => {
        let r = ''; let inS = false;
        arr.forEach(o => {
          if (o.type === tC) { if (!inS) { r += `<span class="inline-${tC}">`; inS = true; } r += escapeHtml(o.char); }
          else { if (inS) { r += `</span>`; inS = false; } r += escapeHtml(o.char); }
        });
        if (inS) r += `</span>`; return r || ' ';
      };
      html += `<div class="diff-row removed"><span class="diff-num">-</span><span class="diff-content">${renderInline(dOld, 'removed')}</span></div>`;
      html += `<div class="diff-row added"><span class="diff-num">+</span><span class="diff-content">${renderInline(dNew, 'added')}</span></div>`;
      k++; 
    } else {
      if (item.type === 'unchanged') html += `<div class="diff-row unchanged"><span class="diff-num"> </span><span class="diff-content">${escapeHtml(item.text) || ' '}</span></div>`;
      else if (item.type === 'added') html += `<div class="diff-row added"><span class="diff-num">+</span><span class="diff-content">${escapeHtml(item.text) || ' '}</span></div>`;
      else if (item.type === 'removed') html += `<div class="diff-row removed"><span class="diff-num">-</span><span class="diff-content">${escapeHtml(item.text) || ' '}</span></div>`;
    }
  }
  return html;
})

const loadPrompt = async () => {
  try {
    const res = await axios.get(`/api/script/prompts/${currentKey.value}`)
    if (res.data && res.data.status === 'success') {
      officialPrompt.value = res.data.official_prompt || ''
      const localDraft = localStorage.getItem(`prompt_draft_${currentKey.value}`)
      if (localDraft && localDraft !== res.data.user_prompt) { 
        editBuffer.value = localDraft 
        saveStatus.value = "已恢复未部署的本地草稿"
      } else { 
        editBuffer.value = res.data.user_prompt || ''
        saveStatus.value = "已与云端同步"
      }
      // 直接从官方提示词中提取变量并初始化测试输入
      const matches = officialPrompt.value.match(/\{([a-zA-Z_]\w*)\}/g) || [];
      const vars = [...new Set(matches.map(m => m.replace(/[{}]/g, '')))];
      vars.forEach(v => { 
        if(!testInputs.value[v]) testInputs.value[v] = ""
      })
      console.log('加载完成，官方变量:', vars)
    } else {
      ElMessage.error({ 
        message: `<span class='error-icon'>❌</span> 资产加载失败：${res.data.message}`, 
        grouping: true, 
        duration: 3000,
        customClass: 'friendly-error-message'
      })
    }
  } catch (err) {
    console.error('加载失败:', err)
    ElMessage.error({ 
      message: "<span class='error-icon'>❌</span> 资产加载失败，请检查网络连接或后端服务是否正常！", 
      grouping: true, 
      duration: 3000,
      customClass: 'friendly-error-message'
    })
  }
}

const switchAsset = (key) => { currentKey.value = key; loadPrompt(); testResults.value = { official: "", draft: "" }; isTesting.value = false }

const handleDeploy = async () => {
  if (missingVars.value.length > 0) { 
    ElMessage.error({ 
      message: "<span class='error-icon'>❌</span> 部署阻断：核心变量槽缺失，请修复！", 
      grouping: true, 
      duration: 3000,
      customClass: 'friendly-error-message'
    }); return; 
  }
  isDeploying.value = true
  try {
    const formData = new FormData(); formData.append('key', currentKey.value); formData.append('content', editBuffer.value);
    await axios.post("/api/script/prompts/update", formData);
    ElMessage.success("🚀 部署成功！");
    localStorage.removeItem(`prompt_draft_${currentKey.value}`); saveStatus.value = "已与云端同步";
  } catch (err) { 
    ElMessage.error({ 
      message: "<span class='error-icon'>❌</span> 部署失败，请检查网络连接或后端服务是否正常！", 
      grouping: true, 
      duration: 3000,
      customClass: 'friendly-error-message'
    }); 
  } finally { isDeploying.value = false }
}

const handleReset = () => {
  ElMessageBox.confirm('是否还原？草稿会丢失！', '还原确认', { type: 'warning' })
  .then(async () => {
    await axios.post(`/api/script/prompts/reset/${currentKey.value}`);
    localStorage.removeItem(`prompt_draft_${currentKey.value}`); loadPrompt();
  }).catch(() => {})
}

const copyOfficial = () => { navigator.clipboard.writeText(officialPrompt.value); ElMessage.success("已复制官方配置"); }
const copyToClipboard = () => { navigator.clipboard.writeText(editBuffer.value); ElMessage.success("已复制当前编辑区内容"); }





// 倒计时定时器引用
let countdownInterval = null;

// 动态计算预计等待时间
const calculateEstimatedTime = () => {
  // 检查是否在Mock模式下
  const mockMode = isMockMode(config);
  
  if (mockMode) {
    // Mock模式下，等待时间较短
    return 1;
  } else {
    // 非Mock模式下，根据输入长度计算等待时间
    const inputLength = Object.values(testInputs.value).reduce((total, val) => total + (val ? val.length : 0), 0);
    // 每1000个字符预计等待1秒，最少3秒，最多30秒
    return Math.min(Math.max(3, Math.ceil(inputLength / 1000)), 30);
  }
};

// 测试提示词
const testPrompt = () => {
  // 验证API Key
  if (!validateApiKey()) return;
  // 检查是否在Mock模式下
  const mockMode = isMockMode(config);
  
  if (mockMode) {
    // Mock模式下，等待时间较短
    return 1;
  }
  
  // 非Mock模式下，根据内容长度计算
  // 获取输入内容长度
  const contentLength = (editBuffer.value || '').length;
  const officialLength = (officialPrompt.value || '').length;
  const totalLength = contentLength + officialLength;
  
  // 根据内容长度计算预计等待时间（秒）
  // 基础时间 2 秒，每 1000 个字符增加 1 秒，最多 15 秒
  let estimatedTime = 2 + Math.min(Math.floor(totalLength / 1000), 13);
  
  // 确保至少 3 秒，最多 15 秒
  estimatedTime = Math.max(3, Math.min(estimatedTime, 15));
  
  return estimatedTime;
};



const runABTest = () => {
  // 验证API Key
  if (!validateApiKey()) return;
  if (missingVars.value.length > 0) { 
    ElMessage.error({ 
      message: "<span class='error-icon'>❌</span> 缺失核心变量槽，无法测试！", 
      grouping: true, 
      duration: 3000,
      customClass: 'friendly-error-message'
    }); return; 
  }
  
  // 验证沙盒变量是否都已填写
  const emptyVars = officialVars.value.filter(v => !testInputs.value[v] || testInputs.value[v].trim() === '');
  if (emptyVars.length > 0) {
    ElMessage.error({
      message: '请填写所有沙盒变量：' + emptyVars.join(', '),
      grouping: true,
      duration: 3000
    }); return;
  }
  
  isTesting.value = true; 
  
  // 动态计算预计等待时间
  const estimatedTime = calculateEstimatedTime();
  let countdown = estimatedTime;
  
  // 显示初始提示
  testResults.value = { 
    official: `<span class="rocket-spin">🚀</span> 正在准备发射... 预计等待 ${estimatedTime} 秒`, 
    draft: `<span class="rocket-spin">🚀</span> 正在准备发射... 预计等待 ${estimatedTime} 秒` 
  }; 
  currentTaskId.value = `test_${Date.now()}`;
  
  // 倒计时功能
  countdownInterval = setInterval(() => {
    countdown--;
    if (countdown > 0) {
      testResults.value = { 
        official: `<span class="rocket-spin">🚀</span> 正在准备发射... 预计等待 ${countdown} 秒`, 
        draft: `<span class="rocket-spin">🚀</span> 正在准备发射... 预计等待 ${countdown} 秒` 
      };
    } else {
      clearInterval(countdownInterval);
    }
  }, 1000);
  
  // 存储流式输出的临时数据
  let officialBuffer = '';
  let draftBuffer = '';
  
  // 节流处理的更新函数
  const updateOfficialResult = throttle((content) => {
    testResults.value.official = content;
  }, 100); // 每100ms更新一次
  
  const updateDraftResult = throttle((content) => {
    testResults.value.draft = content;
  }, 100); // 每100ms更新一次
  
  // 添加等待时间，显示火箭图标和等待提示
  setTimeout(() => {
    clearInterval(countdownInterval);
    let offC = officialPrompt.value || ''; let draC = editBuffer.value || '';
    Object.keys(testInputs.value).forEach(k => { const val = String(testInputs.value[k] || ''); offC = offC.split(`{${k}}`).join(val); draC = draC.split(`{${k}}`).join(val); })
    let doneCount = 0; const checkDone = () => { doneCount++; if (doneCount >= 2) isTesting.value = false }
    
    // 更新提示信息
    testResults.value = { 
      official: '<span class="rocket-spin">🚀</span> 火箭发射中...', 
      draft: '<span class="rocket-spin">🚀</span> 火箭发射中...' 
    };
    
    engine.fetchStream('script/prompts/test_stream', { system_prompt: "原版", user_prompt: offC, task_id: currentTaskId.value }, 
      (chunk) => { 
        if (testResults.value.official.includes('火箭发射中')) {
          officialBuffer = '';
        }
        officialBuffer += chunk;
        updateOfficialResult(officialBuffer);
      }, 
      () => checkDone(), 
      checkDone, 
      checkDone
    )
    engine.fetchStream('script/prompts/test_stream', { system_prompt: "调优版", user_prompt: draC, task_id: currentTaskId.value }, 
      (chunk) => { 
        if (testResults.value.draft.includes('火箭发射中')) {
          draftBuffer = '';
        }
        draftBuffer += chunk;
        updateDraftResult(draftBuffer);
      }, 
      () => checkDone(), 
      checkDone, 
      checkDone
    )
  }, estimatedTime * 1000); // 预计等待时间
}

const stopTest = () => { 
  if(currentTaskId.value) engine.stopTask(currentTaskId.value); 
  isTesting.value = false; 
  testResults.value = { official: "", draft: "" }; 
  // 清除倒计时定时器
  if (countdownInterval) {
    clearInterval(countdownInterval);
    countdownInterval = null;
  }
  ElMessage.warning('🚨 已触发全局熔断机制') 
}
onMounted(() => loadPrompt())
</script>

<style scoped>
/* ================= 核心手感增强样式 ================= */
.modern-studio-container { display: flex; height: calc(100vh - 110px); background: #f3f4f6; gap: 20px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

/* 必填变量补全栏标签 */
.var-clickable-badge { cursor: pointer; transition: transform 0.2s, background 0.3s; margin-right: 8px; border: 1px solid #e5e7eb; background: #fff7ed; color: #ea580c; font-weight: 600; font-family: monospace; }
.var-clickable-badge:hover { transform: translateY(-2px); background: #ffedd5; box-shadow: 0 4px 8px rgba(227,112,13,0.1); }
.var-clickable-badge.is-missing { background: #fef2f2; color: #ef4444; border-color: #fecaca; text-decoration: line-through; }

/* ================= 沙盒数据注入文本框样式 (保留您的自定义) ================= */
.var-input-group { margin-bottom: 16px; }
.var-input-group .el-input { width: 100%; }
.var-input-group .el-textarea__inner {
  resize: vertical;
  font-family: 'Courier New', Courier, monospace;
  line-height: 1.5;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  background: #f9fafb;
}
.var-input-group .el-textarea__inner:focus {
  border-color: #e3700d;
  box-shadow: 0 0 0 3px rgba(227, 112, 13, 0.1);
  background: #ffffff;
}
.var-input-group .el-textarea .el-textarea__wrap { border-radius: 8px; }

/* 沙盒输入框滚动条样式 */
.var-input-group .el-textarea__inner::-webkit-scrollbar { width: 8px; height: 8px; }
.var-input-group .el-textarea__inner::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 4px; }
.var-input-group .el-textarea__inner::-webkit-scrollbar-thumb { background: #c1c1c1; border-radius: 4px; }
.var-input-group .el-textarea__inner::-webkit-scrollbar-thumb:hover { background: #a1a1a1; }



/* 脚本阅读器样式 */
.script-reader {
  font-family: 'Courier New', Courier, monospace;
  line-height: 1.6;
  white-space: pre-wrap;
  color: #374151;
}

.script-reader h1,
.script-reader h2,
.script-reader h3 {
  margin-top: 24px;
  margin-bottom: 16px;
  color: #111827;
}

.script-reader p {
  margin-bottom: 12px;
}

/* 工具按钮样式 */
.tools-right {
  display: flex;
  gap: 8px;
}

.tool-btn {
  color: #6b7280;
  transition: color 0.3s ease;
}

.tool-btn:hover {
  color: #e3700d;
}

/* ================= 侧边栏 ================= */
.modern-sidebar { width: 280px; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); display: flex; flex-direction: column; overflow: hidden; border: 1px solid #e5e7eb; }
.sidebar-brand { padding: 24px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #f3f4f6; }
.brand-icon { width: 40px; height: 40px; background: linear-gradient(135deg, #e3700d, #f59e0b); border-radius: 10px; color: white; font-size: 24px; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 10px rgba(227, 112, 13, 0.3); }
.brand-text h2 { margin: 0; font-size: 1.1rem; color: #111827; }
.brand-text span { font-size: 0.8rem; color: #6b7280; }

.asset-nav { flex: 1; padding: 20px 12px; overflow-y: auto; }
.nav-label { font-size: 0.75rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; margin-bottom: 12px; padding-left: 8px; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin-bottom: 8px; border-radius: 12px; cursor: pointer; transition: all 0.2s ease; position: relative; }
.nav-item:hover { background: #f9fafb; }
.nav-item.active { background: #fff7ed; }
.nav-icon { font-size: 20px; color: #6b7280; }
.nav-item.active .nav-icon { color: #e3700d; }
.nav-info { display: flex; flex-direction: column; }
.nav-info .title { font-size: 0.95rem; font-weight: 600; color: #374151; }
.nav-info .subtitle { font-size: 0.7rem; color: #9ca3af; font-family: monospace; }
.nav-item.active .title { color: #e3700d; }
.active-indicator { position: absolute; right: 12px; width: 6px; height: 6px; border-radius: 50%; background: #e3700d; box-shadow: 0 0 8px #e3700d; }

.sidebar-actions { padding: 20px; border-top: 1px solid #f3f4f6; display: flex; flex-direction: column; gap: 12px; }
.action-btn { height: 44px; border-radius: 10px; font-weight: 600; font-size: 0.95rem; margin: 0 !important; }
.action-btn.deploy { background: #e3700d; color: white; border: none; transition: all 0.3s; }
.action-btn.deploy:hover { background: #ea580c; box-shadow: 0 4px 12px rgba(227, 112, 13, 0.2); transform: translateY(-1px); }
.action-btn.deploy:disabled { background: #9ca3af !important; box-shadow: none; cursor: not-allowed; transform: none; }
.action-btn.reset { color: #6b7280; border-color: #d1d5db; }

/* ================= 主工作区顶部 ================= */
.modern-main { flex: 1; display: flex; flex-direction: column; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); border: 1px solid #e5e7eb; overflow: hidden; }

.main-topbar { padding: 20px 30px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center; }
.current-module-info { display: flex; align-items: center; gap: 12px; }
.pulse-ring { width: 10px; height: 10px; background: #10b981; border-radius: 50%; box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2); transition: background 0.3s;}
.pulse-ring.error-ring { background: #ef4444; box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2); animation: pulse-error 1s infinite; }
.current-module-info h3 { margin: 0; font-size: 1.2rem; color: #111827; }

.glass-tabs { display: flex; background: #f3f4f6; padding: 4px; border-radius: 12px; }
.glass-tabs button { border: none; background: transparent; padding: 8px 20px; border-radius: 8px; font-size: 0.9rem; font-weight: 600; color: #6b7280; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.3s; }
.glass-tabs button:hover { color: #374151; }
.glass-tabs button.active { background: #ffffff; color: #e3700d; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

.workspace-area { flex: 1; overflow: hidden; padding: 24px 30px; display: flex; flex-direction: column; background: #fafaf9; }
.workspace-panel { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

/* ================= 创作模式 (Edit) ================= */
.editor-tools { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-radius: 8px; transition: all 0.3s;}
.editor-tools.has-error { padding: 10px; background: #fef2f2; border: 1px solid #fecaca; }

.detected-vars { font-size: 0.85rem; color: #6b7280; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;}
.error-msg { color: #ef4444; font-weight: bold; display: flex; align-items: center; gap: 4px; margin-left: 8px;}
.fullscreen-btn { border-radius: 8px; color: #4b5563; }

.tools-right { display: flex; align-items: center; gap: 16px; }
.save-status { font-size: 0.8rem; color: #9ca3af; display: flex; align-items: center; gap: 6px; }
.save-status.is-saved { color: #10b981; }
.save-status.is-error { color: #ef4444; font-weight: bold; }

/* 代码编辑器 MAC 风格外壳 */
.mac-ide-wrapper { flex: 1; display: flex; flex-direction: column; background: #1e1e1e; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.15); border: 1px solid #374151; transition: border-color 0.3s; }
.mac-ide-wrapper.error-border { border-color: #ef4444; box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2); }
.mac-header { height: 40px; background: #2d2d2d; display: flex; align-items: center; padding: 0 16px; position: relative; border-bottom: 1px solid #111; }
.traffic-lights { display: flex; gap: 8px; }
.light { width: 12px; height: 12px; border-radius: 50%; }
.light.red { background: #ff5f56; } .light.yellow { background: #ffbd2e; } .light.green { background: #27c93f; }
.filename { position: absolute; left: 50%; transform: translateX(-50%); color: #9ca3af; font-family: monospace; font-size: 0.85rem; }
.copy-action { margin-left: auto; color: #9ca3af; cursor: pointer; transition: color 0.2s; }
.copy-action:hover { color: #fff; }

.ide-body { flex: 1; display: flex; overflow: hidden; }
.line-numbers { width: 48px; background: #1e1e1e; border-right: 1px solid #333; padding: 16px 0; text-align: center; color: #6b7280; font-family: 'Fira Code', 'Consolas', monospace; font-size: 14px; line-height: 1.6; overflow: hidden; user-select: none; }
.code-input { flex: 1; background: transparent; border: none; outline: none; padding: 16px; color: #e5e7eb; font-family: 'Fira Code', 'Consolas', monospace; font-size: 14px; line-height: 1.6; resize: none; white-space: pre; overflow: auto; }
.code-input::placeholder { color: #4b5563; }

/* 官方出厂设定折叠面板 */
.ref-collapse { border: none; background: transparent; margin-top: 15px; }
:deep(.el-collapse-item__header) { background: transparent; border: none; font-weight: 600; color: #4b5563; }
:deep(.el-collapse-item__wrap) { border: none; background: transparent; }
.ref-toolbar { display: flex; justify-content: flex-end; gap: 16px; margin-bottom: 8px; padding-right: 4px;}
.readonly-bg { background: #f3f4f6; padding: 16px; border-radius: 8px; color: #4b5563; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; overflow-y: auto; max-height: 150px; border: 1px solid #e5e7eb; }
.readonly-fullscreen { color: #9ca3af !important; cursor: text; }

/* ================= 差异比对模式 (Diff) ================= */
.diff-header-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #374151; padding-bottom: 12px; }
.diff-legend { display: flex; gap: 12px; font-size: 0.85rem; font-weight: 600; align-items: center;}
.legend-item.removed { color: #ff7b72; } .legend-item.added { color: #7ee787; }
.diff-legend .sign { display: inline-block; width: 18px; text-align: center; background: rgba(255,255,255,0.1); border-radius: 4px; margin-right: 4px; }
.diff-code-box { flex: 1; background: #1e1e1e; border-radius: 12px; border: 1px solid #374151; overflow: auto; font-family: 'Fira Code', monospace; font-size: 13px; line-height: 1.6; padding: 10px 0; }
:deep(.diff-row) { display: flex; padding: 2px 16px; word-break: break-all; white-space: pre-wrap; }
:deep(.diff-num) { width: 30px; flex-shrink: 0; text-align: right; padding-right: 12px; user-select: none; color: #6b7280; }
:deep(.diff-content) { flex: 1; margin-left: 12px; }
:deep(.diff-row.removed) { background-color: rgba(248, 81, 73, 0.15); }
:deep(.diff-row.removed .diff-num), :deep(.diff-row.removed .diff-content) { color: #ff7b72; text-decoration: line-through; }
:deep(.diff-row.added) { background-color: rgba(46, 160, 67, 0.15); }
:deep(.diff-row.added .diff-num), :deep(.diff-row.added .diff-content) { color: #7ee787; }
:deep(.diff-row.unchanged:hover) { background-color: rgba(255,255,255,0.05); }
:deep(.diff-row.unchanged .diff-content) { color: #8b949e; }
:deep(.inline-removed) { background-color: rgba(248, 81, 73, 0.2); padding: 0 2px; border-radius: 2px; color: #ff7b72; text-decoration: line-through; }
:deep(.inline-added) { background-color: rgba(46, 160, 67, 0.2); padding: 0 2px; border-radius: 2px; color: #7ee787; }

/* ================= A/B 实验室模式 (Playground) ================= */
.playground-panel { flex-direction: row; gap: 24px; }
.pg-sidebar { width: 320px; display: flex; flex-direction: column; background: #ffffff; border-radius: 16px; padding: 24px; border: 1px solid #e5e7eb; box-shadow: 0 4px 20px rgba(0,0,0,0.02); }
.pg-sidebar h4 { margin: 0 0 20px 0; display: flex; align-items: center; gap: 8px; color: #111827; }
.var-list { flex: 1; overflow-y: auto; padding-right: 8px; }

.var-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;}
.var-header label { font-size: 0.85rem; font-weight: 700; color: #e3700d; font-family: monospace; display: flex; flex-direction: column;}
.cn-name { font-size: 0.75rem; color: #6b7280; font-family: 'PingFang SC', sans-serif; font-weight: normal; margin-top: 2px;}

:deep(.import-upload .el-upload) { width: 100%; text-align: right; }

.action-footer { margin-top: 24px; padding-top: 20px; border-top: 1px solid #e5e7eb; }
.battle-btn { height: 44px; border-radius: 10px; font-weight: bold; background: #e3700d; color: white; border: none; transition: all 0.3s; box-shadow: 0 4px 12px rgba(227, 112, 13, 0.2); width: 100%; }
.battle-btn:hover:not(:disabled) { background: #ea580c; box-shadow: 0 6px 16px rgba(227, 112, 13, 0.3); transform: translateY(-1px); }
.battle-btn:disabled { background: #9ca3af !important; cursor: not-allowed; box-shadow: none; transform: none; }
.battle-btn.el-button--danger { background: #ef4444; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2); }
.battle-btn.el-button--danger:hover { background: #dc2626; }

/* 实验室双屏监视器 (高定风) */
.pg-screens { flex: 1; display: flex; gap: 24px; overflow: hidden; }
.mock-screen { flex: 1; display: flex; flex-direction: column; background: #ffffff; border-radius: 16px; border: 1px solid #e5e7eb; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.02); transition: all 0.3s; }
.mock-screen.active-monitor { border-color: #e3700d; box-shadow: 0 8px 30px rgba(227, 112, 13, 0.1); }

.screen-head { padding: 14px 20px; background: #F8F9FA; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e5e7eb; }
.screen-head.glow { background: rgba(227, 112, 13, 0.05); border-bottom-color: rgba(227, 112, 13, 0.2); }
.title-left { font-size: 14px; font-weight: 700; color: #374151; display: flex; align-items: center; gap: 8px; }
.glow .title-left { color: #e3700d; }

.live-dot { width: 8px; height: 8px; background: #ef4444; border-radius: 50%; animation: pulse-red 1.5s infinite; }
.tools-right { display: flex; gap: 8px; }
.tool-btn { color: #9ca3af !important; font-size: 16px; padding: 4px; transition: all 0.2s; }
.tool-btn:hover { color: #e3700d !important; background: white; border-radius: 6px; }

.screen-content { flex: 1; padding: 24px; overflow-y: auto; background: white; }
.script-reader { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; font-size: 14px; line-height: 1.8; color: #2C3E50; white-space: pre-wrap; }

/* ================= 沉浸式弹窗阅读器 (导出与全屏) ================= */
.hermes-dialog :deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
.hermes-dialog :deep(.el-dialog__header) { background: #F8F9FA; border-bottom: 1px solid #e5e7eb; margin: 0; padding: 20px 24px; font-weight: bold; color: #111827; }
.full-text-reader { padding: 24px; font-size: 15px; line-height: 1.8; color: #2C3E50; font-family: 'Microsoft YaHei', sans-serif; max-height: 65vh; overflow-y: auto; background: #FAFAFA; border-radius: 12px; border: 1px solid #e5e7eb; }
.dialog-footer-actions { display: flex; justify-content: flex-end; gap: 16px; padding-top: 10px; }

/* ================= 工具动画与杂项 ================= */
.pulse-dot { width: 6px; height: 6px; background: #fbbf24; border-radius: 50%; animation: pulse 1s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
@keyframes pulse-error { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
@keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 70% { box-shadow: 0 0 0 6px rgba(239,68,68,0); } 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); } }

.blink { animation: flash 1.5s infinite; }
@keyframes flash { 0% {opacity: 1;} 50% {opacity: 0.5;} 100% {opacity: 1;} }
.rocket-spin { display: inline-block; animation: spin 2s linear infinite; font-size: 24px; margin-right: 8px; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.friendly-error-message { border-radius: 8px !important; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2) !important; padding: 12px 16px !important; }
.friendly-error-message .error-icon { margin-right: 8px; font-size: 16px; }
.friendly-error-message .el-message__content { font-size: 14px; line-height: 1.5; }

/* ================= 专注模式弹窗 (Zen Mode) ================= */
:deep(.zen-dialog .el-dialog__header) { display: none; }
:deep(.zen-dialog .el-dialog__body) { padding: 0; height: 100vh; display: flex; flex-direction: column; background: #111827; }
.zen-toolbar { padding: 16px 24px; background: #1f2937; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #374151; }
.zen-title { color: #f3f4f6; font-size: 1.2rem; font-weight: 600; display: flex; align-items: center; gap: 12px; }
.zen-ide { border-radius: 0; border: none; box-shadow: none; background: #111827; transition: border 0.3s;}
.zen-ide.error-border { border: 2px solid #ef4444; }
.zen-ide .mac-header { display: none; } 
.zen-ide .line-numbers { background: #111827; border-color: #374151; }

/* ================= 专注差异模式 (Diff Zen) ================= */
:deep(.diff-zen-dialog .el-dialog__body) { background: #0d1117; }
.zen-diff-box { background: #0d1117 !important; border: none !important; border-radius: 0 !important; color: #c9d1d9; }
:deep(.diff-zen-dialog .diff-row.removed) { background-color: rgba(248, 81, 73, 0.15); }
:deep(.diff-zen-dialog .diff-row.removed .diff-num), :deep(.diff-zen-dialog .diff-row.removed .diff-content) { color: #ff7b72; }
:deep(.diff-zen-dialog .diff-row.added) { background-color: rgba(46, 160, 67, 0.15); }
:deep(.diff-zen-dialog .diff-row.added .diff-num), :deep(.diff-zen-dialog .diff-row.added .diff-content) { color: #7ee787; }
:deep(.diff-zen-dialog .diff-row.unchanged:hover) { background-color: rgba(255,255,255,0.05); }
:deep(.diff-zen-dialog .diff-row.unchanged .diff-content) { color: #8b949e; }
</style>