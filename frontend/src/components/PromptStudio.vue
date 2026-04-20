<template>
  <div class="studio-shell fade-in">
    <aside class="studio-sidebar">
      <div class="sidebar-brand">
        <div class="brand-mark"><el-icon><Cpu /></el-icon></div>
        <div>
          <h2>提示词工坊</h2>
          <p>围绕策略流、三幕式与分镜约束的双屏调优台</p>
        </div>
      </div>

      <div class="sidebar-section">
        <div class="section-label">核心资产</div>
        <button
          v-for="(label, key) in assetMap"
          :key="key"
          class="asset-card"
          :class="{ active: currentKey === key }"
          @click="switchAsset(key)"
        >
          <el-icon class="asset-icon"><component :is="getIcon(key)" /></el-icon>
          <span class="asset-copy">
            <strong>{{ label }}</strong>
            <small>{{ assetMeta[key].short }}</small>
          </span>
          <span class="asset-chip">{{ assetMeta[key].type }}</span>
        </button>
      </div>

      <div class="sidebar-summary">
        <div class="summary-row">
          <span>当前模式</span>
          <strong>{{ playgroundMeta.mode }}</strong>
        </div>
        <div class="summary-row">
          <span>输出形态</span>
          <strong>{{ playgroundMeta.output }}</strong>
        </div>
        <div class="summary-row">
          <span>缺失变量</span>
          <strong :class="{ danger: missingVars.length > 0 }">{{ missingVars.length }}</strong>
        </div>
      </div>

      <div class="sidebar-actions">
        <el-tooltip :disabled="missingVars.length === 0" content="请先补齐必需变量后再部署" placement="top">
          <el-button class="action-btn primary" @click="handleDeploy" :loading="isDeploying" :disabled="missingVars.length > 0">
            <el-icon><UploadFilled /></el-icon> 部署到生产
          </el-button>
        </el-tooltip>
        <el-button class="action-btn" plain @click="handleReset">
          <el-icon><RefreshLeft /></el-icon> 恢复官方版本
        </el-button>
      </div>
    </aside>

    <main class="studio-main">
      <header class="studio-header">
        <div class="header-copy">
          <span class="status-dot" :class="{ danger: missingVars.length > 0 }"></span>
          <div>
            <h3>{{ assetMap[currentKey] }}</h3>
            <p>{{ assetMeta[currentKey].description }}</p>
          </div>
        </div>

        <div class="studio-tabs">
          <button :class="{ active: activeTab === 'Edit' }" @click="activeTab = 'Edit'">
            <el-icon><EditPen /></el-icon> 创作台
          </button>
          <button :class="{ active: activeTab === 'Diff' }" @click="activeTab = 'Diff'">
            <el-icon><Connection /></el-icon> 版本审查
          </button>
          <button :class="{ active: activeTab === 'Playground' }" @click="activeTab = 'Playground'">
            <el-icon><DataAnalysis /></el-icon> 提示词工坊
          </button>
        </div>
      </header>

      <section class="studio-workspace">
        <div v-show="activeTab === 'Edit'" class="workspace-panel edit-panel">
          <div class="editor-banner" :class="{ warning: missingVars.length > 0 }">
            <div class="editor-vars">
              <el-icon><MagicStick /></el-icon>
              <span>必备变量</span>
              <el-tag
                v-for="v in officialVars"
                :key="v"
                class="var-badge"
                :class="{ missing: missingVars.includes(v) }"
                @click="insertVar(v)"
              >
                {{ getFriendlyVarName(v) }} {{ formatVarToken(v) }}
              </el-tag>
            </div>

            <div class="editor-actions-inline">
              <span class="save-status" :class="{ ok: missingVars.length === 0, danger: missingVars.length > 0 }">
                <el-icon v-if="missingVars.length === 0"><CircleCheck /></el-icon>
                <el-icon v-else><CircleClose /></el-icon>
                {{ missingVars.length > 0 ? '变量缺失，请先修复' : saveStatus }}
              </span>
              <el-button class="fullscreen-btn" plain size="small" @click="isFullscreen = true">
                <el-icon><FullScreen /></el-icon> 全屏专注编写
              </el-button>
            </div>
          </div>

          <div class="editor-shell" :class="{ warning: missingVars.length > 0 }">
            <div class="editor-shell-head">
              <div class="traffic-lights">
                <span class="red"></span>
                <span class="yellow"></span>
                <span class="green"></span>
              </div>
              <div class="editor-file">{{ currentKey.toLowerCase() }}.prompt</div>
              <button class="ghost-icon" @click="copyToClipboard">
                <el-icon><CopyDocument /></el-icon>
              </button>
            </div>

            <div class="editor-shell-body">
              <div class="line-numbers" ref="lineNumbersRef">
                <div v-for="n in lineCount" :key="n">{{ n }}</div>
              </div>
              <textarea
                ref="textareaRef"
                v-model="editBuffer"
                class="code-input"
                wrap="off"
                spellcheck="false"
                placeholder="在这里编写提示词逻辑..."
                @scroll="syncScroll"
                @keydown.tab.prevent="handleTab"
              ></textarea>
            </div>
          </div>

          <el-collapse class="reference-panel">
            <el-collapse-item name="official">
              <template #title>
                <div class="collapse-title"><el-icon><View /></el-icon> 参考官方版本</div>
              </template>
              <div class="reference-toolbar">
                <el-button link type="primary" @click="copyOfficial">
                  <el-icon><CopyDocument /></el-icon> 复制
                </el-button>
                <el-button link type="primary" @click="isOfficialFullscreen = true">
                  <el-icon><FullScreen /></el-icon> 全屏查看
                </el-button>
              </div>
              <pre class="reference-content">{{ officialPrompt }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div v-show="activeTab === 'Diff'" class="workspace-panel diff-panel">
          <div class="diff-toolbar">
            <div class="diff-legend">
              <span class="removed">- 官方删除内容</span>
              <span class="added">+ 当前新增内容</span>
              <span class="muted">深色高亮表示行内修改</span>
            </div>
            <el-button class="fullscreen-btn" plain size="small" @click="isDiffFullscreen = true">
              <el-icon><FullScreen /></el-icon> 全屏审查
            </el-button>
          </div>
          <div class="diff-stats">
            <div class="diff-stat-card">
              <span>官方行数</span>
              <strong>{{ diffStats.officialLines }}</strong>
            </div>
            <div class="diff-stat-card">
              <span>当前行数</span>
              <strong>{{ diffStats.draftLines }}</strong>
            </div>
            <div class="diff-stat-card added">
              <span>新增行</span>
              <strong>{{ diffStats.added }}</strong>
            </div>
            <div class="diff-stat-card removed">
              <span>删除行</span>
              <strong>{{ diffStats.removed }}</strong>
            </div>
          </div>
          <div class="diff-box" v-html="diffHtml"></div>
        </div>

        <div v-show="activeTab === 'Playground'" class="workspace-panel playground-panel">
          <div class="playground-top">
            <div class="playground-hero">
              <div class="hero-copy">
                <span class="hero-kicker">{{ playgroundMeta.mode }}</span>
                <h3>{{ playgroundMeta.title }}</h3>
              </div>
              <div class="hero-tags">
                <span class="hero-tag">{{ playgroundMeta.output }}</span>
                <span class="hero-tag">{{ playgroundMeta.exportLabel }}</span>
                <span class="hero-tag">{{ officialVars.length }} 项输入</span>
              </div>
            </div>

            <div class="playground-actions">
              <el-button class="battle-btn" @click="runABTest" :loading="isTesting" v-if="!isTesting" :disabled="!canStartABTest">
                <el-icon><Lightning /></el-icon> {{ playgroundMeta.action }}
              </el-button>
              <el-button class="battle-btn stop" @click="stopTest" v-else>
                <el-icon><VideoPause /></el-icon> 停止双屏演练
              </el-button>
            </div>
          </div>

          <div v-if="isTesting" class="testing-banner">
            <div class="testing-banner-left">
              <span class="loading-orb"></span>
              <div>
                <strong>双屏演练进行中</strong>
              </div>
            </div>
            <div class="testing-banner-right">
              <div class="time-chip">
                <span>预计</span>
                <strong>{{ estimatedTimeLabel }}</strong>
              </div>
              <div class="time-chip">
                <span>已运行</span>
                <strong>{{ elapsedTimeLabel }}</strong>
              </div>
              <div class="time-chip">
                <span>剩余参考</span>
                <strong>{{ remainingTimeLabel }}</strong>
              </div>
            </div>
            <div class="progress-track">
              <div class="progress-bar" :style="{ width: `${testProgressPercent}%` }"></div>
            </div>
          </div>

          <div class="playground-grid">
            <section class="sandbox-panel">
              <div class="panel-head">
                <div>
                  <span class="panel-kicker">Sandbox</span>
                  <h4>沙盒数据注入</h4>
                </div>
                <div class="sandbox-status" :class="{ warning: requiresApiKey && !apiKeyReady }">
                  <span>{{ requiresApiKey && !apiKeyReady ? '待配置 API Key' : isTesting ? '演练中' : '就绪' }}</span>
                </div>
              </div>

              <div class="input-list">
                <div v-for="v in officialVars" :key="v" class="input-card">
                  <div class="input-card-head">
                    <div>
                      <div class="input-name">{{ getFriendlyVarName(v) }}</div>
                      <div class="input-key">{{ formatVarToken(v) }}</div>
                    </div>
                    <div class="input-tools">
                      <el-button v-if="testInputs[v]" link type="danger" @click="testInputs[v] = ''">
                        <el-icon><CircleClose /></el-icon> 清空
                      </el-button>

                      <el-upload
                        v-if="supportsExcelImport(v)"
                        action=""
                        :auto-upload="false"
                        :show-file-list="false"
                        :on-change="(file) => handleImportFile(file, v)"
                        accept=".xlsx,.xls,.csv"
                      >
                        <el-button link type="primary">
                          <el-icon><DocumentAdd /></el-icon> 导入 Excel
                        </el-button>
                      </el-upload>

                      <el-upload
                        v-if="supportsWordImport(v)"
                        action=""
                        :auto-upload="false"
                        :show-file-list="false"
                        :on-change="(file) => handleImportFile(file, v)"
                        accept=".docx,.txt"
                      >
                        <el-button link type="primary">
                          <el-icon><DocumentAdd /></el-icon> 导入 Word/TXT
                        </el-button>
                      </el-upload>
                    </div>
                  </div>

                  <el-input
                    v-model="testInputs[v]"
                    :type="isLongField(v) ? 'textarea' : 'text'"
                    :rows="isLongField(v) ? 6 : 1"
                    :autosize="isLongField(v) ? { minRows: 6, maxRows: 14 } : false"
                    :placeholder="getInputPlaceholder(v)"
                  />
                </div>
              </div>
            </section>

            <section class="compare-panel">
              <div class="compare-toolbar">
                <div class="compare-mode">{{ playgroundMeta.mode }}</div>
                <div class="compare-export">{{ playgroundMeta.exportLabel }}</div>
              </div>

              <div class="screen-wall">
                <article class="screen-card">
                  <header class="screen-head">
                    <div>
                      <span class="screen-badge">A 屏</span>
                      <h5>官方原版</h5>
                    </div>
                    <div class="screen-tools">
                      <el-button link class="tool-btn" @click="copyContent(testResults.official)">
                        <el-icon><CopyDocument /></el-icon>
                      </el-button>
                      <el-button
                        link
                        class="tool-btn"
                        @click="handleExportResult('official')"
                        :disabled="!hasEffectiveContent(testResults.official)"
                      >
                        <el-icon><Download /></el-icon>
                      </el-button>
                      <el-button
                        link
                        class="tool-btn"
                        @click="openResultFullscreen('official', testResults.official)"
                        :disabled="!hasEffectiveContent(testResults.official)"
                      >
                        <el-icon><FullScreen /></el-icon>
                      </el-button>
                      <el-button link class="tool-btn" @click="openReader('官方原版', testResults.official)">
                        <el-icon><FullScreen /></el-icon>
                      </el-button>
                    </div>
                  </header>
                  <div class="screen-body">
                    <pre class="screen-text">{{ getDisplayContent(testResults.official) }}</pre>
                  </div>
                </article>

                <article class="screen-card active">
                  <header class="screen-head glow">
                    <div>
                      <span class="screen-badge live">B 屏</span>
                      <h5>当前调优版</h5>
                    </div>
                    <div class="screen-tools">
                      <el-button link class="tool-btn" @click="copyContent(testResults.draft)">
                        <el-icon><CopyDocument /></el-icon>
                      </el-button>
                      <el-button
                        link
                        class="tool-btn"
                        @click="handleExportResult('draft')"
                        :disabled="!hasEffectiveContent(testResults.draft)"
                      >
                        <el-icon><Download /></el-icon>
                      </el-button>
                      <el-button
                        link
                        class="tool-btn"
                        @click="openResultFullscreen('draft', testResults.draft)"
                        :disabled="!hasEffectiveContent(testResults.draft)"
                      >
                        <el-icon><FullScreen /></el-icon>
                      </el-button>
                      <el-button link class="tool-btn" @click="openReader('当前调优版', testResults.draft)">
                        <el-icon><FullScreen /></el-icon>
                      </el-button>
                    </div>
                  </header>
                  <div class="screen-body">
                    <pre class="screen-text">{{ getDisplayContent(testResults.draft) }}</pre>
                  </div>
                </article>
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>

    <el-dialog v-model="isFullscreen" fullscreen :show-close="false" class="zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title">
          <el-icon><EditPen /></el-icon> 专注模式 - {{ assetMap[currentKey] }}
        </div>
        <el-button type="danger" plain @click="isFullscreen = false">退出专注模式</el-button>
      </div>
      <div class="editor-shell zen-editor" :class="{ warning: missingVars.length > 0 }">
        <div class="editor-shell-body">
          <div class="line-numbers" ref="zenLineNumbersRef">
            <div v-for="n in lineCount" :key="n">{{ n }}</div>
          </div>
          <textarea v-model="editBuffer" class="code-input" wrap="off" spellcheck="false" @scroll="syncZenScroll"></textarea>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="isOfficialFullscreen" fullscreen :show-close="false" class="zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title"><el-icon><View /></el-icon> 官方版本只读查看</div>
        <div class="zen-toolbar-actions">
          <el-button type="primary" plain @click="copyOfficial">
            <el-icon><CopyDocument /></el-icon> 复制内容
          </el-button>
          <el-button type="danger" plain @click="isOfficialFullscreen = false">关闭</el-button>
        </div>
      </div>
      <div class="editor-shell zen-editor">
        <div class="editor-shell-body">
          <textarea readonly :value="officialPrompt" class="code-input readonly-fullscreen" wrap="off" spellcheck="false"></textarea>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="isDiffFullscreen" fullscreen :show-close="false" class="zen-dialog diff-zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title"><el-icon><ZoomIn /></el-icon> 全屏版本审查</div>
        <el-button type="danger" plain @click="isDiffFullscreen = false">关闭</el-button>
      </div>
      <div class="diff-box zen-diff-box" v-html="diffHtml"></div>
    </el-dialog>

    <el-dialog v-model="readerVisible" :title="`沉浸阅读 - ${readerTitle}`" width="72%" center class="reader-dialog">
      <pre class="reader-content">{{ getDisplayContent(readerContent) }}</pre>
      <template #footer>
        <div class="dialog-footer-actions">
          <el-button @click="readerVisible = false" size="large">关闭</el-button>
          <el-button type="primary" class="export-btn" size="large" @click="handleReaderExport">
            <el-icon><Download /></el-icon> 导出
          </el-button>
        </div>
      </template>
    </el-dialog>
    <el-dialog v-model="resultFullscreenVisible" fullscreen :show-close="false" class="zen-dialog result-zen-dialog">
      <div class="zen-toolbar">
        <div class="zen-title"><el-icon><FullScreen /></el-icon> 结果全屏预览 - {{ resultFullscreenTitle }}</div>
        <div class="zen-toolbar-actions">
          <el-button type="primary" plain @click="copyContent(resultFullscreenContent)">
            <el-icon><CopyDocument /></el-icon> 复制内容
          </el-button>
          <el-button type="primary" plain @click="handleResultFullscreenExport">
            <el-icon><Download /></el-icon> 导出结果
          </el-button>
          <el-button type="danger" plain @click="resultFullscreenVisible = false">关闭</el-button>
        </div>
      </div>
      <div class="result-fullscreen-body">
        <pre class="result-fullscreen-text">{{ getDisplayContent(resultFullscreenContent) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, inject, nextTick } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { engine } from '../api/engine'
import { apiUrl } from '../api/base'
import * as XLSX from 'xlsx'
import JSZip from 'jszip'
import { throttle, isMockMode, createErrorMessage, retryAsync, isRetriableNetworkError } from '../utils'
import {
  Cpu,
  UploadFilled,
  RefreshLeft,
  EditPen,
  Connection,
  DataAnalysis,
  MagicStick,
  CircleCheck,
  CircleClose,
  FullScreen,
  CopyDocument,
  View,
  Setting,
  DocumentAdd,
  Lightning,
  VideoPause,
  Download,
  User,
  Reading,
  Memo,
  Collection,
  SetUp,
  ZoomIn
} from '@element-plus/icons-vue'

const config = inject('config', { provider: 'Mock (演示)' })

const assetMap = {
  SCRIPT_SYSTEM: '导演全局人设',
  OUTLINE_TASK: '小说大纲策略',
  BATCH_SCRIPT_PROMPT: '小说分镜约束',
  ACT_GEN_TASK: '剧本三幕式生成',
  SCRIPT_TASK_TEMPLATE: '剧本分镜约束'
}

const assetMeta = {
  SCRIPT_SYSTEM: {
    short: '系统级人物设定与语气基准',
    type: '基座',
    description: '用于定义创作总基调、人设边界与导演视角。',
  },
  OUTLINE_TASK: {
    short: '大纲策略双屏流式对打',
    type: '流式',
    description: '用沙盒小说数据注入后，比较官方版与调优版的大纲策略产出。'
  },
  BATCH_SCRIPT_PROMPT: {
    short: 'Excel 注入的分镜约束对比',
    type: '分镜',
    description: '上传小说/约束数据后，双屏对比分镜脚本格式输出。'
  },
  ACT_GEN_TASK: {
    short: '三幕式生成流式演练',
    type: '流式',
    description: '围绕原始创意进行三幕式结构生成，适合策略版与调优版并排校验。'
  },
  SCRIPT_TASK_TEMPLATE: {
    short: '剧本大纲驱动的分镜约束',
    type: '分镜',
    description: '导入 Word/TXT 大纲或文本，输出更长篇的分镜脚本结构。'
  }
}

const friendlyVarMap = {
  start_ep: '起始集数',
  end_ep: '结束集数',
  total_episodes: '总集数',
  content: '内容源文',
  user_choice: '用户输入',
  outline: '分集大纲',
  episode_range: '集数范围',
  original_idea: '原始创意'
}

const streamPromptKeys = ['OUTLINE_TASK', 'ACT_GEN_TASK']
const storyboardPromptKeys = ['BATCH_SCRIPT_PROMPT', 'SCRIPT_TASK_TEMPLATE']

const currentKey = ref('BATCH_SCRIPT_PROMPT')
const activeTab = ref('Edit')
const editBuffer = ref('')
const officialPrompt = ref('')
const testInputs = ref({})
const testResults = ref({ official: '', draft: '' })
const currentTaskId = ref('')

const isDeploying = ref(false)
const isTesting = ref(false)

const isFullscreen = ref(false)
const isOfficialFullscreen = ref(false)
const isDiffFullscreen = ref(false)

const readerVisible = ref(false)
const readerTitle = ref('')
const readerContent = ref('')
const resultFullscreenVisible = ref(false)
const resultFullscreenTitle = ref('')
const resultFullscreenContent = ref('')
const estimatedSeconds = ref(0)
const elapsedSeconds = ref(0)

const lineNumbersRef = ref(null)
const zenLineNumbersRef = ref(null)
const textareaRef = ref(null)

const saveStatus = ref('已与云端同步')
let saveTimeout = null

let testTimer = null
let activeTestRunId = ''

const validateApiKey = () => {
  if (!config) return true
  if (config.provider === 'Mock (演示)') return true
  if (!config.apiKey || config.apiKey.trim() === '') {
    ElMessage.warning('请先在左侧配置并连接 API Key')
    return false
  }
  return true
}

const clearTestTimer = () => {
  if (testTimer) {
    clearInterval(testTimer)
    testTimer = null
  }
}

const resetTestingState = (resetResults = false) => {
  isTesting.value = false
  clearTestTimer()
  elapsedSeconds.value = 0
  estimatedSeconds.value = 0
  activeTestRunId = ''
  currentTaskId.value = ''
  if (resetResults) {
    testResults.value = { official: '', draft: '' }
  }
}

watch(() => config.provider, (newProvider, oldProvider) => {
  if (!newProvider || newProvider === oldProvider) return

  if (currentTaskId.value && isTesting.value) {
    engine.stopTask(`${currentTaskId.value}_official`)
    engine.stopTask(`${currentTaskId.value}_draft`)
    engine.stopTask(currentTaskId.value)
  }

  resetTestingState()
})

const getFriendlyVarName = (v) => friendlyVarMap[v] || '参数'
const formatVarToken = (v) => `{${v}}`

const getIcon = (key) => {
  if (key === 'SCRIPT_SYSTEM') return User
  if (key === 'OUTLINE_TASK') return Reading
  if (key === 'BATCH_SCRIPT_PROMPT') return Collection
  if (key === 'ACT_GEN_TASK') return Memo
  return SetUp
}

const playgroundMeta = computed(() => {
  if (streamPromptKeys.includes(currentKey.value)) {
    return {
      mode: '流式双屏演练',
      title: currentKey.value === 'OUTLINE_TASK' ? '大纲策略流演练' : '三幕式生成流演练',
      description: currentKey.value === 'OUTLINE_TASK'
        ? '沙盒注入小说源数据后，同时启动官方版与调优版，以流式输出对比结构质量、节奏与压缩能力。'
        : '围绕创意或需求注入，实时比较官方版与当前调优版的三幕式结构输出。',
      output: '流式文本输出',
      exportLabel: '支持导出 Word',
      action: '点击 A/B 开始双屏演练',
      compareHint: '更适合看结构、节奏、钩子与段落组织差异。',
      exportHint: '适合导出长文本、策略说明和三幕式结构稿。',
      resultType: 'word'
    }
  }

  return {
    mode: '分镜约束对打',
    title: currentKey.value === 'BATCH_SCRIPT_PROMPT' ? '小说分镜约束双屏工坊' : '剧本分镜约束双屏工坊',
    description: currentKey.value === 'BATCH_SCRIPT_PROMPT'
      ? '上传 Excel/CSV 约束源文后，比较两套提示词生成的分镜脚本格式。'
      : '注入 Word/TXT 大纲或长文本，输出更长篇的分镜脚本格式，并支持表格导出。',
    output: '分镜脚本格式输出',
    exportLabel: '支持导出 Excel',
    action: '点击 A/B 开始双屏分镜对打',
    compareHint: '更适合看镜号、场景、画面和声音字段的稳定性。',
    exportHint: '长内容也可落成 Excel，便于交付与继续编排。',
    resultType: 'excel'
  }
})

const officialVars = computed(() => {
  if (!officialPrompt.value) return []
  const matches = officialPrompt.value.match(/\{([a-zA-Z_]\w*)\}/g) || []
  return [...new Set(matches.map((m) => m.replace(/[{}]/g, '')))]
})

const detectedVars = computed(() => {
  if (!editBuffer.value) return []
  const matches = editBuffer.value.match(/\{([^}]+)\}/g) || []
  return [...new Set(matches.map((m) => m.replace(/[{}]/g, '').trim()).filter(Boolean))]
})

const missingVars = computed(() => {
  if (!officialVars.value.length) return []
  return officialVars.value.filter((item) => !detectedVars.value.includes(item))
})

const requiresApiKey = computed(() => config?.provider !== 'Mock (演示)')
const apiKeyReady = computed(() => !requiresApiKey.value || Boolean(config?.apiKey && config.apiKey.trim()))
const canStartABTest = computed(() => apiKeyReady.value && missingVars.value.length === 0)

const diffStats = computed(() => {
  const officialLines = officialPrompt.value ? officialPrompt.value.split('\n').length : 0
  const draftLines = editBuffer.value ? editBuffer.value.split('\n').length : 0
  const officialSet = officialPrompt.value ? officialPrompt.value.split('\n') : []
  const draftSet = editBuffer.value ? editBuffer.value.split('\n') : []

  return {
    officialLines,
    draftLines,
    added: draftSet.filter((line) => !officialSet.includes(line)).length,
    removed: officialSet.filter((line) => !draftSet.includes(line)).length
  }
})

const estimateTestDuration = () => {
  const inputLength = Object.values(testInputs.value).reduce((sum, item) => sum + String(item || '').length, 0)
  const promptLength = (officialPrompt.value?.length || 0) + (editBuffer.value?.length || 0)

  if (config?.provider === 'Mock (演示)') {
    return 12
  }

  const raw = Math.ceil((inputLength + promptLength) / 1800) * 20
  return Math.min(Math.max(raw, 35), 240)
}

const formatDuration = (seconds) => {
  const safe = Math.max(0, Math.round(seconds || 0))
  const mins = Math.floor(safe / 60)
  const secs = safe % 60

  if (mins <= 0) return `${secs} 秒`
  return `${mins} 分 ${secs} 秒`
}

const estimatedTimeLabel = computed(() => formatDuration(estimatedSeconds.value || estimateTestDuration()))
const elapsedTimeLabel = computed(() => formatDuration(elapsedSeconds.value))
const remainingTimeLabel = computed(() => formatDuration(Math.max(estimatedSeconds.value - elapsedSeconds.value, 0)))
const testProgressPercent = computed(() => {
  if (!isTesting.value || !estimatedSeconds.value) return 0
  return Math.min(96, Math.max(8, Math.round((elapsedSeconds.value / estimatedSeconds.value) * 100)))
})
const testingStatusHint = computed(() => {
  if (!isTesting.value) return '等待开始'
  if (config?.provider === 'Mock (演示)') return 'Mock 演示模式下正在返回本地演练结果。'
  return '系统正在并发请求官方版与调优版，请耐心等待流式输出。'
})

watch(editBuffer, (newVal) => {
  saveStatus.value = '正在保存...'
  clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    localStorage.setItem(`prompt_draft_${currentKey.value}`, newVal)
    saveStatus.value = '已保存到本地草稿'
  }, 500)
})

