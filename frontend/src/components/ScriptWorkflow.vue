<template>
  <div class="workflow-engine">
    <div class="premium-steps">
      <div class="step-item" :class="{ 'is-active': activeStep === 0, 'is-done': activeStep > 0 }"><div class="step-icon">1</div><span class="step-text">原始创意</span></div>
      <div class="step-line"></div>
      <div class="step-item" :class="{ 'is-active': activeStep === 1, 'is-done': activeStep > 1 }"><div class="step-icon">2</div><span class="step-text">三幕式构建</span></div>
      <div class="step-line"></div>
      <div class="step-item" :class="{ 'is-active': activeStep === 2, 'is-done': activeStep > 2 }"><div class="step-icon">3</div><span class="step-text">动态大纲</span></div>
      <div class="step-line"></div>
      <div class="step-item" :class="{ 'is-active': activeStep === 3 }"><div class="step-icon">4</div><span class="step-text">分镜脚本</span></div>
    </div>

    <div class="workflow-content">
      <div v-show="activeStep === 0" class="glass-card fade-in">
        <div class="creative-input-box">
          <div class="box-header"><span class="dot"></span> 💡 核心灵感库：默认创意已载入</div>
          <el-alert title="提示：AI 已为您载入后台预设创意，您可以随意微调，内容将实时暂存。" type="info" show-icon :closable="false" style="margin-bottom: 20px;" />
          <el-input v-model="creativeIdea" type="textarea" :rows="14" class="premium-textarea" placeholder="正在努力载入默认灵感..." />
          <div class="step-footer" style="text-align: center; margin-top: 32px;">
            <el-button class="btn-hermes mega" @click="generateThreeActs" :loading="isGenerating">🚀 激发灵感，构建三幕式戏剧结构 ➡</el-button>
          </div>
        </div>
      </div>

      <div v-show="activeStep === 1" class="glass-card fade-in">
        <div class="box-header"><span class="dot"></span> 三幕式选择：请选择一个版本作为剧本骨架</div>
        
        <div v-if="isGenerating" class="estimate-box">
          <span class="spinner-small"></span>
          系统正在进行高强度头脑风暴... <strong>预计用时: {{ estimatedTime }}</strong>
        </div>

        <div v-if="isGenerating" class="ai-terminal">
          <div class="terminal-header">
            <div class="mac-btns"><span class="r"></span><span class="y"></span><span class="g"></span></div>
            <span class="title">Structure_Engine.sh</span>
            <span class="status blink">🟢 Running</span>
          </div>
          <div class="terminal-body" ref="terminalBody">
            <div v-if="progressMsg" class="sys-msg">> {{ progressMsg }} <span class="blink">_</span></div>
            <pre class="typewriter-text">{{ tempActsText }}</pre>
          </div>
        </div>

        <div v-else class="acts-grid">
          <div class="pro-tips"><el-icon><InfoFilled /></el-icon> 编剧锦囊：为您生成了 3 个备选方案。您可以直接在卡片内微调，或点击右上角“全屏精修”进入沉浸模式。</div>
          
          <div class="premium-cards-wrapper">
            <div v-for="(act, index) in threeActOptions" :key="index"
                 class="premium-act-card"
                 :class="{ 'is-selected': selectedActIndex === index }"
                 @click="selectedActIndex = index">
              
              <div class="card-top-bar">
                <div class="version-badge">方案 {{ ['A', 'B', 'C'][index] || index + 1 }}</div>
                <el-button type="primary" link class="fullscreen-btn" @click.stop="openImmersive(index)">
                  <el-icon style="margin-right: 4px"><FullScreen /></el-icon> 全屏精修
                </el-button>
              </div>

              <div class="card-editor-area">
                <el-input v-model="threeActOptions[index]" type="textarea" @click.stop />
              </div>

              <div class="card-bottom-action">
                 <div class="action-select-btn" :class="{ 'active-btn': selectedActIndex === index }">
                    <el-icon v-if="selectedActIndex === index" style="margin-right:6px; font-size:16px;"><Select /></el-icon>
                    {{ selectedActIndex === index ? '✅ 已锁定此大纲' : '采用此方案' }}
                 </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="step-footer split">
          <el-button plain @click="goBack" size="large" :disabled="isGenerating">⬅ 上一步：修改创意</el-button>
          <el-button type="danger" plain @click="stopTask" v-if="isGenerating">■ 紧急阻断</el-button>
          <el-button class="btn-hermes" :disabled="selectedActIndex === null || isGenerating" @click="activeStep = 2" size="large" v-if="!isGenerating">确认结构，进入动态大纲阶段 ➡</el-button>
        </div>
      </div>

      <div v-show="activeStep === 2" class="glass-card fade-in">
        
        <div class="config-toolbar-premium">
          <div class="setting-group">
            <div class="icon-box"><el-icon><Setting /></el-icon></div>
            <div class="setting-info">
              <span class="title">剧本名称</span>
              <span class="desc">用于导出文件命名</span>
            </div>
            <el-input v-model="scriptName" placeholder="请输入剧本名称" class="premium-input" />
          </div>
          
          <div class="setting-group">
            <div class="icon-box"><el-icon><VideoCamera /></el-icon></div>
            <div class="setting-info">
              <span class="title">目标集数配置</span>
              <span class="desc">系统将根据此数值智能分配剧情节奏</span>
            </div>
            <el-input-number v-model="totalEpisodes" :min="1" :max="100" class="premium-num-input" />
          </div>
          
          <div class="action-group">
            <el-button class="btn-hermes mega" @click="generateOutline" :loading="isGenerating" v-if="!isGenerating">
              <el-icon style="margin-right:8px"><VideoPlay /></el-icon> 执行 {{ totalEpisodes }} 集动态解析
            </el-button>
            <el-button type="danger" class="mega" @click="stopTask" v-else>■ 紧急阻断任务</el-button>
          </div>
        </div>

        <div v-if="isGenerating" class="estimate-box">
          <span class="spinner-small"></span>
          系统正在将骨架扩写为丰满的剧情... <strong>预计用时: {{ estimatedTime }}</strong>
        </div>

        <div class="outline-editor-layout">
          <div class="main-editor">
            <div class="ai-terminal" v-if="isGenerating || scriptOutline">
               <div class="terminal-header"><div class="mac-btns"><span class="r"></span><span class="y"></span><span class="g"></span></div><span class="title">Outline_Processor.sh</span></div>
              <div class="terminal-body" ref="terminalBody">
                <div v-if="isGenerating && progressMsg" class="sys-msg">> {{ progressMsg }} <span class="blink">_</span></div>
                <el-input v-model="scriptOutline" type="textarea" :rows="18" class="premium-textarea ghost-input" />
              </div>
            </div>
          </div>
        </div>

        <div class="step-footer split">
          <el-button plain @click="goBack" size="large" :disabled="isGenerating">⬅ 上一步：重选三幕式</el-button>
          <el-button class="btn-hermes" :disabled="!scriptOutline || isGenerating" @click="goToStep4AndGenerate" size="large">
            大纲定稿，一键下发分镜渲染 ➡
          </el-button>
        </div>
      </div>

      <div v-show="activeStep === 3" class="glass-card fade-in" style="padding: 0; overflow: hidden;">
        
        <div class="premium-empty-state" v-if="!isGeneratingStoryboard && Object.keys(finalResults).length === 0">
          <div class="empty-icon-box">
            <div class="pulse-ring"></div>
            <el-icon><Film /></el-icon>
          </div>
          <h2 class="empty-title">大纲已就绪，等待下发分镜渲染引擎</h2>
          <p class="empty-desc">系统将自动调度大模型算力，为您将大纲裂变为包含镜号、景别、画面、台词的专业分镜矩阵</p>
          <div class="action-buttons">
            <el-button plain @click="goBack" class="mega-plain" size="large">⬅ 返回精修大纲</el-button>
            <el-button class="btn-hermes mega" @click="generateStoryboard">
              <el-icon style="margin-right: 8px"><VideoPlay /></el-icon> 启动全分镜渲染
            </el-button>
          </div>
        </div>

        <div v-if="isGeneratingStoryboard" class="rendering-status">
          <div class="spinner"></div>
          <div class="status-header"><h3>正在根据动态大纲渲染影视分镜...</h3></div>
          <p class="estimate-text">
            <strong>预计用时：{{ estimatedStoryboardTime }}</strong> (引擎已开启防堵塞保护)
          </p>
          <div class="cyber-terminal-mini">
            <span class="blink">_</span> {{ progressMsg }}
          </div>
          <el-progress :percentage="progressVal" :stroke-width="12" striped striped-flow color="#E3700D" />
          <el-button type="danger" plain @click="stopTask" style="margin-top: 30px;">■ 物理阻断任务</el-button>
        </div>

        <div v-if="Object.keys(finalResults).length > 0" class="results-showcase fade-in">
          <!-- 头部区域 -->
          <div class="showcase-header">
            <div class="title">
              <span class="dot g"></span> 剧本分镜矩阵生成完毕 (共 {{ Object.keys(finalResults).length }} 集)
            </div>
            <div class="actions">
              <el-button plain @click="goBack">返回上一步</el-button>
              <el-button plain type="primary" @click="exportCurrentExcel" style="font-weight: bold">
                <el-icon style="margin-right: 6px"><Download /></el-icon> 下载本集
              </el-button>
              <el-button class="btn-hermes" @click="exportAllSheetsExcel" style="padding: 8px 20px">
                <el-icon style="margin-right: 6px"><Document /></el-icon> 下载全集
              </el-button>
              <el-button class="btn-hermes" @click="exportBatchZip" style="padding: 8px 20px">
                <el-icon style="margin-right: 6px"><Files /></el-icon> 打包 ZIP
              </el-button>
            </div>
          </div>

          <!-- 搜索和筛选区域 -->
          <div class="search-filter-bar">
            <div class="search-section">
              <el-input v-model="searchQuery" placeholder="搜索画面或台词内容..." clearable prefix-icon="Search" @input="handleSearch" class="search-input" />
            </div>
            <div class="filter-section">
              <el-select v-model="sceneFilter" placeholder="按场景筛选" clearable @change="handleFilter" class="filter-select">
                <el-option v-for="scene in uniqueScenes" :key="scene" :label="scene" :value="scene" />
              </el-select>
              <el-button type="primary" plain @click="resetFilters">
                <el-icon><Refresh /></el-icon> 重置
              </el-button>
            </div>
          </div>

          <!-- 布局切换 -->
          <div class="view-controls">
            <div class="layout-toggle">
              <span class="toggle-label">阅览模式:</span>
              <el-radio-group v-model="layoutMode" @change="switchLayout">
                <el-radio-button label="table"><el-icon style="margin-right:4px"><Grid /></el-icon> 数据表格</el-radio-button>
                <el-radio-button label="av"><el-icon style="margin-right:4px"><Reading /></el-icon> 视听剧本</el-radio-button>
              </el-radio-group>
            </div>
            <div class="pagination-toggle">
              <el-switch v-model="showPagination" active-text="显示分页" inactive-text="无限滚动" @change="currentPage = 1" />
            </div>
            <div class="view-info">
              共 <strong>{{ filteredScenes.length }}</strong> 个场景 / <strong>{{ filteredData.length }}</strong> 个分镜
            </div>
          </div>

          <!-- 主要内容区域 -->
          <div class="showcase-body">
            <!-- 侧边栏 -->
            <div class="episode-sidebar">
              <!-- 快速导航 -->
              <div class="sidebar-header">
                <h4>剧集导航</h4>
                <el-input v-model="episodeSearch" placeholder="搜索剧集..." clearable prefix-icon="Search" size="small" class="episode-search" />
              </div>
              
              <!-- 剧集列表 -->
              <ul class="ep-list">
                <li v-for="(content, ep) in filteredEpisodes" :key="ep" class="ep-item" :class="{ active: currentEpisodeTab === ep }" @click="currentEpisodeTab = ep">
                  <el-icon style="margin-right: 8px"><Film /></el-icon> {{ ep }}
                  <span class="scene-count">({{ getSceneCount(ep) }} 镜)</span>
                </li>
              </ul>
            </div>

            <!-- 内容区域 -->
            <div class="episode-content">
              <!-- 表格布局 -->
              <div v-if="layoutMode === 'table'" class="table-view">
                <el-table
                  :data="pagedData"
                  border
                  stripe
                  class="premium-table script-table"
                  :header-cell-style="{ background: 'var(--input-bg)', color: 'var(--text-main)', fontWeight: 'bold' }"
                >
                  <el-table-column v-for="header in parsedCurrentEpisode.headers" :key="header" :label="header" :prop="header" :min-width="header.includes('镜号') ? '80' : '200'" sortable>
                    <template #default="scope">
                      <div style="white-space: pre-wrap; line-height: 1.6; font-size: 14px">{{ scope.row[header] }}</div>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 视听剧本布局 -->
              <div v-else-if="layoutMode === 'av'" class="av-script-view">
                <div class="av-scene-item" v-for="(scene, index) in pagedData" :key="index">
                  
                  <div class="scene-meta-axis">
                    <div class="shot-badge">SHOT {{ scene['镜号'] || index + 1 }}</div>
                    <div class="location-tag">
                      <el-icon><Location /></el-icon>
                      <span>{{ scene['场景'] || '未知场景' }}</span>
                    </div>
                  </div>

                  <div class="scene-content-split">
                    <div class="av-col visual-col">
                      <div class="col-header">
                        <div class="header-icon-wrap v-bg"><el-icon><VideoCamera /></el-icon></div>
                        <span>画面 (Visual)</span>
                      </div>
                      <div class="col-body">{{ scene['画面内容 (Visual)'] || '暂无画面描述' }}</div>
                    </div>
                    
                    <div class="av-col audio-col">
                      <div class="col-header">
                        <div class="header-icon-wrap a-bg"><el-icon><Microphone /></el-icon></div>
                        <span>声音 & 台词 (Audio)</span>
                      </div>
                      <div class="col-body dialogue-text">{{ scene['台词 (Dialogue) & 音效 (SFX)'] || '暂无声音描述' }}</div>
                    </div>
                  </div>

                </div>
              </div>

              <!-- 分页 -->
              <div v-if="showPagination" class="pagination-container">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[20, 50, 100, 200]"
                  layout="total, sizes, prev, pager, next, jumper"
                  :total="filteredData.length"
                  @size-change="handleSizeChange"
                  @current-change="handleCurrentChange"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="immersiveDialogVisible" :title="`✏️ 沉浸精修 - 方案 ${['A', 'B', 'C'][currentEditIndex]}`" fullscreen destroy-on-close>
      <div class="immersive-editor-container">
        <el-input v-model="tempEditContent" type="textarea" class="immersive-textarea" placeholder="在这里尽情挥洒灵感..." />
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="immersiveDialogVisible = false" size="large">放弃修改</el-button>
          <el-button type="primary" class="btn-hermes" @click="confirmImmersiveEdit" size="large">保存并锁定此方案</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.workflow-engine {
  margin-top: 24px;
}

