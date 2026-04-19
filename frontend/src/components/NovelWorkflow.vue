<template>
  <div class="workflow-engine">
    <div class="premium-steps">
      <div class="step-item" :class="{ 'is-active': activeStep === 0, 'is-done': activeStep > 0 }">
        <div class="step-icon">1</div>
        <span class="step-text">数据载入</span>
      </div>
      <div class="step-line"></div>
      <div class="step-item" :class="{ 'is-active': activeStep === 1, 'is-done': activeStep > 1 }">
        <div class="step-icon">2</div>
        <span class="step-text">大纲解析</span>
      </div>
      <div class="step-line"></div>
      <div class="step-item" :class="{ 'is-active': activeStep === 2 }">
        <div class="step-icon">3</div>
        <span class="step-text">分镜渲染</span>
      </div>
    </div>

    <transition name="fade-slide" mode="out-in">
      <div v-if="activeStep === 0" class="glass-card">
        <el-upload
          action="/api/upload_novel"
          :show-file-list="false"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :on-change="handleUploadChange"
          :on-exceed="handleUploadExceed"
          :before-upload="beforeUpload"
          drag
          class="upload-area"
        >
          <div class="premium-upload-container" :class="{ 'is-success-bg': uploadedFileName }">
            <div v-if="!uploadedFileName">
              <div class="upload-icon-wrapper">
                <el-icon><Document /></el-icon>
              </div>
              <h3 class="upload-title">导入剧本源数据</h3>
              <p class="upload-desc">支持 .xlsx / .csv 格式，引擎将自动清洗并识别结构</p>
              <el-button class="btn-hermes round-btn" size="large">
                <el-icon style="margin-right: 8px"><FolderOpened /></el-icon> 浏览并选取文件
              </el-button>
            </div>

            <div v-else class="upload-success-state">
              <div class="upload-icon-wrapper success-icon">
                <el-icon><Select /></el-icon>
              </div>
              <h3 class="upload-title" style="color: #2ecc71">文件解析完毕</h3>

              <div class="file-name-badge">
                <el-icon style="margin-right: 6px; font-size: 18px"><DocumentChecked /></el-icon>
                {{ uploadedFileName }}
              </div>
              <p class="upload-desc" style="margin-top: 20px; font-size: 13px">点击该区域可重新选择文件</p>
            </div>
          </div>
        </el-upload>

        <div v-if="previewData.length" class="preview-box fade-in">
          <div class="box-header"><span class="dot"></span> 数据结构嗅探完毕 (共 {{ totalRows }} 章节，Top 10 预览)</div>

          <el-table
            :data="previewData"
            border
            stripe
            class="premium-table"
            style="width: 100%; border-radius: 8px; overflow: hidden"
            :header-cell-style="{ background: 'var(--input-bg)', color: 'var(--text-main)', fontWeight: 'bold' }"
          >
            <el-table-column
              v-for="(col, index) in tableCols"
              :key="index"
              :label="getColumnLabel(col)"
              :min-width="index === 0 ? '150' : '400'"
            >
              <template #default="scope">
                <div class="cell-content">
                  <div class="text-clamp">{{ scope.row[index] }}</div>
                  <el-button
                    v-if="scope.row[index] && scope.row[index].toString().length > 80"
                    type="primary"
                    link
                    size="small"
                    @click="openFullText(scope.row[index])"
                    style="margin-top: 6px; font-weight: bold"
                  >
                    <el-icon style="margin-right: 4px"><ZoomIn /></el-icon>查看全文
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="action-bar">
            <el-button class="btn-hermes" @click="activeStep = 1">
              确认数据无误，下一步 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div v-else-if="activeStep === 1" class="glass-card">
        <div class="config-toolbar">
          <div class="setting-item">
            <span class="label" style="margin-right: 12px; font-weight: bold; color: var(--text-main)"
              >🎯 动态目标集数:</span
            >
            <el-input-number v-model="totalEpisodes" :min="1" :max="200" class="premium-num-input" />
          </div>
          <div class="action-group">
            <el-button class="btn-hermes" @click="generateOutline" :loading="isGenerating" v-if="!isGenerating">
              ▶ 启动智能大纲提炼
            </el-button>
            <el-button type="danger" @click="stopTask" v-else class="btn-pulse"> ■ 紧急阻断任务 </el-button>
          </div>
        </div>

        <div v-if="isGenerating" class="estimate-box">
          <span class="spinner-small"></span>
          系统正在提炼压缩庞大剧情... <strong>预计用时: {{ estimatedTime }}</strong
          >，请耐心等待。
        </div>

        <div class="ai-terminal" v-if="isGenerating">
          <div class="terminal-header">
            <div class="mac-btns"><span class="r"></span><span class="y"></span><span class="g"></span></div>
            <span class="title">ScriptMaster_Engine_v2.exe</span>
            <span class="status blink">🟢 Running</span>
          </div>
          <div class="terminal-body" ref="terminalBody">
            <div v-if="progressMsg" class="sys-msg">> {{ progressMsg }} <span class="blink">_</span></div>
            <pre class="typewriter-text">{{ outlineText }}</pre>
          </div>
        </div>

        <div class="editor-box fade-in" v-if="!isGenerating && outlineText">
          <div class="box-header" v-if="!outlineError"><span class="dot g"></span> 大纲生成完毕，您可以直接在此处进行文本修改：</div>
          <div class="box-header error" v-else><span class="dot r"></span> 生成失败：</div>
          <el-input
            v-model="outlineText"
            type="textarea"
            :rows="18"
            placeholder="分集大纲内容..."
            class="premium-textarea"
            :class="{ 'error-textarea': outlineError }"
          />
        </div>

        <div class="action-bar split" v-if="!isGenerating && outlineText">
          <div>
            <el-button plain @click="goBack">返回上一步</el-button>
            <el-button
              plain
              @click="
                activeStep = 0;
                uploadedFileName = '';
              "
              >重新上传</el-button
            >
            <el-button type="primary" plain @click="exportWord">📥 导出大纲为 Word</el-button>
          </div>
          <el-button class="btn-hermes" @click="activeStep = 2">大纲核对无误，开始分镜渲染</el-button>
        </div>
      </div>

      <div v-else-if="activeStep === 2" class="glass-card" style="padding: 0">
        
        <div class="center-action" v-if="!isGeneratingStoryboard && Object.keys(finalResults).length === 0" style="padding: 80px">
          <el-button plain @click="goBack" style="margin-bottom: 20px">返回上一步</el-button>
          <el-button class="btn-hermes mega" @click="generateStoryboard">
            🚀 启动工业级分镜渲染引擎 (共 {{ totalEpisodes }} 集)
          </el-button>
        </div>

        <div v-if="isGeneratingStoryboard" class="rendering-status" style="margin: 40px">
          <div class="spinner"></div>
          <h3>神经计算群组正在渲染分镜...</h3>
          <p class="estimate-text">
            <strong>预计用时：{{ estimatedStoryboardTime }}</strong> (系统已开启多线程防堵塞保护)
          </p>
          <p class="cyber-text">{{ progressMsg }}</p>
          <el-progress :percentage="progressVal" :stroke-width="12" striped striped-flow color="#E3700D" />
          <el-button type="danger" plain style="margin-top: 24px" @click="stopTask">物理阻断任务</el-button>
        </div>

        <div v-if="Object.keys(finalResults).length > 0" class="results-showcase fade-in">
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

          <div class="showcase-body">
            <div class="episode-sidebar">
              <div class="sidebar-header">
                <h4>剧集导航</h4>
                <el-input v-model="episodeSearch" placeholder="搜索剧集..." clearable prefix-icon="Search" size="small" class="episode-search" />
              </div>
              <ul class="ep-list">
                <li v-for="(content, ep) in filteredEpisodes" :key="ep" class="ep-item" :class="{ active: currentEpisodeTab === ep }" @click="currentEpisodeTab = ep">
                  <el-icon style="margin-right: 8px"><Film /></el-icon> {{ ep }}
                  <span class="scene-count">({{ getSceneCount(ep) }} 镜)</span>
                </li>
              </ul>
            </div>

            <div class="episode-content">
              
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
    </transition>

    <el-dialog v-model="dialogVisible" title="📄 章节完整内容" width="60%" center>
      <div class="full-text-reader">{{ currentFullText }}</div>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ============================================================
   保留所有您原有的 CSS (步骤1、步骤2、侧边栏等) 完全不变 
   ============================================================ */