const lineCount = computed(() => (editBuffer.value ? editBuffer.value.split('\n').length : 1))

const syncScroll = (e) => {
  if (lineNumbersRef.value) lineNumbersRef.value.scrollTop = e.target.scrollTop
}

const syncZenScroll = (e) => {
  if (zenLineNumbersRef.value) zenLineNumbersRef.value.scrollTop = e.target.scrollTop
}

const insertVar = (v) => {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const token = `{${v}}`
  editBuffer.value = editBuffer.value.slice(0, start) + token + editBuffer.value.slice(end)
  nextTick(() => {
    el.focus()
    el.selectionStart = el.selectionEnd = start + token.length
  })
}

const handleTab = (e) => {
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  editBuffer.value = editBuffer.value.slice(0, start) + '    ' + editBuffer.value.slice(end)
  nextTick(() => {
    el.selectionStart = el.selectionEnd = start + 4
  })
}

const isLongField = (v) => ['content', 'outline', 'original_idea', 'user_choice'].includes(v)

const supportsExcelImport = (varName) => {
  if (currentKey.value === 'OUTLINE_TASK') return ['content', 'user_choice'].includes(varName)
  if (currentKey.value === 'BATCH_SCRIPT_PROMPT') return ['content', 'user_choice'].includes(varName)
  if (currentKey.value === 'SCRIPT_TASK_TEMPLATE') return ['content', 'user_choice'].includes(varName)
  return false
}