.premium-steps {
  display: flex;
  align-items: center;
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 32px;
  border: 1px solid var(--border-color);
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
}

.step-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #6c757d;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.step-item.is-active .step-icon {
  background: var(--hermes-primary);
  color: white;
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
  transform: scale(1.1);
}

.step-item.is-done .step-icon {
  background: #28a745;
  color: white;
}

.step-text {
  font-size: 14px;
  font-weight: 500;
  color: #6c757d;
  transition: all 0.3s ease;
}

.step-item.is-active .step-text {
  color: var(--hermes-primary);
  font-weight: 600;
}

.step-line {
  flex: 1;
  height: 2px;
  background: #e9ecef;
  margin: 0 16px;
  position: relative;
}

.step-item.is-done ~ .step-line {
  background: #28a745;
}

.glass-card {
  background: var(--panel-bg);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.creative-input-box {
  margin-bottom: 24px;
}

.box-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: var(--text-main);
  font-size: 14px;
}

.box-header .dot {
  width: 8px;
  height: 8px;
  background: var(--hermes-primary);
  border-radius: 50%;
  margin-right: 8px;
}

.premium-textarea .el-textarea__wrapper {
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.premium-textarea .el-textarea__wrapper:hover,
.premium-textarea .el-textarea__wrapper.is-focus {
  border-color: var(--hermes-primary);
  box-shadow: 0 0 0 2px rgba(227, 112, 13, 0.1);
}

.step-footer {
  margin-top: 24px;
  text-align: center;
}

.step-footer.split {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-hermes {
  background: var(--hermes-primary);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
}

.btn-hermes:hover {
  background: var(--hermes-hover);
  box-shadow: 0 6px 20px rgba(227, 112, 13, 0.4);
  transform: translateY(-2px);
}

.btn-hermes.mega {
  padding: 12px 32px;
  font-size: 16px;
}

.estimate-box {
  background: rgba(227, 112, 13, 0.05);
  border: 1px solid rgba(227, 112, 13, 0.2);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--text-main);
}

.spinner-small {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid var(--hermes-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.ai-terminal {
  background: #111827;
  border-radius: 12px;
  overflow: hidden;
  margin-top: 15px;
  border: 1px solid #374151;
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.2);
}

.terminal-header {
  background: #1f2937;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #374151;
}

.mac-btns {
  display: flex;
  gap: 8px;
}

.mac-btns span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.mac-btns .r { background: #ef4444; }
.mac-btns .y { background: #f59e0b; }
.mac-btns .g { background: #10b981; }

.terminal-header .title {
  flex: 1;
  font-size: 13px;
  color: #9ca3af;
  font-family: 'Courier New', monospace;
}

.terminal-header .status {
  font-size: 12px;
  color: #10b981;
  font-family: 'Courier New', monospace;
}

.terminal-body {
  padding: 24px;
  height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.sys-msg {
  color: #10b981;
  margin-bottom: 12px;
  font-weight: bold;
}

.typewriter-text {
  color: #d1d5db;
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.blink {
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

.acts-grid {
  margin-top: 24px;
}

.pro-tips {
  background: rgba(227, 112, 13, 0.05);
  border: 1px solid rgba(227, 112, 13, 0.2);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 24px;
  font-size: 14px;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
}

.premium-cards-wrapper {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 32px;
  margin-top: 24px;
}

.premium-act-card {
  background: var(--input-bg);
  border: 2px solid var(--border-color);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  min-height: 520px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  overflow: hidden;
}

.premium-act-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(227, 112, 13, 0.15);
  border-color: var(--hermes-primary);
}

.premium-act-card.is-selected {
  border-color: var(--hermes-primary);
  box-shadow: 0 8px 20px rgba(227, 112, 13, 0.2);
}

.card-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--panel-bg);
  border-radius: 14px 14px 0 0;
}

.version-badge {
  background: var(--hermes-primary);
  color: white;
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(227, 112, 13, 0.3);
}

.fullscreen-btn {
  font-size: 13px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.fullscreen-btn:hover {
  background: rgba(227, 112, 13, 0.1);
}

.card-editor-area {
  flex: 1;
  padding: 24px;
  overflow: hidden;
}

.card-editor-area .el-textarea {
  height: 100%;
}

.card-editor-area .el-textarea__wrapper {
  height: 100%;
  background: transparent;
  border: none;
  box-shadow: none;
  resize: none;
  border-radius: 8px;
}

.card-editor-area .el-textarea__inner {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-main);
  padding: 0;
}

.card-bottom-action {
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--panel-bg);
  border-radius: 0 0 14px 14px;
}

.action-select-btn {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  background: var(--input-bg);
  color: var(--text-main);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.action-select-btn:hover {
  border-color: var(--hermes-primary);
  background: rgba(227, 112, 13, 0.05);
}

.action-select-btn.active-btn {
  background: var(--hermes-primary);
  color: white;
  border-color: var(--hermes-primary);
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
}

.config-toolbar-premium {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  padding: 20px 30px;
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.02);
}

.setting-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-box {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--hermes-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-info .title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.setting-info .desc {
  font-size: 12px;
  color: var(--text-sub);
}

.premium-input .el-input__wrapper {
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.premium-input .el-input__wrapper:hover,
.premium-input .el-input__wrapper.is-focus {
  border-color: var(--hermes-primary);
  box-shadow: 0 0 0 2px rgba(227, 112, 13, 0.1);
}

.premium-num-input .el-input-number__decrease,
.premium-num-input .el-input-number__increase {
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  color: var(--text-main);
}

.premium-num-input .el-input__wrapper {
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: none;
}

.action-group {
  display: flex;
  gap: 12px;
}

.outline-editor-layout {
  display: flex;
  gap: 24px;
  margin-top: 24px;
}

.main-editor {
  flex: 1;
}

.ghost-input .el-textarea__wrapper {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  resize: none;
}

.premium-empty-state {
  text-align: center;
  padding: 64px 0;
  background: var(--input-bg);
  border-radius: 0 0 16px 16px;
}

.empty-icon-box {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: var(--hermes-primary);
}

.pulse-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 4px solid transparent;
  border-top: 4px solid var(--hermes-primary);
  border-radius: 50%;
  animation: pulse-ring 2s linear infinite;
}

@keyframes pulse-ring {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 12px;
}

.empty-desc {
  color: var(--text-sub);
  max-width: 500px;
  margin: 0 auto 32px;
  line-height: 1.6;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}

.mega-plain {
  padding: 12px 32px;
  font-size: 16px;
}

.immersive-editor-container {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  padding: 0 40px;
}

.immersive-textarea {
  flex: 1;
  font-size: 16px;
  line-height: 1.8;
  font-family: 'Courier New', monospace;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: var(--panel-bg) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.immersive-textarea .el-textarea__wrapper {
  height: 100% !important;
  border: none !important;
  border-radius: 12px;
  background: var(--input-bg) !important;
  padding: 32px !important;
  box-shadow: none !important;
}

.immersive-textarea .el-textarea__inner {
  font-size: 16px;
  line-height: 1.8;
  color: var(--text-main);
  resize: none;
  background: transparent !important;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 24px 40px;
  border-top: 1px solid var(--border-color);
  background: var(--panel-bg);
  margin-top: 24px;
  border-radius: 12px;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.05);
}

.dialog-footer .el-button {
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.dialog-footer .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.dialog-footer .btn-hermes {
  background: var(--hermes-primary);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
}

.dialog-footer .btn-hermes:hover {
  background: var(--hermes-hover);
  box-shadow: 0 6px 20px rgba(227, 112, 13, 0.4);
}

.fade-in {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 暗黑模式适配 */
.dark-theme .glass-card {
  background: var(--panel-bg);
  border-color: var(--border-color);
}

.dark-theme .premium-textarea .el-textarea__wrapper {
  background: var(--input-bg);
  border-color: var(--border-color);
}

.dark-theme .estimate-box {
  background: rgba(227, 112, 13, 0.1);
  border-color: rgba(227, 112, 13, 0.3);
  color: var(--text-main);
}

.dark-theme .pro-tips {
  background: rgba(227, 112, 13, 0.1);
  border-color: rgba(227, 112, 13, 0.3);
  color: var(--text-main);
}

.dark-theme .premium-act-card {
  background: var(--input-bg);
  border-color: var(--border-color);
}

.dark-theme .card-top-bar {
  background: var(--panel-bg);
  border-color: var(--border-color);
}

.dark-theme .card-bottom-action {
  background: var(--panel-bg);
  border-color: var(--border-color);
}

.dark-theme .action-select-btn {
  background: var(--input-bg);
  border-color: var(--border-color);
  color: var(--text-main);
}

.dark-theme .config-toolbar-premium {
  background: var(--input-bg);
  border-color: var(--border-color);
}

.dark-theme .setting-info .title {
  color: var(--text-main);
}

.dark-theme .setting-info .desc {
  color: var(--text-sub);
}

.dark-theme .premium-input .el-input__wrapper {
  background: var(--input-bg);
  border-color: var(--border-color);
}

.dark-theme .premium-num-input .el-input-number__decrease,
.dark-theme .premium-num-input .el-input-number__increase {
  background: var(--input-bg);
  border-color: var(--border-color);
  color: var(--text-main);
}

.dark-theme .premium-num-input .el-input__wrapper {
  background: var(--input-bg);
  border-color: var(--border-color);
}

.dark-theme .premium-empty-state {
  background: var(--input-bg);
}

.dark-theme .empty-title {
  color: var(--text-main);
}

.dark-theme .empty-desc {
  color: var(--text-sub);
}

.dark-theme .immersive-textarea .el-textarea__wrapper {
  background: var(--input-bg) !important;
}

.dark-theme .dialog-footer {
  background: var(--panel-bg);
  border-color: var(--border-color);
}

/* 分镜渲染结果布局 */
.results-showcase {
  padding: 24px;
  background: var(--panel-bg);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.results-showcase:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.showcase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.showcase-header .title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 10px;
}

.showcase-header .title .dot {
  width: 10px;
  height: 10px;
  background: linear-gradient(135deg, #28a745, #20c997);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.showcase-header .title .count-badge {
  margin-left: 12px;
  background: var(--input-bg);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: normal;
  color: var(--text-sub);
}

.showcase-header .actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.showcase-header .actions .el-button {
  transition: all 0.3s ease;
}

.showcase-header .actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.showcase-body {
  display: flex;
  min-height: 600px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
  background: var(--input-bg);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
}

.episode-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--panel-bg), rgba(227, 112, 13, 0.03));
  border-right: 1px solid var(--border-color);
  overflow-y: auto;
  padding: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.episode-sidebar::-webkit-scrollbar {
  width: 8px;
}

.episode-sidebar::-webkit-scrollbar-track {
  background: var(--input-bg);
  border-radius: 4px;
}

.episode-sidebar::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.episode-sidebar::-webkit-scrollbar-thumb:hover {
  background: var(--hermes-primary);
}

.ep-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.ep-item {
  padding: 16px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-main);
  position: relative;
  overflow: hidden;
  background: var(--panel-bg);
}

.ep-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: transparent;
  transition: all 0.3s ease;
}

.ep-item:hover {
  background: linear-gradient(90deg, rgba(227, 112, 13, 0.1), var(--panel-bg));
  padding-left: 28px;
  transform: translateX(4px);
}

.ep-item:hover::before {
  background: var(--hermes-primary);
  box-shadow: 0 0 12px rgba(227, 112, 13, 0.5);
}

.ep-item.active {
  background: linear-gradient(90deg, var(--hermes-primary), rgba(227, 112, 13, 0.9));
  color: white;
  padding-left: 28px;
  box-shadow: 0 4px 16px rgba(227, 112, 13, 0.4);
  transform: translateX(4px);
}

.ep-item.active::before {
  background: white;
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.5);
}

.ep-item .el-icon {
  margin-right: 12px;
  font-size: 18px;
  transition: all 0.3s ease;
}

.ep-item:hover .el-icon {
  transform: scale(1.1);
}

.episode-content {
  flex: 1;
  padding: 16px;
  background: var(--panel-bg);
  overflow: auto;
}

.episode-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.episode-content::-webkit-scrollbar-track {
  background: var(--input-bg);
  border-radius: 4px;
}

.episode-content::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.episode-content::-webkit-scrollbar-thumb:hover {
  background: var(--hermes-primary);
}

.script-table {
  width: 100%;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
}

.script-table .el-table__header-wrapper th {
  background: linear-gradient(135deg, var(--hermes-primary), rgba(227, 112, 13, 0.9));
  font-weight: 600;
  color: white;
  padding: 14px 16px;
  border-bottom: 2px solid var(--hermes-primary);
  text-align: center;
  font-size: 14px;
}

.script-table .el-table__body-wrapper td {
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-color);
  line-height: 1.6;
  white-space: normal;
  word-wrap: break-word;
  min-height: 70px;
  font-size: 14px;
}

.script-table .el-table__body-wrapper tr:hover {
  background: rgba(227, 112, 13, 0.08);
  transform: scale(1.01);
  transition: all 0.3s ease;
}

/* 视听剧本布局样式 */
.av-script-view {
  display: flex;
  flex-direction: column;
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.av-scene-item {
  display: flex;
  gap: 24px;
  position: relative;
  padding-bottom: 32px;
}

/* 左侧时间线轴线 */
.av-scene-item::after {
  content: '';
  position: absolute;
  left: 36px; /* 对齐左侧中心 */
  top: 40px;
  bottom: 0;
  width: 2px;
  background: var(--border-color);
  z-index: 1;
}
.av-scene-item:last-child::after {
  display: none;
}

.scene-meta-axis {
  width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  z-index: 2;
}

.shot-badge {
  background: var(--hermes-primary);
  color: white;
  font-family: 'Courier New', Courier, monospace;
  font-size: 16px;
  font-weight: 900;
  padding: 8px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3);
  letter-spacing: 1px;
}

.location-tag {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: var(--text-sub);
  background: var(--input-bg);
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  line-height: 1.4;
}
.location-tag .el-icon {
  margin-top: 2px;
  color: var(--hermes-primary);
}

.scene-content-split {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  background: white;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.04);
  overflow: hidden;
  transition: all 0.3s;
}
.scene-content-split:hover {
  border-color: rgba(227, 112, 13, 0.4);
  box-shadow: 0 8px 30px rgba(227, 112, 13, 0.1);
  transform: translateY(-2px);
}

.av-col {
  display: flex;
  flex-direction: column;
}

.visual-col {
  border-right: 1px dashed var(--border-color);
}

.col-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: var(--input-bg);
  border-bottom: 1px solid var(--border-color);
  font-weight: 700;
  font-size: 14px;
  color: var(--text-main);
}