.workflow-engine { margin-top: 24px; }
.premium-steps { display: flex; align-items: center; background: white; padding: 16px 24px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); margin-bottom: 32px; border: 1px solid var(--border-color); }
.step-item { display: flex; flex-direction: column; align-items: center; z-index: 2; }
.step-icon { width: 36px; height: 36px; border-radius: 50%; background: #e9ecef; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #6c757d; margin-bottom: 8px; transition: all 0.3s ease; }
.step-item.is-active .step-icon { background: var(--hermes-primary); color: white; box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3); transform: scale(1.1); }
.step-item.is-done .step-icon { background: #28a745; color: white; }
.step-text { font-size: 14px; font-weight: 500; color: #6c757d; transition: all 0.3s ease; }
.step-item.is-active .step-text { color: var(--hermes-primary); font-weight: 600; }
.step-line { flex: 1; height: 2px; background: #e9ecef; margin: 0 16px; position: relative; }
.step-item.is-done ~ .step-line { background: #28a745; }

.glass-card { background: var(--panel-bg); border-radius: 16px; padding: 32px; box-shadow: 0 12px 40px rgba(0, 0, 0, 0.05); border: 1px solid var(--border-color); transition: all 0.3s ease; }
.upload-area { border: none; padding: 0; }
.premium-upload-container { border: 2px dashed var(--border-color); border-radius: 20px; padding: 60px; text-align: center; transition: all 0.3s ease; background: var(--input-bg); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }
.premium-upload-container:hover { border-color: var(--hermes-primary); background: rgba(227, 112, 13, 0.03); box-shadow: 0 6px 20px rgba(227, 112, 13, 0.1); transform: translateY(-2px); }
.premium-upload-container.is-success-bg { border-color: #28a745; background: rgba(40, 167, 69, 0.08); box-shadow: 0 6px 20px rgba(40, 167, 69, 0.1); }
.upload-icon-wrapper { width: 100px; height: 100px; border-radius: 50%; background: linear-gradient(135deg, var(--input-bg), #f8f9fa); display: flex; align-items: center; justify-content: center; margin: 0 auto 32px; font-size: 40px; color: var(--hermes-primary); transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); }
.upload-icon-wrapper:hover { transform: scale(1.05); box-shadow: 0 6px 20px rgba(227, 112, 13, 0.2); }
.upload-icon-wrapper.success-icon { background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(40, 167, 69, 0.2)); color: #28a745; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.2); }
.upload-title { font-size: 20px; font-weight: 700; color: var(--text-main); margin-bottom: 8px; }
.upload-desc { color: var(--text-sub); margin-bottom: 24px; font-size: 14px; }

.btn-hermes { background: var(--hermes-primary); color: white; border: none; border-radius: 8px; font-weight: 600; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(227, 112, 13, 0.3); }
.btn-hermes:hover { background: var(--hermes-hover); box-shadow: 0 6px 20px rgba(227, 112, 13, 0.4); transform: translateY(-2px); }
.btn-hermes.round-btn { border-radius: 24px; padding: 10px 24px; }
.file-name-badge { background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 16px; display: inline-flex; align-items: center; margin: 16px 0; font-size: 14px; color: var(--text-main); font-weight: 500; }
.preview-box { margin-top: 24px; background: var(--input-bg); border-radius: 12px; padding: 24px; border: 1px solid var(--border-color); }
.box-header { display: flex; align-items: center; margin-bottom: 16px; font-weight: 600; color: var(--text-main); font-size: 14px; }
.box-header .dot { width: 8px; height: 8px; background: var(--hermes-primary); border-radius: 50%; margin-right: 8px; }
.box-header .dot.g { background: #28a745; }
.box-header.error { color: #f56c6c; }
.box-header .dot.r { background: #f56c6c; }
.error-textarea .el-textarea__inner { border-color: #f56c6c; color: #f56c6c; }
.premium-table { border-radius: 8px; overflow: hidden; border: 1px solid var(--border-color); }
.cell-content { padding: 8px 0; }
.text-clamp { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis; line-height: 1.4; font-size: 14px; color: var(--text-main); }
.action-bar { margin-top: 24px; display: flex; justify-content: flex-end; }
.action-bar.split { justify-content: space-between; align-items: center; }

.config-toolbar { display: flex; justify-content: space-between; align-items: center; background: var(--input-bg); border: 1px solid var(--border-color); padding: 20px 30px; border-radius: 16px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.02); }
.setting-item { display: flex; align-items: center; gap: 12px; }
.premium-num-input .el-input-number__decrease, .premium-num-input .el-input-number__increase { background: var(--input-bg); border: 1px solid var(--border-color); color: var(--text-main); }
.premium-num-input .el-input__wrapper { background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: none; }
.estimate-box { background: rgba(227, 112, 13, 0.05); border: 1px solid rgba(227, 112, 13, 0.2); border-radius: 8px; padding: 16px 20px; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; font-size: 14px; color: var(--text-main); }
.spinner-small { width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid var(--hermes-primary); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.ai-terminal { background: #111827; border-radius: 12px; overflow: hidden; margin-top: 15px; border: 1px solid #374151; box-shadow: 0 16px 32px rgba(0, 0, 0, 0.2); }
.terminal-header { background: #1f2937; padding: 12px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid #374151; }
.mac-btns { display: flex; gap: 8px; }
.mac-btns span { width: 12px; height: 12px; border-radius: 50%; }
.mac-btns .r { background: #ef4444; } .mac-btns .y { background: #f59e0b; } .mac-btns .g { background: #10b981; }
.terminal-header .title { flex: 1; font-size: 13px; color: #9ca3af; font-family: 'Courier New', monospace; }
.terminal-header .status { font-size: 12px; color: #10b981; font-family: 'Courier New', monospace; }
.terminal-body { padding: 24px; height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.6; }
.sys-msg { color: #10b981; margin-bottom: 12px; font-weight: bold; }
.typewriter-text { color: #d1d5db; margin: 0; white-space: pre-wrap; word-wrap: break-word; }
.blink { animation: blink 1s step-end infinite; }
@keyframes blink { from, to { opacity: 1; } 50% { opacity: 0; } }

.premium-textarea .el-textarea__wrapper { background: var(--input-bg); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: none; transition: all 0.3s ease; }
.premium-textarea .el-textarea__wrapper:hover, .premium-textarea .el-textarea__wrapper.is-focus { border-color: var(--hermes-primary); box-shadow: 0 0 0 2px rgba(227, 112, 13, 0.1); }
.btn-pulse { animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

/* 第三步整体布局 */
.results-showcase { padding: 24px; background: var(--panel-bg); border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid var(--border-color); transition: all 0.3s ease; }
.showcase-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border-color); }
.showcase-header .title { font-size: 18px; font-weight: 700; color: var(--text-main); display: flex; align-items: center; gap: 10px; }
.showcase-header .title .dot { width: 10px; height: 10px; background: linear-gradient(135deg, #28a745, #20c997); border-radius: 50%; }
.showcase-header .actions { display: flex; gap: 12px; align-items: center; }
.showcase-body { display: flex; min-height: 650px; border: 1px solid var(--border-color); border-radius: 10px; overflow: hidden; background: var(--input-bg); }

/* 左侧栏 */
.episode-sidebar { width: 240px; flex-shrink: 0; background: linear-gradient(180deg, var(--panel-bg), rgba(227, 112, 13, 0.03)); border-right: 1px solid var(--border-color); overflow-y: auto; padding: 0; }
.ep-list { list-style: none; padding: 0; margin: 0; }
.ep-item { padding: 16px 20px; cursor: pointer; transition: all 0.3s ease; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; font-size: 14px; font-weight: 500; color: var(--text-main); position: relative; }
.ep-item::before { content: ''; position: absolute; left: 0; top: 0; width: 4px; height: 100%; background: transparent; transition: all 0.3s ease; }
.ep-item:hover { background: rgba(227, 112, 13, 0.05); padding-left: 24px; }
.ep-item.active { background: linear-gradient(90deg, var(--hermes-primary), rgba(227, 112, 13, 0.9)); color: white; padding-left: 24px; }
.ep-item.active::before { background: white; }
.scene-count { font-size: 12px; color: var(--text-sub); margin-left: auto; background: rgba(0, 0, 0, 0.08); padding: 4px 10px; border-radius: 12px; }
.ep-item.active .scene-count { color: white; background: rgba(255,255,255,0.2); }

/* 搜索过滤控制条 */
.search-filter-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 16px; background: var(--input-bg); border-radius: 8px; border: 1px solid var(--border-color); }
.search-section { flex: 1; margin-right: 16px; }
.search-input { width: 100%; max-width: 400px; }
.filter-section { display: flex; align-items: center; gap: 12px; }
.view-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 12px 16px; background: rgba(227, 112, 13, 0.05); border-radius: 8px; border: 1px solid rgba(227, 112, 13, 0.2); }
.layout-toggle { display: flex; align-items: center; gap: 12px; }
.toggle-label { font-weight: bold; color: var(--text-main); font-size: 14px; }

/* 内容区通用 */
.episode-content { flex: 1; padding: 24px; background: var(--panel-bg); overflow: auto; }
.table-view { height: 100%; display: flex; flex-direction: column; }
.table-view .el-table { flex: 1; margin-bottom: 20px; }
.pagination-container { display: flex; justify-content: center; padding: 20px 0; margin-top: auto; }

/* ============================================================
   ✨✨✨ 全新高定视听剧本视图 (A/V Script Flow) CSS ✨✨✨
   ============================================================ */
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
}
</style>

<script setup>
import { ref, computed, nextTick, watch, inject } from 'vue';
import { v4 as uuidv4 } from 'uuid';
import { engine } from '../api/engine';
import { ElMessage, ElMessageBox } from 'element-plus';

// 获取全局配置
const config = inject('config');

// 监听provider变化，从Mock模式切换到非Mock模式时清空生成结果
watch(() => config?.provider, (newProvider, oldProvider) => {
  if (oldProvider === 'Mock (演示)' && newProvider !== 'Mock (演示)') {
    isGenerating.value = false;
    isGeneratingStoryboard.value = false;
    outlineText.value = '';
    progressMsg.value = '';
    progressVal.value = 0;
    finalResults.value = {};
    previewData.value = [];
    tableCols.value = [];
    fullDataJson.value = '';
    isTaskStopped.value = false;
  }
});
import {
  ArrowRight, Document, FolderOpened, ZoomIn, Select, DocumentChecked, 
  Download, Files, Film, Search, Refresh, Location, VideoCamera, Microphone, Grid, Reading
} from '@element-plus/icons-vue';

// 引入三大导出神器
import * as XLSX from 'xlsx';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

const activeStep = ref(0);
const totalEpisodes = ref(30);
const previewData = ref([]);
const tableCols = ref([]);
const fullDataJson = ref('');
const uploadedFileName = ref('');
const currentTaskId = ref('');
const totalRows = ref(0); 

const isGenerating = ref(false);
const isGeneratingStoryboard = ref(false);
const outlineText = ref('');
const progressMsg = ref('');
const progressVal = ref(0);
const finalResults = ref({});

let globalTimer = null;
const isTaskStopped = ref(false);
const outlineError = ref(false); 

const estimatedTime = ref('约 40 秒 ~ 1 分钟');
const estimatedStoryboardTime = ref('约 2 ~ 3 分钟');

const terminalBody = ref(null);
const dialogVisible = ref(false);
const currentFullText = ref('');

const currentEpisodeTab = ref('');
const searchQuery = ref('');
const sceneFilter = ref('');
const episodeSearch = ref('');

// 🚀 核心修改点：默认视图改为 'av' (视听剧本)
const layoutMode = ref('av');

const currentPage = ref(1);
const pageSize = ref(50); 
const showPagination = ref(false); 

const getColumnLabel = (col) => {
  const strCol = String(col).trim();
  if (strCol === '0') return '📖 章节 / 标题';
  if (strCol === '1') return '📝 剧情 / 正文内容';
  return strCol;
};

const openFullText = (text) => {
  currentFullText.value = text;
  dialogVisible.value = true;
};

watch(outlineText, async () => {
  if (isGenerating.value) {
    await nextTick();
    if (terminalBody.value) {
      terminalBody.value.scrollTop = terminalBody.value.scrollHeight;
    }
  }
});

// CSV 解析
const parseCSV = (csvText) => {
  if (!csvText) return { headers: [], data: [] };
  const lines = csvText.trim().split(/\r?\n/);
  if (lines.length === 0) return { headers: [], data: [] };

  const parseLine = (line) => {
    let result = [];
    let cur = '';
    let inQuote = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') inQuote = !inQuote;
      else if (line[i] === ',' && !inQuote) {
        result.push(cur);
        cur = '';
      } else cur += line[i];
    }
    result.push(cur);
    return result.map((s) => s.replace(/^"|"$/g, '').replace(/""/g, '"'));
  };

  const headers = parseLine(lines[0]);
  const data = lines.slice(1).map((line) => {
    const values = parseLine(line);
    let obj = {};
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
  if (!currentEpisodeTab.value || !finalResults.value[currentEpisodeTab.value]) {
    return { headers: [], data: [] };
  }
  return parseCSV(finalResults.value[currentEpisodeTab.value]);
});

const filteredEpisodes = computed(() => {
  let episodes = finalResults.value;
  
  // 如果有搜索关键词，先过滤
  if (episodeSearch.value) {
    const searchLower = episodeSearch.value.toLowerCase();
    const filtered = {};
    for (const [ep, content] of Object.entries(finalResults.value)) {
      if (ep.toLowerCase().includes(searchLower)) filtered[ep] = content;
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

const uniqueScenes = computed(() => {
  if (!currentEpisodeTab.value || !finalResults.value[currentEpisodeTab.value]) return [];
  const data = parseCSV(finalResults.value[currentEpisodeTab.value]).data;
  const scenes = new Set();
  data.forEach(item => { if (item['场景']) scenes.add(item['场景']); });
  return Array.from(scenes).sort();
});

const filteredScenes = computed(() => {
  if (!sceneFilter.value) return uniqueScenes.value;
  return uniqueScenes.value.filter(scene => scene.includes(sceneFilter.value));
});

const filteredData = computed(() => {
  const data = parsedCurrentEpisode.value.data;
  let filtered = data;
  
  if (searchQuery.value || sceneFilter.value) {
    filtered = data.filter(item => {
      const matchesSearch = !searchQuery.value || 
        (item['画面内容 (Visual)'] && item['画面内容 (Visual)'].toLowerCase().includes(searchQuery.value.toLowerCase())) ||
        (item['台词 (Dialogue) & 音效 (SFX)'] && item['台词 (Dialogue) & 音效 (SFX)'].toLowerCase().includes(searchQuery.value.toLowerCase()));
      const matchesScene = !sceneFilter.value || (item['场景'] && item['场景'] === sceneFilter.value);
      return matchesSearch && matchesScene;
    });
  }
  
  return filtered.sort((a, b) => {
    const numA = parseInt(a['镜号']) || 0;
    const numB = parseInt(b['镜号']) || 0;
    return numA - numB;
  });
});

const pagedData = computed(() => {
  if (!showPagination.value) return filteredData.value;
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return filteredData.value.slice(start, end);
});

const handleSearch = () => { currentPage.value = 1; };
const handleFilter = () => { currentPage.value = 1; };
const resetFilters = () => { searchQuery.value = ''; sceneFilter.value = ''; currentPage.value = 1; };
const switchLayout = () => { currentPage.value = 1; };
const handleSizeChange = (size) => { pageSize.value = size; currentPage.value = 1; };
const handleCurrentChange = (page) => { currentPage.value = page; };
const getSceneCount = (ep) => {
  if (!finalResults.value[ep]) return 0;
  return parseCSV(finalResults.value[ep]).data.length;
};

// ================= API 和 流程控制保持不变 =================
const handleUploadSuccess = (res) => {
  previewData.value = res.preview; tableCols.value = res.columns; fullDataJson.value = res.full_data_json;
  uploadedFileName.value = res.filename; totalRows.value = res.total_rows || 0;
  ElMessage.success('剧本源文件解析成功！');
};
const handleUploadError = () => ElMessage.error('上传失败，请检查网络连接');
const handleUploadChange = (file, fileList) => {};
const handleUploadExceed = (files, fileList) => { ElMessage.warning(`只能上传一个文件，已选择 ${fileList.length} 个文件`); };

const validateApiKey = () => {
  if (!config) return true;
  if (config.provider === 'Mock (演示)') return true;
  if (!config.apiKey || config.apiKey.trim() === '') {
    ElMessage.warning('请先在左侧配置并连接API Key！'); return false;
  }
  return true;
};

const beforeUpload = (file) => {
  const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.csv');
  const isLt2M = file.size / 1024 / 1024 < 20;
  if (!isExcel) { ElMessage.error('只能上传 Excel 或 CSV 文件！'); return false; }
  if (!isLt2M) { ElMessage.error('文件大小不能超过 20MB！'); return false; }
  return true;
};

const generateOutline = () => {
  if (!validateApiKey()) return;
  if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
  isTaskStopped.value = false; isGenerating.value = true; outlineError.value = false;
  outlineText.value = ''; progressMsg.value = ''; progressVal.value = 0;
  currentTaskId.value = `task_${uuidv4().slice(0, 8)}`;
  const startTime = Date.now();

  globalTimer = setInterval(() => {
    const elapsedTime = (Date.now() - startTime) / 1000;
    const progress = progressVal.value / 100;
    if (progress > 0.01) {
      const totalEstimatedTime = elapsedTime / progress;
      const remainingTime = totalEstimatedTime - elapsedTime;
      if (remainingTime > 0 && remainingTime < 3600) {
        if (remainingTime > 60) estimatedTime.value = `约 ${Math.round(remainingTime / 60)} 分钟 ${Math.round(remainingTime % 60)} 秒`;
        else estimatedTime.value = `约 ${Math.round(remainingTime)} 秒`;
      }
    }
  }, 2000);

  engine.fetchStream('generate_outline', { task_id: currentTaskId.value, novel_data_json: fullDataJson.value, total_episodes: totalEpisodes.value },
    (chunk) => { outlineText.value += chunk; },
    (msg, val) => {
      progressMsg.value = msg; progressVal.value = val;
      const elapsedTime = (Date.now() - startTime) / 1000;
      const progress = val / 100;
      if (progress > 0.01) {
        const totalEstimatedTime = elapsedTime / progress;
        const remainingTime = totalEstimatedTime - elapsedTime;
        if (remainingTime > 0 && remainingTime < 3600) {
          if (remainingTime > 60) estimatedTime.value = `约 ${Math.round(remainingTime / 60)} 分钟 ${Math.round(remainingTime % 60)} 秒`;
          else estimatedTime.value = `约 ${Math.round(remainingTime)} 秒`;
        }
      }
    },
    () => {
      isGenerating.value = false;
      if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
      ElMessage.success('分集大纲构建完成，您可自由编辑！');
    },
    (err) => {
      ElMessage.error(err); isGenerating.value = false; outlineError.value = true; outlineText.value = err;
      if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
    }
  );
};

const generateStoryboard = () => {
  if (!validateApiKey()) return;
  if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
  isTaskStopped.value = false; isGeneratingStoryboard.value = true;
  progressMsg.value = ''; progressVal.value = 0; estimatedStoryboardTime.value = '计算中...';
  currentTaskId.value = `task_${uuidv4().slice(0, 8)}`;
  const startTime = Date.now();

  globalTimer = setInterval(() => {
    const elapsedTime = (Date.now() - startTime) / 1000;
    const progress = progressVal.value / 100;
    if (progress > 0.01) {
      const totalEstimatedTime = elapsedTime / progress;
      const remainingTime = totalEstimatedTime - elapsedTime;
      if (remainingTime > 0 && remainingTime < 3600) {
        if (remainingTime > 60) estimatedStoryboardTime.value = `约 ${Math.round(remainingTime / 60)} 分钟 ${Math.round(remainingTime % 60)} 秒`;
        else estimatedStoryboardTime.value = `约 ${Math.round(remainingTime)} 秒`;
      }
    }
  }, 2000);

  engine.fetchStream('generate_storyboard', { task_id: currentTaskId.value, outline_text: outlineText.value, total_episodes: totalEpisodes.value },
    (chunk) => {},
    (msg, val) => {
      progressMsg.value = msg; progressVal.value = val;
      const elapsedTime = (Date.now() - startTime) / 1000;
      const progress = val / 100;
      if (progress > 0.01) {
        const totalEstimatedTime = elapsedTime / progress;
        const remainingTime = totalEstimatedTime - elapsedTime;
        if (remainingTime > 0 && remainingTime < 3600) {
          if (remainingTime > 60) estimatedStoryboardTime.value = `约 ${Math.round(remainingTime / 60)} 分钟 ${Math.round(remainingTime % 60)} 秒`;
          else estimatedStoryboardTime.value = `约 ${Math.round(remainingTime)} 秒`;
        }
      }
    },
    (results) => {
      finalResults.value = results;
      const eps = Object.keys(results);
      if (eps.length > 0) currentEpisodeTab.value = eps[0];
      isGeneratingStoryboard.value = false;
      if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
      ElMessage.success('工业级分镜全部渲染完毕！');
    },
    (err) => {
      ElMessage.error(err); isGeneratingStoryboard.value = false;
      if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
    }
  );
};

const stopTask = () => {
  engine.stopTask(currentTaskId.value);
  isTaskStopped.value = true; isGenerating.value = false; isGeneratingStoryboard.value = false;
  if (globalTimer) { clearInterval(globalTimer); globalTimer = null; }
  progressMsg.value = ''; progressVal.value = 0;
  estimatedTime.value = '约 40 秒 ~ 1 分钟'; estimatedStoryboardTime.value = '约 2 ~ 3 分钟';
  ElMessage.warning('任务已紧急阻断');
};

const goBack = () => {
  if (isGenerating.value || isGeneratingStoryboard.value) {
    ElMessageBox.confirm('AI正在执行高强度运算，回退将立即强制中断。确定要放弃当前任务吗？', '强制阻断确认', {
      confirmButtonText: '确定中断并回退', cancelButtonText: '点错了，继续生成', type: 'warning', buttonSize: 'large',
    }).then(() => {
        stopTask(); activeStep.value--; ElMessage.success('当前AI任务已物理阻断，算力已回收');
    }).catch(() => {});
  } else { activeStep.value--; }
};

const exportWord = () => {
  if (!outlineText.value) return;
  const sourceHTML = "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'></head><body><p style='white-space: pre-wrap; font-family: Microsoft YaHei; line-height: 1.6;'>" + outlineText.value.replace(/\n/g, '<br>') + '</p></body></html>';
  const source = 'data:application/vnd.ms-word;charset=utf-8,' + encodeURIComponent(sourceHTML);
  const fileDownload = document.createElement('a');
  document.body.appendChild(fileDownload); fileDownload.href = source;
  const baseName = uploadedFileName.value ? uploadedFileName.value.replace(/\.[^/.]+$/, '') : '小说智能分集大纲';
  fileDownload.download = `${baseName}_大纲.doc`;
  fileDownload.click(); document.body.removeChild(fileDownload);
  ElMessage.success('大纲 Word 文档已开始下载！');
};

const exportCurrentExcel = () => {
  if (!parsedCurrentEpisode.value.data.length) return;
  const ws = XLSX.utils.json_to_sheet(parsedCurrentEpisode.value.data);
  const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, currentEpisodeTab.value);
  const baseName = uploadedFileName.value ? uploadedFileName.value.replace(/\.[^/.]+$/, '') : '分镜脚本';
  XLSX.writeFile(wb, `${baseName}_${currentEpisodeTab.value}_分镜脚本.xlsx`);
  ElMessage.success(`✅ ${currentEpisodeTab.value} 导出成功！`);
};

const exportBatchZip = () => {
  if (Object.keys(finalResults.value).length === 0) return;
  ElMessage.info('📦 正在极速打包 ZIP，请稍候...');
  const zip = new JSZip();
  const baseName = uploadedFileName.value ? uploadedFileName.value.replace(/\.[^/.]+$/, '') : '分镜剧本全集';
  const folder = zip.folder(`${baseName}_分镜剧本全集`);
  for (const [ep, csvContent] of Object.entries(finalResults.value)) {
    const parsed = parseCSV(csvContent);
    const ws = XLSX.utils.json_to_sheet(parsed.data);
    const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, ep);
    const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    folder.file(`${baseName}_${ep}_分镜脚本.xlsx`, excelBuffer);
  }
  zip.generateAsync({ type: 'blob' }).then((content) => {
    saveAs(content, `${baseName}_分镜脚本全集.zip`);
    ElMessage.success('🎉 ZIP 打包下载完成！');
  });
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
  const baseName = uploadedFileName.value ? uploadedFileName.value.replace(/\.[^/.]+$/, '') : '分镜脚本全集';
  XLSX.writeFile(wb, `${baseName}_分镜脚本全集.xlsx`);
  ElMessage.success('🎉 多Sheet Excel文件导出成功！');
};
</script>