const supportsWordImport = (varName) => currentKey.value === 'SCRIPT_TASK_TEMPLATE' && varName === 'outline'

const getInputPlaceholder = (varName) => {
  if (supportsExcelImport(varName)) return '可直接粘贴文本，或导入 Excel/CSV 注入沙盒'
  if (supportsWordImport(varName)) return '可直接粘贴大纲，或导入 Word/TXT'
  if (varName === 'original_idea') return '输入创意原点、人物关系、故事钩子或命题'
  return `填写 ${getFriendlyVarName(varName)}`
}

const copyContent = async (text) => {
  const content = getDisplayContent(text)
  if (!content.trim()) {
    ElMessage.warning('当前没有可复制的内容')
    return
  }
  await navigator.clipboard.writeText(content)
  ElMessage.success('内容已复制')
}

const copyOfficial = async () => {
  await navigator.clipboard.writeText(officialPrompt.value || '')
  ElMessage.success('官方版本已复制')
}

const copyToClipboard = async () => {
  await navigator.clipboard.writeText(editBuffer.value || '')
  ElMessage.success('当前草稿已复制')
}

const openReader = (title, content) => {
  readerTitle.value = title
  readerContent.value = content || ''
  readerVisible.value = true
}

const openResultFullscreen = (title, content) => {
  resultFullscreenTitle.value = title
  resultFullscreenContent.value = content || ''
  resultFullscreenVisible.value = true
}