.header-icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: white;
}
.v-bg { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.a-bg { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }

.col-body {
  padding: 20px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-main);
  white-space: pre-wrap;
}

/* 台词区稍微做一下背景区分，符合剧本视觉习惯 */
.dialogue-text {
  background: rgba(0,0,0,0.015);
  font-weight: 500;
}

/* 响应式调整 */
@media (max-width: 1100px) {
  .scene-content-split {
    grid-template-columns: 1fr;
  }
  .visual-col {
    border-right: none;
    border-bottom: 1px dashed var(--border-color);
  }
}
@media (max-width: 768px) {
  .av-scene-item {
    flex-direction: column;
    gap: 16px;
  }
  .av-scene-item::after { display: none; }
  .scene-meta-axis {
    width: 100%;
    flex-direction: row;
    align-items: center;
  }
  .shot-badge {
    font-size: 14px;
    padding: 6px 12px;
  }
  .location-tag {
    font-size: 12px;
    padding: 6px 10px;
  }
  .col-header {
    padding: 12px 16px;
    font-size: 13px;
  }
  .col-body {
    padding: 16px;
    font-size: 13px;
  }
}

.script-table .el-table__body-wrapper tr {
  transition: all 0.3s ease;
}

.script-table .el-table__body-wrapper tr:nth-child(even) {
  background: rgba(0, 0, 0, 0.02);
}

.script-table .el-table__body-wrapper tr:nth-child(odd) {
  background: var(--panel-bg);
}

/* 搜索和筛选区域 */
.search-filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--input-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.search-section {
  flex: 1;
  margin-right: 16px;
}

.search-input {
  width: 100%;
  max-width: 400px;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-select {
  min-width: 200px;
}

/* 布局控制区域 */
.view-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 12px 16px;
  background: rgba(227, 112, 13, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(227, 112, 13, 0.2);
}

.layout-toggle {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-label {
  font-weight: 500;
  color: var(--text-main);
  font-size: 14px;
}

.view-info {
  font-size: 14px;
  color: var(--text-sub);
  font-weight: 500;
}

/* 侧边栏头部 */
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 16px;
}

.sidebar-header h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-main);
}

.episode-search {
  width: 100%;
}

/* 场景计数 */
.scene-count {
  font-size: 12px;
  color: var(--text-sub);
  margin-left: auto;
  background: rgba(0, 0, 0, 0.08);
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.ep-item:hover .scene-count {
  background: rgba(227, 112, 13, 0.2);
  color: var(--hermes-primary);
}

.ep-item.active .scene-count {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
}

/* 表格视图 */
.table-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.table-view .el-table {
  flex: 1;
  margin-bottom: 20px;
}

/* 卡片视图 */
.card-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.scene-card {
  background: linear-gradient(135deg, var(--panel-bg), rgba(227, 112, 13, 0.02));
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.scene-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, var(--hermes-primary), rgba(227, 112, 13, 0.8));
  border-radius: 4px 0 0 4px;
}