const getDisplayContent = (content) => {
  if (!content) return '等待输出...'
  return String(content)
    .replace(/<span class="rocket-spin">.*?<\/span>/g, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .trim() || '等待输出...'
}

const hasEffectiveContent = (content) => {
  const text = getDisplayContent(content)
  return text && text !== '等待输出...'
}

const exportWord = (content, suffix) => {
  const text = getDisplayContent(content)
  if (!text || text === '等待输出...') {
    ElMessage.warning('没有可导出的有效内容')
    return
  }

  const html = [
    "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>",
    "<head><meta charset='utf-8'></head><body>",
    `<div style="font-family:Microsoft YaHei, PingFang SC, sans-serif; line-height:1.8; font-size:14px; white-space:pre-wrap;">${text.replace(/\n/g, '<br>')}</div>`,
    '</body></html>'
  ].join('')

  const link = document.createElement('a')
  link.href = `data:application/vnd.ms-word;charset=utf-8,${encodeURIComponent(html)}`
  link.download = `${assetMap[currentKey.value]}_${suffix}.doc`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  ElMessage.success('Word 导出已开始')
}

const parseCsvLine = (line) => {
  const result = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i]
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
    } else if (char === ',' && !inQuotes) {
      result.push(current)
      current = ''
    } else {
      current += char
    }
  }

  result.push(current)
  return result.map((item) => item.trim())
}