.scene-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-3px);
  border-color: var(--hermes-primary);
}

.scene-card-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.scene-number {
  font-weight: 700;
  color: var(--hermes-primary);
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.scene-number::before {
  content: '🎬';
  font-size: 14px;
}

.scene-location {
  font-size: 14px;
  color: var(--text-sub);
  background: rgba(227, 112, 13, 0.1);
  padding: 6px 16px;
  border-radius: 16px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.scene-card:hover .scene-location {
  background: rgba(227, 112, 13, 0.2);
  color: var(--hermes-primary);
}

.scene-card-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.scene-content h5,
.scene-dialogue h5 {
  margin: 0 0 12px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
}

.scene-content h5::before {
  content: '🖼️';
  font-size: 14px;
}

.scene-dialogue h5::before {
  content: '💬';
  font-size: 14px;
}

.scene-content p,
.scene-dialogue p {
  margin: 0;
  line-height: 1.6;
  font-size: 14px;
  color: var(--text-main);
  white-space: pre-wrap;
  padding: 12px;
  background: var(--input-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.scene-card:hover .scene-content p,
.scene-card:hover .scene-dialogue p {
  border-color: var(--hermes-primary);
  background: rgba(227, 112, 13, 0.02);
}

/* 分页容器 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  margin-top: auto;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .episode-sidebar {
    width: 180px;
  }
  
  .showcase-body {
    min-height: 500px;
  }
  
  .card-view {
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  }
}

@media (max-width: 768px) {
  .showcase-body {
    flex-direction: column;
  }
  
  .episode-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    max-height: 200px;
  }
  
  .showcase-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .showcase-header .actions {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .showcase-header .actions .el-button {
    flex: 1;
    min-width: 120px;
  }
  
  .search-filter-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .search-section {
    margin-right: 0;
  }
  
  .filter-section {
    justify-content: space-between;
  }
  
  .view-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .layout-toggle {
    justify-content: center;
  }
  
  .card-view {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup>
import { ref, computed, onMounted, nextTick, watch, inject } from 'vue'
import { v4 as uuidv4 } from 'uuid'
import { engine } from '../api/engine'
import { apiUrl } from '../api/base'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import * as XLSX from 'xlsx'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { Film, Select, InfoFilled, Download, Files, FullScreen, Setting, VideoPlay, VideoCamera, Search, Refresh } from '@element-plus/icons-vue'

// 注入全局配置
const config = inject('config');

// API Key验证函数
const validateApiKey = () => {
  if (!config) return true;
  if (config.provider === 'Mock (演示)') return true;
  if (!config.apiKey || config.apiKey.trim() === '') {
    ElMessage.warning('请先在左侧配置并连接API Key！'); return false;
  }
  return true;
};

// 监听provider变化，从Mock模式切换到非Mock模式时清空生成结果
watch(() => config?.provider, (newProvider, oldProvider) => {
  if (oldProvider === 'Mock (演示)' && newProvider !== 'Mock (演示)') {
    // 从Mock模式切换到非Mock模式，清空之前的生成结果
    isGenerating.value = false;
    isGeneratingStoryboard.value = false;
    tempActsText.value = '';
    threeActOptions.value = [];
    selectedActIndex.value = null;
    scriptOutline.value = '';
    finalResults.value = {};
    currentEpisodeTab.value = '';
    progressMsg.value = '';
    progressVal.value = 0;
    isTaskStopped.value = false;
  }
});

const activeStep = ref(0);
const creativeIdea = ref(''); 
const tempActsText = ref('');
const threeActOptions = ref([]);
const selectedActIndex = ref(null);
const scriptOutline = ref('');
const totalEpisodes = ref(10); 
const isGenerating = ref(false);
const isGeneratingStoryboard = ref(false);
const finalResults = ref({});
const currentEpisodeTab = ref('');

// 新增：搜索和筛选相关
const searchQuery = ref('');
const sceneFilter = ref('');
const episodeSearch = ref('');
const layoutMode = ref('table');
const showPagination = ref(false); // 控制是否显示分页

// 新增：分页相关
const currentPage = ref(1);
const pageSize = ref(20);
const progressMsg = ref('');
const progressVal = ref(0);
const currentTaskId = ref('');
const terminalBody = ref(null);

// 🔴 新增：任务阻断标记，防止紧急阻断后继续处理结果
const isTaskStopped = ref(false);

const immersiveDialogVisible = ref(false);
const currentEditIndex = ref(0);
const tempEditContent = ref('');

const estimatedTime = ref('约 1 分钟');
const estimatedStoryboardTime = ref('约 3 分钟');
// 新增：剧本名称（动态）
const scriptName = ref('剧本生成项目');
let timer = null;

onMounted(async () => {
  try {
    const res = await axios.get(apiUrl('/api/script/default_creative'));
    if (res.data && res.data.creative) creativeIdea.value = res.data.creative;
  } catch (err) { creativeIdea.value = "无法加载默认创意，请手动输入。"; }
});

const openImmersive = (index) => {
  currentEditIndex.value = index;
  tempEditContent.value = threeActOptions.value[index];
  immersiveDialogVisible.value = true;
};

const confirmImmersiveEdit = () => {
  threeActOptions.value[currentEditIndex.value] = tempEditContent.value;
  immersiveDialogVisible.value = false;
  ElMessage.success("精修内容已保存！");
};

const stopTask = () => {
  if (currentTaskId.value) engine.stopTask(currentTaskId.value);
  // 🔴 关键：设置任务阻断标记，防止后续流回调继续处理
  isTaskStopped.value = true;
  isGenerating.value = false;
  isGeneratingStoryboard.value = false;
  progressMsg.value = "";
  if(timer) clearInterval(timer);
  ElMessage.warning('任务已紧急阻断');
};

const goBack = () => {
  if (isGenerating.value || isGeneratingStoryboard.value) {
    ElMessageBox.confirm('🚀AI正在执行高强度运算，回退将立即强制中断...', '强制阻断确认', {
      confirmButtonText: '确定中断并回退',
      cancelButtonText: '点错了，继续生成',
      type: 'warning',
    })
    .then(() => {
      stopTask();
      activeStep.value--;
      ElMessage.success('🚀当前AI任务已物理阻断，算力已回收');
    })
    .catch(() => {});
  } else {
    if (activeStep.value > 0) activeStep.value--;
  }
};

const goToStep4AndGenerate = () => {
  activeStep.value = 3;
  setTimeout(() => {
    if (Object.keys(finalResults.value).length === 0 && !isGeneratingStoryboard.value) {
      generateStoryboard();
    }
  }, 300);
};

// 🚀 核心修复：史诗级增强版的切割算法！
const generateThreeActs = () => {
  if (!creativeIdea.value) return ElMessage.warning("请填写创意");
  // 🔴 重置任务阻断标记，开始新任务
  isTaskStopped.value = false;
  isGenerating.value = true; activeStep.value = 1; tempActsText.value = ""; threeActOptions.value = []; progressMsg.value = ""; progressVal.value = 0;
  currentTaskId.value = `task_${uuidv4().slice(0, 8)}`;
  
  // 估算目标文本长度（根据创意长度动态估算）
  const estimateTargetLength = Math.max(1500, creativeIdea.value.length * 8);
  
  const startTime = Date.now();
  estimatedTime.value = "计算中...";
  if(timer) clearInterval(timer);
  timer = setInterval(() => {
    const elapsedTime = (Date.now() - startTime) / 1000;
    const currentLength = tempActsText.value.length;
    
    if (currentLength > 0) {
      const progress = Math.min(currentLength / estimateTargetLength, 0.99);
      if (progress > 0 && progress < 1) {
        const totalEst = elapsedTime / progress;
        const remaining = Math.max(0, totalEst - elapsedTime);
        // 直接显示为分钟
      estimatedTime.value = `约 ${Math.ceil(remaining / 60)} 分钟`;
        progressVal.value = Math.floor(progress * 100);
      } else {
        estimatedTime.value = `已用时 ${Math.ceil(elapsedTime / 60)} 分钟...`;
      }
    } else {
      estimatedTime.value = `已用时 ${Math.ceil(elapsedTime / 60)} 分钟...`;
    }
  }, 1000);
  
  engine.fetchStream('script/generate_acts', { task_id: currentTaskId.value, idea: creativeIdea.value }, 
    (chunk) => { 
      // 🔴 检查任务是否已被阻断，阻断后不再处理数据
      if (isTaskStopped.value) return;
      tempActsText.value += chunk; 
    }, 
    (msg, val) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) return;
      progressMsg.value = msg; 
      if (val) progressVal.value = val; 
    }, 
    () => { 
      // 🔴 关键：任务完成回调前先检查阻断标记
      if (isTaskStopped.value) {
        console.log('⏹️ 任务已被紧急阻断，跳过结果处理');
        return;
      }
      progressVal.value = 100;
      // 暴力正则：无论是 ---、***、[Version 1] 还是 方案 A：，统统切开！
      let parts = tempActsText.value.split(/\n\s*[-_*]{3,}\s*\n|\[Version \d\]|\*\*方案\s*[A-Z]\s*[：:]\*\*/i);
      
      parts = parts.map(v => v.trim()).filter(v => v.length > 20);
      
      // 兜底机制：就算模型发癫只输出了一整块，也强行补齐 3 个占位符，保证 UI 绝对不会塌陷
      while(parts.length < 3) {
         parts.push("AI 似乎漏写了这个方案的内容，您可以点击此处自行发挥灵感，或者返回上一步重新生成...");
      }
      
      threeActOptions.value = parts.slice(0, 3); 
      isGenerating.value = false; 
      clearInterval(timer);
      ElMessage.success("为你生成了三个备选方案！");
    }, 
    (err) => { 
      // 🔴 检查任务是否已被阻断，如果是阻断则不显示错误信息
      if (isTaskStopped.value) return;
      isGenerating.value = false; 
      ElMessage.error('生成失败，请检查配置后重试'); 
      activeStep.value = 0; 
      clearInterval(timer); 
    }
  );
};

const generateOutline = () => {
  // 🔴 验证API Key
  if (!validateApiKey()) return;
  // 🔴 重置任务阻断标记，开始新任务
  isTaskStopped.value = false;
  isGenerating.value = true; scriptOutline.value = ""; progressMsg.value = ""; progressVal.value = 0;
  currentTaskId.value = `task_${uuidv4().slice(0, 8)}`;
  
  const startTime = Date.now();
  estimatedTime.value = "计算中...";
  if(timer) clearInterval(timer);
  timer = setInterval(() => {
    const elapsedTime = (Date.now() - startTime) / 1000;
    const progress = progressVal.value / 100;
    if (progress > 0 && progress < 1) {
      const totalEst = elapsedTime / progress;
      const remaining = Math.max(0, totalEst - elapsedTime);
      // 直接显示为分钟
      estimatedTime.value = `约 ${Math.ceil(remaining / 60)} 分钟`;
    } else {
      estimatedTime.value = `已用时 ${Math.ceil(elapsedTime / 60)} 分钟...`;
    }
  }, 2000);
  
  engine.fetchStream('script/generate_outline', { 
    task_id: currentTaskId.value, act_structure: threeActOptions.value[selectedActIndex.value], total_episodes: totalEpisodes.value 
  }, 
    (chunk) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) return;
      scriptOutline.value += chunk; 
    }, 
    (msg, val) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) return;
      progressMsg.value = msg; 
      progressVal.value = val || progressVal.value; 
    }, 
    () => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) {
        console.log('⏹️ 任务已被紧急阻断，跳过结果处理');
        return;
      }
      isGenerating.value = false; 
      clearInterval(timer); 
      // 自动从大纲中提取标题
      const extractedTitle = extractTitleFromOutline(scriptOutline.value);
      if (extractedTitle) {
        scriptName.value = extractedTitle;
        ElMessage.success(`大纲生成完成！已自动提取标题：${extractedTitle}`);
      } else {
        ElMessage.success("大纲生成完成！");
      }
    },
    (err) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) return;
      isGenerating.value = false; 
      ElMessage.error('生成失败，请检查配置后重试'); 
      clearInterval(timer); 
    }
  );
};