const parseResultToRows = (content) => {
  const text = getDisplayContent(content)
  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
  if (!lines.length) return [['内容'], [text]]

  const csvLike = lines.some((line) => line.includes(',')) || lines.some((line) => line.includes('\t'))
  if (csvLike) {
    return lines.map((line) => {
      if (line.includes('\t')) return line.split('\t').map((item) => item.trim())
      return parseCsvLine(line)
    })
  }

  const sceneRows = lines
    .map((line, index) => {
      const shotMatch = line.match(/(?:镜号|SHOT)\s*[:：]?\s*(\d+)/i)
      const sceneMatch = line.match(/场景\s*[:：]?\s*([^|；;]+)/)
      const visualMatch = line.match(/(?:画面|Visual)\s*[:：]?\s*([^|]+)/i)
      const audioMatch = line.match(/(?:声音|台词|Dialogue|SFX)\s*[:：]?\s*(.+)$/i)

      if (!shotMatch && !sceneMatch && !visualMatch && !audioMatch) return null
      return [
        shotMatch?.[1] || index + 1,
        sceneMatch?.[1]?.trim() || '',
        visualMatch?.[1]?.trim() || line,
        audioMatch?.[1]?.trim() || ''
      ]
    })
    .filter(Boolean)

  if (sceneRows.length) {
    return [['镜号', '场景', '画面内容 (Visual)', '台词 (Dialogue) & 音效 (SFX)'], ...sceneRows]
  }

  return [['内容'], ...lines.map((line) => [line])]
}

const exportExcel = (content, suffix) => {
  const rows = parseResultToRows(content)
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet(rows)
  XLSX.utils.book_append_sheet(wb, ws, '结果对比')
  XLSX.writeFile(wb, `${assetMap[currentKey.value]}_${suffix}.xlsx`)
  ElMessage.success('Excel 导出已开始')
}

const handleExportResult = (side) => {
  const target = side === 'official' ? testResults.value.official : testResults.value.draft
  const suffix = side === 'official' ? '官方原版' : '当前调优版'
  if (playgroundMeta.value.resultType === 'excel') {
    exportExcel(target, suffix)
    return
  }
  exportWord(target, suffix)
}

const handleReaderExport = () => {
  if (playgroundMeta.value.resultType === 'excel') {
    exportExcel(readerContent.value, readerTitle.value)
    return
  }
  exportWord(readerContent.value, readerTitle.value)
}

const handleResultFullscreenExport = () => {
  if (playgroundMeta.value.resultType === 'excel') {
    exportExcel(resultFullscreenContent.value, resultFullscreenTitle.value)
    return
  }
  exportWord(resultFullscreenContent.value, resultFullscreenTitle.value)
}

const handleImportFile = async (fileObj, varName) => {
  const file = fileObj.raw
  if (!file) return

  const fileName = file.name.toLowerCase()

  try {
    if (supportsExcelImport(varName)) {
      if (!/\.(xlsx|xls|csv)$/.test(fileName)) {
        ElMessage.error('请导入 Excel/CSV 文件')
        return
      }

      const reader = new FileReader()
      reader.onload = (event) => {
        try {
          const data = new Uint8Array(event.target.result)
          const workbook = XLSX.read(data, { type: 'array' })
          const rows = XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]], { header: 1 })
          const text = rows
            .filter((row) => Array.isArray(row) && row.some((cell) => String(cell || '').trim()))
            .map((row) => row.map((cell) => String(cell ?? '').trim()).join(' | '))
            .join('\n')

          testInputs.value[varName] = text
          ElMessage.success('Excel 数据已注入沙盒')
        } catch (error) {
          ElMessage.error(`Excel 解析失败：${error.message}`)
        }
      }
      reader.readAsArrayBuffer(file)
      return
    }

    if (supportsWordImport(varName)) {
      if (!/\.(docx|txt)$/.test(fileName)) {
        ElMessage.error('请导入 Word/TXT 文件')
        return
      }

      if (fileName.endsWith('.txt')) {
        const reader = new FileReader()
        reader.onload = (event) => {
          testInputs.value[varName] = String(event.target.result || '')
          ElMessage.success('TXT 大纲已注入沙盒')
        }
        reader.readAsText(file)
        return
      }

      const zip = new JSZip()
      const loadedZip = await zip.loadAsync(file)
      const xmlData = await loadedZip.file('word/document.xml').async('string')
      testInputs.value[varName] = xmlData.replace(/<w:p[^>]*>/gi, '\n').replace(/<[^>]+>/g, '').trim()
      ElMessage.success('Word 大纲已注入沙盒')
    }
  } catch (error) {
    ElMessage.error(`文件处理异常：${error.message}`)
  }
}

const escapeHtml = (unsafe) => (unsafe || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const diffHtml = computed(() => {
  const oldLines = officialPrompt.value.split('\n')
  const newLines = editBuffer.value.split('\n')
  const dp = Array(oldLines.length + 1).fill(null).map(() => Array(newLines.length + 1).fill(0))

  for (let i = 1; i <= oldLines.length; i += 1) {
    for (let j = 1; j <= newLines.length; j += 1) {
      dp[i][j] = oldLines[i - 1] === newLines[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1])
    }
  }

  let i = oldLines.length
  let j = newLines.length
  const diff = []

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      diff.unshift({ type: 'unchanged', text: oldLines[i - 1] })
      i -= 1
      j -= 1
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      diff.unshift({ type: 'added', text: newLines[j - 1] })
      j -= 1
    } else {
      diff.unshift({ type: 'removed', text: oldLines[i - 1] })
      i -= 1
    }
  }

  let html = ''
  diff.forEach((item) => {
    html += `<div class="diff-row ${item.type}"><span class="diff-num">${item.type === 'added' ? '+' : item.type === 'removed' ? '-' : ' '}</span><span class="diff-content">${escapeHtml(item.text) || ' '}</span></div>`
  })
  return html
})

const loadPrompt = async () => {
  try {
    const res = await retryAsync(
      () => axios.get(apiUrl(`/api/script/prompts/${currentKey.value}`)),
      { retries: 6, delayMs: 800, shouldRetry: isRetriableNetworkError }
    )
    if (res.data?.status !== 'success') {
      ElMessage.error(`资产加载失败：${res.data?.message || '未知错误'}`)
      return
    }

    officialPrompt.value = res.data.official_prompt || ''
    const localDraft = localStorage.getItem(`prompt_draft_${currentKey.value}`)
    if (localDraft && localDraft !== res.data.user_prompt) {
      editBuffer.value = localDraft
      saveStatus.value = '已恢复本地草稿'
    } else {
      editBuffer.value = res.data.user_prompt || ''
      saveStatus.value = '已与云端同步'
    }

    const matches = officialPrompt.value.match(/\{([a-zA-Z_]\w*)\}/g) || []
    const vars = [...new Set(matches.map((m) => m.replace(/[{}]/g, '')))]
    vars.forEach((item) => {
      if (typeof testInputs.value[item] !== 'string') testInputs.value[item] = ''
    })
  } catch (error) {
    ElMessage.error(createErrorMessage(error, '资产加载失败，请检查后端服务'))
  }
}