const generateStoryboard = () => {
  // 🔴 验证API Key
  if (!validateApiKey()) return;
  // 🔴 重置任务阻断标记，开始新任务
  isTaskStopped.value = false;
  isGeneratingStoryboard.value = true; finalResults.value = {}; progressVal.value = 0;
  currentTaskId.value = `task_${uuidv4().slice(0, 8)}`;
  
  const startTime = Date.now();
  estimatedStoryboardTime.value = "神经引擎预热中...";
  if(timer) clearInterval(timer);
  timer = setInterval(() => {
    const elapsedTime = (Date.now() - startTime) / 1000;
    const progress = progressVal.value / 100;
    if (progress > 0 && progress < 1) {
      const totalEst = elapsedTime / progress;
      const remaining = Math.max(0, totalEst - elapsedTime);
      // 直接显示为分钟
      estimatedStoryboardTime.value = `约 ${Math.ceil(remaining / 60)} 分钟`;
    } else {
      estimatedStoryboardTime.value = `已用时 ${Math.ceil(elapsedTime / 60)} 分钟...`;
    }
  }, 2000);
  
  engine.fetchStream('script/generate_storyboard', { 
    task_id: currentTaskId.value, outline_text: scriptOutline.value, total_episodes: totalEpisodes.value 
  }, 
    null, 
    (msg, val) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) return;
      progressMsg.value = msg; 
      progressVal.value = val || progressVal.value; 
    },
    (results) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) {
        console.log('⏹️ 任务已被紧急阻断，跳过结果处理');
        return;
      }
      finalResults.value = results; 
      const eps = Object.keys(results);
      if (eps.length > 0) currentEpisodeTab.value = eps[0];
      isGeneratingStoryboard.value = false; 
      clearInterval(timer);
      ElMessage.success("分镜全集渲染完毕！");
    },
    (err) => { 
      // 🔴 检查任务是否已被阻断
      if (isTaskStopped.value) return;
      isGeneratingStoryboard.value = false; 
      ElMessage.error('生成失败，请检查配置后重试'); 
      clearInterval(timer); 
    }
  );
};

const extractTitleFromOutline = (outlineText) => {
  if (!outlineText) return null;
  const lines = outlineText.trim().split(/\r?\n/);
  for (let line of lines) {
    line = line.trim();
    if (!line) continue;
    // 匹配常见的标题格式：## 标题、**标题**、# 标题、「标题」、《标题》、标题：等
    const titleMatch = line.match(/^(?:##?\s*|\*\*|#\s*)?([^\s*#「《【][^\n\r]{2,50}?)(?:\*\*|：|:|，|。|$)/);
    if (titleMatch && titleMatch[1]) {
      const title = titleMatch[1].trim();
      // 过滤掉太短或太长的
      if (title.length >= 2 && title.length <= 50) {
        return title;
      }
    }
  }
  // 如果没找到，试试第一行非空行
  for (let line of lines) {
    line = line.trim();
    if (line && line.length >= 2 && line.length <= 50) {
      return line.replace(/^[#*《「【]|[》」】]$/g, '').trim();
    }
  }
  return null;
};

const parseCSV = (csvText) => {
  if (!csvText) return { headers: [], data: [] };
  const lines = csvText.trim().split(/\r?\n/);
  if (lines.length === 0) return { headers: [], data: [] };
  const parseLine = (line) => {
    let result = [], cur = '', inQuote = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') inQuote = !inQuote;
      else if (line[i] === ',' && !inQuote) { result.push(cur); cur = ''; }
      else cur += line[i];
    }
    result.push(cur);
    return result.map((s) => s.replace(/^"|"$/g, '').replace(/""/g, '"'));
  };
  const headers = parseLine(lines[0]);
  const data = lines.slice(1).map((line) => {
    const values = parseLine(line); let obj = {};
    headers.forEach((h, i) => (obj[h] = values[i] || ''));
    return obj;
  }).filter(item => {
    // 过滤掉可能的重复表头行
    const isHeaderRow = headers.every(header => item[header] === header);
    // 过滤掉空行
    const isEmptyRow = Object.values(item).every(value => value.trim() === '');
    return !isHeaderRow && !isEmptyRow;
  });
  return { headers, data };
};

const parsedCurrentEpisode = computed(() => {
  if (!currentEpisodeTab.value || !finalResults.value[currentEpisodeTab.value]) return { headers: [], data: [] };
  return parseCSV(finalResults.value[currentEpisodeTab.value]);
});

// 过滤后的剧集列表
const filteredEpisodes = computed(() => {
  let episodes = finalResults.value;
  
  // 如果有搜索关键词，先过滤
  if (episodeSearch.value) {
    const searchLower = episodeSearch.value.toLowerCase();
    const filtered = {};
    for (const [ep, content] of Object.entries(finalResults.value)) {
      if (ep.toLowerCase().includes(searchLower)) {
        filtered[ep] = content;
      }
    }
    episodes = filtered;
  }
  
  // 对剧集进行数值排序
  const sortedEpisodes = {};
  Object.keys(episodes)
    .sort((a, b) => {
      // 提取剧集编号并转换为数字进行比较
      const numA = parseInt(a.match(/\d+/)?.[0] || '0');
      const numB = parseInt(b.match(/\d+/)?.[0] || '0');
      return numA - numB;
    })
    .forEach(key => {
      sortedEpisodes[key] = episodes[key];
    });
  
  return sortedEpisodes;
});

// 唯一场景列表
const uniqueScenes = computed(() => {
  if (!currentEpisodeTab.value || !finalResults.value[currentEpisodeTab.value]) {
    return [];
  }
  const data = parseCSV(finalResults.value[currentEpisodeTab.value]).data;
  const scenes = new Set();
  data.forEach(item => {
    if (item['场景']) {
      scenes.add(item['场景']);
    }
  });
  return Array.from(scenes).sort();
});

// 过滤后的场景列表
const filteredScenes = computed(() => {
  if (!sceneFilter.value) {
    return uniqueScenes.value;
  }
  return uniqueScenes.value.filter(scene => scene.includes(sceneFilter.value));
});

// 过滤后的数据
const filteredData = computed(() => {
  const data = parsedCurrentEpisode.value.data;
  let filtered = data;
  
  // 应用搜索和筛选
  if (searchQuery.value || sceneFilter.value) {
    filtered = data.filter(item => {
      const matchesSearch = !searchQuery.value || 
        (item['画面内容 (Visual)'] && item['画面内容 (Visual)'].toLowerCase().includes(searchQuery.value.toLowerCase())) ||
        (item['台词 (Dialogue) & 音效 (SFX)'] && item['台词 (Dialogue) & 音效 (SFX)'].toLowerCase().includes(searchQuery.value.toLowerCase()));
      const matchesScene = !sceneFilter.value || 
        (item['场景'] && item['场景'] === sceneFilter.value);
      return matchesSearch && matchesScene;
    });
  }
  
  // 去重：根据镜号和场景组合去重
  const uniqueFiltered = [];
  const seen = new Set();
  
  filtered.forEach(item => {
    const key = `${item['镜号']}-${item['场景']}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueFiltered.push(item);
    }
  });
  
  // 按镜号排序
  return uniqueFiltered.sort((a, b) => {
    const numA = parseInt(a['镜号']) || 0;
    const numB = parseInt(b['镜号']) || 0;
    return numA - numB;
  });
});

// 分页后的数据
const pagedData = computed(() => {
  if (!showPagination.value) {
    return filteredData.value;
  }
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredData.value.slice(start, end);
});

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
};

// 处理筛选
const handleFilter = () => {
  currentPage.value = 1;
};

// 重置筛选
const resetFilters = () => {
  searchQuery.value = '';
  sceneFilter.value = '';
  currentPage.value = 1;
};

// 切换布局
const switchLayout = () => {
  currentPage.value = 1;
};

// 处理分页大小变化
const handleSizeChange = (size) => {
  pageSize.value = size;
  currentPage.value = 1;
};

// 处理当前页变化
const handleCurrentChange = (page) => {
  currentPage.value = page;
};

// 获取场景数量
const getSceneCount = (ep) => {
  if (!finalResults.value[ep]) {
    return 0;
  }
  const data = parseCSV(finalResults.value[ep]).data;
  return data.length;
};

const exportCurrentExcel = () => {
  if (!parsedCurrentEpisode.value.data.length) return;
  const ws = XLSX.utils.json_to_sheet(parsedCurrentEpisode.value.data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, currentEpisodeTab.value);
  // 使用动态剧本名称
  XLSX.writeFile(wb, `${scriptName.value}_${currentEpisodeTab.value}_分镜脚本.xlsx`);
  ElMessage.success(`✅ ${currentEpisodeTab.value} 导出成功！`);
};

const exportAllSheetsExcel = () => {
  if (Object.keys(finalResults.value).length === 0) return;
  ElMessage.info('📊 正在生成多Sheet Excel文件，请稍候...');

  const wb = XLSX.utils.book_new();

  for (const [ep, csvContent] of Object.entries(finalResults.value)) {
    const parsed = parseCSV(csvContent);
    const ws = XLSX.utils.json_to_sheet(parsed.data);
    XLSX.utils.book_append_sheet(wb, ws, ep);
  }

  // 使用动态剧本名称
  XLSX.writeFile(wb, `${scriptName.value}_分镜脚本全集.xlsx`);
  ElMessage.success('🎉 多Sheet Excel文件导出成功！');
};

const exportBatchZip = () => {
  if (Object.keys(finalResults.value).length === 0) return;
  ElMessage.info('📦 正在极速打包 ZIP，请稍候...');

  const zip = new JSZip();
  // 使用动态剧本名称
  const baseName = scriptName.value;
  const folder = zip.folder(`${baseName}_分镜剧本全集`);

  for (const [ep, csvContent] of Object.entries(finalResults.value)) {
    const parsed = parseCSV(csvContent);
    const ws = XLSX.utils.json_to_sheet(parsed.data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, ep);
    // 将 Excel 转为二进制流存入 ZIP
    const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    folder.file(`${baseName}_${ep}_分镜脚本.xlsx`, excelBuffer);
  }

  zip.generateAsync({ type: 'blob' }).then((content) => {
    saveAs(content, `${baseName}_分镜剧本全集.zip`);
    ElMessage.success('🎉 ZIP 打包下载完成！');
  });
};

watch([tempActsText, scriptOutline], async () => {
  await nextTick();
  if (terminalBody.value) terminalBody.value.scrollTop = terminalBody.value.scrollHeight;
});
</script>