const switchAsset = (key) => {
  if (currentTaskId.value && isTesting.value) {
    engine.stopTask(`${currentTaskId.value}_official`)
    engine.stopTask(`${currentTaskId.value}_draft`)
    engine.stopTask(currentTaskId.value)
  }

  currentKey.value = key
  resetTestingState(true)
  loadPrompt()
}

const handleDeploy = async () => {
  if (missingVars.value.length > 0) {
    ElMessage.error('部署已阻断：必需变量缺失')
    return
  }

  isDeploying.value = true
  try {
    const formData = new FormData()
    formData.append('key', currentKey.value)
    formData.append('content', editBuffer.value)
    await axios.post(apiUrl('/api/script/prompts/update'), formData)
    localStorage.removeItem(`prompt_draft_${currentKey.value}`)
    saveStatus.value = '已与云端同步'
    ElMessage.success('部署成功')
  } catch (error) {
    ElMessage.error(createErrorMessage(error, '部署失败'))
  } finally {
    isDeploying.value = false
  }
}

const handleReset = () => {
  ElMessageBox.confirm('恢复后将覆盖当前草稿，是否继续？', '恢复确认', { type: 'warning' })
    .then(async () => {
      await axios.post(apiUrl(`/api/script/prompts/reset/${currentKey.value}`))
      localStorage.removeItem(`prompt_draft_${currentKey.value}`)
      await loadPrompt()
      ElMessage.success('已恢复官方版本')
    })
    .catch(() => {})
}

const buildPromptContent = (source) => {
  let content = source || ''
  Object.keys(testInputs.value).forEach((key) => {
    const value = String(testInputs.value[key] || '')
    content = content.split(`{${key}}`).join(value)
  })
  return content
}

const startTestTimer = () => {
  clearTestTimer()
  elapsedSeconds.value = 0
  testTimer = setInterval(() => {
    elapsedSeconds.value += 1
  }, 1000)
}

const runABTest = () => {
  if (!validateApiKey()) return
  if (missingVars.value.length > 0) {
    ElMessage.error('必需变量缺失，无法开始演练')
    return
  }

  const emptyVars = officialVars.value.filter((key) => !String(testInputs.value[key] || '').trim())
  if (emptyVars.length > 0) {
    ElMessage.error(`请先补全沙盒数据：${emptyVars.join('、')}`)
    return
  }

  isTesting.value = true
  currentTaskId.value = `test_${Date.now()}`
  activeTestRunId = currentTaskId.value
  estimatedSeconds.value = estimateTestDuration()
  elapsedSeconds.value = 0
  startTestTimer()
  testResults.value = {
    official: '正在等待流式输出...',
    draft: '正在等待流式输出...'
  }

  let officialBuffer = ''
  let draftBuffer = ''
  let doneCount = 0
  const runId = currentTaskId.value

  const finishOnce = () => {
    if (activeTestRunId !== runId) return
    doneCount += 1
    if (doneCount >= 2) {
      resetTestingState()
    }
  }

  const failOnce = (error) => {
    if (activeTestRunId !== runId) return
    resetTestingState()
    ElMessage.error(error || '双屏演练失败，请稍后重试')
  }

  const updateOfficial = throttle((content) => {
    if (activeTestRunId !== runId) return
    testResults.value.official = content
  }, 80)

  const updateDraft = throttle((content) => {
    if (activeTestRunId !== runId) return
    testResults.value.draft = content
  }, 80)

  const officialUserPrompt = buildPromptContent(officialPrompt.value)
  const draftUserPrompt = buildPromptContent(editBuffer.value)

  engine.fetchStream(
    'script/prompts/test_stream',
    { system_prompt: '官方原版', user_prompt: officialUserPrompt, task_id: `${currentTaskId.value}_official` },
    (chunk) => {
      if (activeTestRunId !== runId) return
      if (officialBuffer === '' && testResults.value.official.includes('等待流式')) officialBuffer = ''
      officialBuffer += chunk
      updateOfficial(officialBuffer)
    },
    undefined,
    finishOnce,
    failOnce,
    config
  )

  engine.fetchStream(
    'script/prompts/test_stream',
    { system_prompt: '当前调优版', user_prompt: draftUserPrompt, task_id: `${currentTaskId.value}_draft` },
    (chunk) => {
      if (activeTestRunId !== runId) return
      if (draftBuffer === '' && testResults.value.draft.includes('等待流式')) draftBuffer = ''
      draftBuffer += chunk
      updateDraft(draftBuffer)
    },
    undefined,
    finishOnce,
    failOnce,
    config
  )
}

const stopTest = () => {
  if (currentTaskId.value) {
    engine.stopTask(`${currentTaskId.value}_official`)
    engine.stopTask(`${currentTaskId.value}_draft`)
    engine.stopTask(currentTaskId.value)
  }
  resetTestingState()
  ElMessage.warning('已停止当前双屏演练')
}

onMounted(loadPrompt)
</script>

<style scoped>
.studio-shell {
  display: flex;
  gap: 20px;
  min-height: calc(100vh - 110px);
  padding: 16px;
  background:
    radial-gradient(circle at top left, rgba(227, 112, 13, 0.08), transparent 28%),
    linear-gradient(180deg, #f8f6f2 0%, #f3f4f6 100%);
}

.studio-sidebar {
  width: 296px;
  display: flex;
  flex-direction: column;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.sidebar-brand {
  display: flex;
  gap: 14px;
  padding: 24px 22px 18px;
  border-bottom: 1px solid #eef2f7;
}

.brand-mark {
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #fff;
  font-size: 22px;
  background: linear-gradient(135deg, #d97706, #fb923c);
  box-shadow: 0 12px 24px rgba(217, 119, 6, 0.28);
}

.sidebar-brand h2 {
  margin: 0;
  font-size: 20px;
  color: #111827;
}

.sidebar-brand p {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 13px;
  line-height: 1.5;
}

.sidebar-section {
  padding: 18px 14px;
  overflow: auto;
}

.section-label {
  margin: 0 8px 12px;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.asset-card {
  width: 100%;
  display: grid;
  grid-template-columns: 32px 1fr auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
  padding: 14px 14px 14px 12px;
  border: 1px solid transparent;
  border-radius: 18px;
  background: transparent;
  cursor: pointer;
  transition: all 0.24s ease;
  text-align: left;
}

.asset-card:hover {
  background: #fffaf3;
  border-color: rgba(251, 146, 60, 0.16);
  transform: translateY(-1px);
}

.asset-card.active {
  background: linear-gradient(135deg, #fff7ed, #ffffff);
  border-color: rgba(234, 88, 12, 0.22);
  box-shadow: 0 12px 24px rgba(217, 119, 6, 0.08);
}

.asset-icon {
  color: #9ca3af;
  font-size: 20px;
}

.asset-card.active .asset-icon {
  color: #d97706;
}

.asset-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.asset-copy strong {
  color: #1f2937;
  font-size: 14px;
}

.asset-copy small {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.4;
}

.asset-chip {
  padding: 4px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.sidebar-summary {
  margin: 0 18px 18px;
  padding: 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #fffdf7 0%, #fff7ed 100%);
  border: 1px solid rgba(251, 146, 60, 0.18);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  color: #6b7280;
  font-size: 13px;
  padding: 6px 0;
}

.summary-row strong {
  color: #111827;
}

.summary-row strong.danger {
  color: #dc2626;
}

.sidebar-actions {
  padding: 18px;
  border-top: 1px solid #eef2f7;
  display: grid;
  gap: 12px;
}

.action-btn {
  height: 44px;
  border-radius: 14px;
  font-weight: 700;
}

.action-btn.primary {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, #d97706, #f97316);
  box-shadow: 0 10px 20px rgba(217, 119, 6, 0.18);
}

.studio-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.studio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 24px 28px 20px;
  border-bottom: 1px solid #edf2f7;
}

.header-copy {
  display: flex;
  align-items: center;
  gap: 14px;
}

.status-dot {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  border-radius: 999px;
  background: #22c55e;
  box-shadow: 0 0 0 8px rgba(34, 197, 94, 0.12);
}

.status-dot.danger {
  background: #ef4444;
  box-shadow: 0 0 0 8px rgba(239, 68, 68, 0.12);
}

.header-copy h3 {
  margin: 0;
  color: #111827;
  font-size: 22px;
}

.header-copy p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.studio-tabs {
  display: inline-flex;
  gap: 6px;
  padding: 5px;
  border-radius: 16px;
  background: #f3f4f6;
}

.studio-tabs button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: none;
  padding: 10px 16px;
  border-radius: 12px;
  background: transparent;
  color: #64748b;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.24s ease;
}

.studio-tabs button.active {
  color: #d97706;
  background: #fff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

.studio-workspace {
  flex: 1;
  overflow: hidden;
  padding: 24px 28px 28px;
  background:
    radial-gradient(circle at top right, rgba(249, 115, 22, 0.06), transparent 24%),
    #fafaf9;
}

.workspace-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-banner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.editor-banner.warning {
  background: #fff5f5;
  border-color: #fecaca;
}

.editor-vars {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  color: #6b7280;
  font-size: 13px;
}

.var-badge {
  cursor: pointer;
  border-radius: 999px;
  border: 1px solid #fed7aa;
  background: #fff7ed;
  color: #c2410c;
  font-weight: 700;
}

.var-badge.missing {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
  text-decoration: line-through;
}

.editor-actions-inline {
  display: flex;
  align-items: center;
  gap: 16px;
}

.save-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #64748b;
}

.save-status.ok {
  color: #16a34a;
}

.save-status.danger {
  color: #dc2626;
}

.fullscreen-btn {
  border-radius: 12px;
}

.editor-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid #374151;
  background: #111827;
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.2);
}

.editor-shell.warning {
  border-color: #ef4444;
}

.editor-shell-head {
  position: relative;
  display: flex;
  align-items: center;
  padding: 14px 18px;
  background: #1f2937;
  border-bottom: 1px solid #374151;
}

.traffic-lights {
  display: flex;
  gap: 8px;
}

.traffic-lights span {
  width: 12px;
  height: 12px;
  border-radius: 999px;
}

.traffic-lights .red {
  background: #ff5f56;
}

.traffic-lights .yellow {
  background: #ffbd2e;
}

.traffic-lights .green {
  background: #27c93f;
}

.editor-file {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  color: #94a3b8;
  font-size: 13px;
  font-family: Consolas, Monaco, monospace;
}

.ghost-icon {
  margin-left: auto;
  border: none;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 18px;
}

.editor-shell-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.line-numbers {
  width: 52px;
  padding: 18px 0;
  overflow: hidden;
  background: #0f172a;
  border-right: 1px solid #273244;
  text-align: center;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
  user-select: none;
  font-family: Consolas, Monaco, monospace;
}

.code-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  padding: 18px;
  background: transparent;
  color: #e5e7eb;
  line-height: 1.7;
  font-size: 14px;
  font-family: Consolas, Monaco, monospace;
  overflow: auto;
  white-space: pre;
}

.reference-panel {
  border: none;
  background: transparent;
}

.collapse-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.reference-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  margin-bottom: 10px;
}

.reference-content {
  margin: 0;
  max-height: 180px;
  overflow: auto;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
  color: #475569;
  font-size: 13px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.diff-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.diff-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 13px;
  font-weight: 700;
}

.diff-legend .removed {
  color: #ef4444;
}

.diff-legend .added {
  color: #22c55e;
}

.diff-legend .muted {
  color: #64748b;
  font-weight: 500;
}

.diff-box {
  flex: 1;
  overflow: auto;
  border-radius: 22px;
  border: 1px solid #374151;
  background: #0f172a;
  padding: 10px 0;
  font-family: Consolas, Monaco, monospace;
}

.diff-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.diff-stat-card {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  background: #fff;
}

.diff-stat-card span {
  display: block;
  color: #64748b;
  font-size: 12px;
}

.diff-stat-card strong {
  display: block;
  margin-top: 6px;
  color: #111827;
  font-size: 22px;
}

.diff-stat-card.added {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.diff-stat-card.removed {
  background: #fef2f2;
  border-color: #fecaca;
}

:deep(.diff-row) {
  display: flex;
  padding: 3px 18px;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.diff-row .diff-num) {
  width: 24px;
  flex-shrink: 0;
  text-align: right;
  color: #64748b;
}

:deep(.diff-row .diff-content) {
  flex: 1;
  margin-left: 12px;
}

:deep(.diff-row.unchanged .diff-content) {
  color: #94a3b8;
}

:deep(.diff-row.added) {
  background: rgba(34, 197, 94, 0.14);
}

:deep(.diff-row.added .diff-content),
:deep(.diff-row.added .diff-num) {
  color: #86efac;
}

:deep(.diff-row.removed) {
  background: rgba(239, 68, 68, 0.14);
}

:deep(.diff-row.removed .diff-content),
:deep(.diff-row.removed .diff-num) {
  color: #fca5a5;
}

.playground-panel {
  overflow: auto;
}

.playground-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: stretch;
}

.playground-hero {
  flex: 1;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(17, 24, 39, 0.94), rgba(51, 65, 85, 0.94)),
    linear-gradient(135deg, #111827, #334155);
  color: #fff;
  overflow: hidden;
}

.hero-copy {
  max-width: 720px;
}

.hero-kicker {
  display: inline-block;
  margin-bottom: 10px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.playground-hero h3 {
  margin: 0;
  font-size: 28px;
}

.playground-hero p {
  margin: 10px 0 0;
  max-width: 680px;
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.7;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  align-content: flex-start;
  gap: 10px;
  min-width: 220px;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  color: #fff7ed;
  font-size: 12px;
  font-weight: 700;
}

.playground-actions {
  width: 260px;
  display: flex;
  align-items: stretch;
}

.battle-btn {
  width: 100%;
  height: auto;
  min-height: 100%;
  border: none;
  border-radius: 24px;
  background: linear-gradient(135deg, #d97706, #f97316);
  color: #fff;
  font-size: 15px;
  font-weight: 800;
  box-shadow: 0 18px 36px rgba(217, 119, 6, 0.2);
}

.battle-btn.stop {
  background: linear-gradient(135deg, #dc2626, #ef4444);
}

.operation-hint {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.9);
}

.operation-hint.warning {
  border-color: rgba(239, 68, 68, 0.24);
  background: linear-gradient(135deg, #fff1f2, #ffffff);
}

.hint-title {
  color: #111827;
  font-size: 14px;
  font-weight: 800;
}

.hint-copy {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}

.testing-banner {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 18px;
  padding: 18px 20px 22px;
  border-radius: 22px;
  background: linear-gradient(135deg, #111827, #1f2937);
  color: #f8fafc;
}

.testing-banner-left,
.testing-banner-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.testing-banner-left strong {
  display: block;
  font-size: 16px;
}

.testing-banner-left p {
  margin: 6px 0 0;
  color: rgba(226, 232, 240, 0.76);
  font-size: 13px;
  line-height: 1.6;
}

.loading-orb {
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: #fb923c;
  box-shadow: 0 0 0 0 rgba(251, 146, 60, 0.45);
  animation: pulseGlow 1.6s infinite;
}

.time-chip {
  min-width: 110px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.time-chip span {
  display: block;
  color: rgba(226, 232, 240, 0.72);
  font-size: 12px;
}

.time-chip strong {
  display: block;
  margin-top: 6px;
  font-size: 15px;
  color: #fff;
}

.progress-track {
  grid-column: 1 / -1;
  height: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #f97316, #fb923c, #fdba74);
  transition: width 0.35s ease;
  animation: shimmerMove 2s linear infinite;
}

.capability-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.capability-item {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.86);
}

.capability-item strong {
  display: block;
  color: #111827;
  font-size: 14px;
}

.capability-item span {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

.playground-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 18px;
  min-height: 0;
}

.sandbox-panel,
.compare-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.04);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 22px 22px 16px;
}

.panel-kicker {
  display: inline-block;
  margin-bottom: 8px;
  color: #d97706;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-head h4 {
  margin: 0;
  font-size: 20px;
  color: #111827;
}

.panel-note {
  max-width: 180px;
  color: #6b7280;
  font-size: 12px;
  line-height: 1.6;
  text-align: right;
}

.flow-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  padding: 0 22px 18px;
}

.flow-step {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.flow-step strong {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  font-size: 12px;
}

.flow-step span {
  color: #475569;
  font-size: 12px;
  line-height: 1.5;
}

.input-list {
  flex: 1;
  overflow: auto;
  padding: 0 22px 22px;
}

.input-card {
  margin-bottom: 14px;
  padding: 16px;
  border-radius: 18px;
  background: #fffdf8;
  border: 1px solid #f1f5f9;
}

.input-card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 10px;
}

.input-name {
  color: #111827;
  font-size: 14px;
  font-weight: 800;
}

.input-key {
  margin-top: 4px;
  color: #94a3b8;
  font-size: 12px;
  font-family: Consolas, Monaco, monospace;
}

.input-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.compare-panel {
  padding: 20px;
  gap: 18px;
}

.compare-overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.overview-card {
  padding: 18px;
  border-radius: 20px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
}

.overview-card.warm {
  background: linear-gradient(135deg, #fff7ed, #fffbeb);
  border-color: rgba(249, 115, 22, 0.18);
}

.overview-label {
  color: #d97706;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.overview-card strong {
  display: block;
  margin-top: 8px;
  color: #111827;
  font-size: 18px;
}

.overview-card p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.6;
}

.screen-wall {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.screen-card {
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: #fff;
}

.screen-card.active {
  border-color: rgba(249, 115, 22, 0.28);
  box-shadow: 0 18px 32px rgba(249, 115, 22, 0.08);
}

.screen-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 18px 18px 14px;
  border-bottom: 1px solid #eef2f7;
  background: #f8fafc;
}

.screen-head.glow {
  background: linear-gradient(135deg, #fff7ed, #ffffff);
}

.screen-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 9px;
  border-radius: 999px;
  background: #111827;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.05em;
}

.screen-badge.live {
  background: #ea580c;
  box-shadow: 0 0 0 6px rgba(234, 88, 12, 0.12);
}

.screen-head h5 {
  margin: 10px 0 0;
  color: #111827;
  font-size: 18px;
}

.screen-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.screen-tools {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tool-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: #6b7280 !important;
}

.screen-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 20px;
  background:
    linear-gradient(180deg, rgba(248, 250, 252, 0.5) 0%, rgba(255, 255, 255, 0.9) 100%);
}

.screen-text,
.reader-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.85;
  color: #1f2937;
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
}

.reader-content {
  max-height: 65vh;
  overflow: auto;
  padding: 18px;
  border-radius: 18px;
  background: #fafaf9;
  border: 1px solid #e5e7eb;
}

.export-btn {
  border: none;
  background: linear-gradient(135deg, #d97706, #f97316);
}

.dialog-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.result-fullscreen-body {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: #020617;
}

.result-fullscreen-text {
  margin: 0;
  min-height: 100%;
  white-space: pre-wrap;
  word-break: break-word;
  color: #e2e8f0;
  font-size: 15px;
  line-height: 1.9;
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
}

:deep(.reader-dialog .el-dialog) {
  border-radius: 24px;
}

:deep(.reader-dialog .el-dialog__header) {
  margin: 0;
  padding: 20px 24px 0;
  font-weight: 800;
}

:deep(.reader-dialog .el-dialog__body) {
  padding: 18px 24px;
}

:deep(.el-collapse-item__header),
:deep(.el-collapse-item__wrap) {
  border: none;
  background: transparent;
}

:deep(.el-textarea__inner),
:deep(.el-input__wrapper) {
  border-radius: 14px;
  box-shadow: none;
}

:deep(.el-textarea__inner) {
  min-height: 120px;
  font-family: Consolas, Monaco, monospace;
  line-height: 1.65;
}

:deep(.zen-dialog .el-dialog__header) {
  display: none;
}

:deep(.zen-dialog .el-dialog__body) {
  height: 100vh;
  padding: 0;
  background: #0f172a;
  display: flex;
  flex-direction: column;
}

.zen-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 16px 22px;
  border-bottom: 1px solid #1e293b;
  background: #111827;
}

.zen-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #f8fafc;
  font-size: 18px;
  font-weight: 800;
}

.zen-toolbar-actions {
  display: flex;
  gap: 10px;
}

.zen-editor {
  flex: 1;
  border-radius: 0;
  border: none;
  box-shadow: none;
}

.readonly-fullscreen {
  color: #cbd5e1;
}

:deep(.diff-zen-dialog .el-dialog__body) {
  background: #020617;
}

.zen-diff-box {
  border-radius: 0;
  border: none;
  background: #020617;
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 0 0 rgba(251, 146, 60, 0.45); transform: scale(1); }
  70% { box-shadow: 0 0 0 14px rgba(251, 146, 60, 0); transform: scale(1.08); }
  100% { box-shadow: 0 0 0 0 rgba(251, 146, 60, 0); transform: scale(1); }
}

@keyframes shimmerMove {
  0% { filter: brightness(0.96); }
  50% { filter: brightness(1.08); }
  100% { filter: brightness(0.96); }
}

@media (max-width: 1400px) {
  .playground-grid {
    grid-template-columns: 320px 1fr;
  }
}

@media (max-width: 1200px) {
  .studio-shell {
    flex-direction: column;
  }

  .studio-sidebar {
    width: 100%;
  }

  .playground-top,
  .playground-grid,
  .screen-wall,
  .capability-strip,
  .diff-stats,
  .testing-banner {
    grid-template-columns: 1fr;
    display: grid;
  }

  .playground-actions {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .studio-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .studio-tabs {
    width: 100%;
    overflow: auto;
  }

  .editor-banner,
  .panel-head,
  .input-card-head,
  .screen-head,
  .testing-banner-left,
  .testing-banner-right {
    flex-direction: column;
    align-items: flex-start;
  }

  .flow-strip,
  .compare-overview,
  .capability-strip,
  .diff-stats {
    grid-template-columns: 1fr;
  }

  .playground-hero {
    flex-direction: column;
  }

  .hero-tags {
    min-width: auto;
  }
}
</style>
