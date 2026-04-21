const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const port = 8000;
const backendReadyUrl = `http://127.0.0.1:${port}/`;
const LOG_FILE_NAME = 'main-process.log';
const LOG_MAX_SIZE = 5 * 1024 * 1024;
const LOG_MAX_FILES = 3;

let backendProcess = null;
let mainWindow = null;

function getLogPath() {
  const installDir = path.dirname(app.getPath('exe'));
  return path.join(installDir, LOG_FILE_NAME);
}

function rotateLogIfNeeded(logPath) {
  try {
    if (!fs.existsSync(logPath)) return;
    const stats = fs.statSync(logPath);
    if (stats.size < LOG_MAX_SIZE) return;

    for (let i = LOG_MAX_FILES - 1; i >= 1; i -= 1) {
      const olderPath = `${logPath}.${i}`;
      const newerPath = `${logPath}.${i + 1}`;
      if (fs.existsSync(olderPath)) {
        if (i === LOG_MAX_FILES - 1) {
          fs.rmSync(olderPath, { force: true });
        } else {
          fs.renameSync(olderPath, newerPath);
        }
      }
    }

    fs.renameSync(logPath, `${logPath}.1`);
  } catch (_error) {
    // Ignore rotation failures and continue writing.
  }
}

function log(message) {
  try {
    const logPath = getLogPath();
    rotateLogIfNeeded(logPath);
    fs.appendFileSync(logPath, `[${new Date().toISOString()}] ${message}\n`);
  } catch (_error) {
    // Ignore logging failures.
  }
}

function toHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderWindowMessage(title, detail, tone = 'loading') {
  if (!mainWindow) return Promise.resolve();

  const themes = {
    loading: {
      border: '#fde68a',
      bg: '#fffbeb',
      title: '#92400e',
      detail: '#78350f',
    },
    error: {
      border: '#fecaca',
      bg: '#fff7ed',
      title: '#b91c1c',
      detail: '#7f1d1d',
    },
  };

  const theme = themes[tone] || themes.loading;
  const html = `<!doctype html>
  <html lang="zh-CN">
    <head>
      <meta charset="UTF-8" />
      <title>${toHtml(title)}</title>
      <style>
        body {
          margin: 0;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(180deg, #fff 0%, ${theme.bg} 100%);
          font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
          color: #111827;
        }
        .panel {
          width: min(720px, calc(100vw - 48px));
          padding: 32px;
          border-radius: 24px;
          border: 1px solid ${theme.border};
          background: rgba(255,255,255,0.96);
          box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
        }
        h1 { margin: 0 0 12px; font-size: 28px; color: ${theme.title}; }
        p { margin: 0 0 16px; line-height: 1.8; color: ${theme.detail}; }
        pre {
          margin: 0;
          padding: 16px;
          border-radius: 16px;
          background: #0f172a;
          color: #e2e8f0;
          white-space: pre-wrap;
          word-break: break-word;
          font-size: 13px;
          line-height: 1.7;
        }
      </style>
    </head>
    <body>
      <div class="panel">
        <h1>${toHtml(title)}</h1>
        <p>${tone === 'error'
          ? '应用启动失败，请检查是否被杀毒软件拦截、端口 8000 被占用，或安装目录权限受限。'
          : '应用正在启动后端服务，请稍候。首次启动可能会稍慢一些。'}</p>
        <pre>${toHtml(detail)}</pre>
      </div>
    </body>
  </html>`;

  return mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
}

function showFatalError(title, detail) {
  renderWindowMessage(title, detail, 'error').catch((error) => {
    log(`Failed to render fatal error page: ${error.stack || error.message}`);
  });
}

/**
 * 🔧 修复1：启动前清理旧后端进程（防止端口冲突）
 * Windows 上查找占用指定端口的进程并杀掉整个进程树
 */
function killExistingBackend() {
  try {
    const result = execSync(
      `netstat -ano | findstr ":${port} " | findstr "LISTENING"`,
      { encoding: 'utf-8', windowsHide: true }
    ).trim();

    if (!result) {
      log(`Port ${port} is free, no cleanup needed.`);
      return;
    }

    // 提取所有占用端口的 PID
    const pids = [...new Set(
      result.split('\n')
        .map(line => {
          const parts = line.trim().split(/\s+/);
          return parseInt(parts[parts.length - 1], 10);
        })
        .filter(pid => pid && pid > 0 && pid !== process.pid)
    )];

    if (pids.length === 0) {
      log(`Port ${port} is occupied but PID is self, skipping.`);
      return;
    }

    log(`Port ${port} is occupied by PIDs: ${pids.join(', ')}. Killing...`);

    for (const pid of pids) {
      try {
        // /F 强制终止 /T 终止子进程树
        execSync(`taskkill /F /T /PID ${pid}`, { windowsHide: true });
        log(`Killed process tree for PID ${pid}.`);
      } catch (e) {
        log(`Failed to kill PID ${pid}: ${e.message}`);
      }
    }

    // 等待端口释放
    log('Waiting for port to be released...');
    let released = false;
    for (let i = 0; i < 15; i++) {
      try {
        const check = execSync(
          `netstat -ano | findstr ":${port} " | findstr "LISTENING"`,
          { encoding: 'utf-8', windowsHide: true }
        ).trim();
        if (!check) {
          released = true;
          break;
        }
      } catch {
        released = true;
        break;
      }
      execSync('timeout /t 1 /nobreak > nul', { windowsHide: true });
    }
    log(released ? 'Port released successfully.' : 'Port release timeout, proceeding anyway.');
  } catch {
    log(`Port ${port} check: netstat not available or port is free.`);
  }
}

function getFrontendEntry() {
  return path.join(app.getAppPath(), 'frontend', 'dist', 'index.html');
}

function getBackendCommand() {
  if (app.isPackaged) {
    return {
      command: path.join(process.resourcesPath, 'backend-dist', 'ScriptMasterBackend.exe'),
      args: ['--host', '127.0.0.1', '--port', String(port)],
      cwd: path.join(process.resourcesPath, 'backend-dist'),
    };
  }

  return {
    command: 'python',
    args: ['main.py', '--host', '127.0.0.1', '--port', String(port)],
    cwd: path.join(app.getAppPath(), 'backend'),
  };
}

function startBackend() {
  const backend = getBackendCommand();
  log(`Starting backend: ${backend.command} ${backend.args.join(' ')} cwd=${backend.cwd}`);
  backendProcess = spawn(backend.command, backend.args, {
    cwd: backend.cwd,
    windowsHide: true,
  });

  backendProcess.stdout?.on('data', (data) => {
    log(`[backend stdout] ${String(data).trim()}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    log(`[backend stderr] ${String(data).trim()}`);
  });

  backendProcess.on('error', (error) => {
    log(`Failed to start backend: ${error.stack || error.message}`);
  });

  backendProcess.on('exit', (code, signal) => {
    log(`Backend exited with code=${code} signal=${signal} pid=${backendProcess?.pid}`);
    backendProcess = null;
  });
}

/**
 * 🔧 修复2：Windows 上杀整个进程树，防止 PyInstaller 子进程残留
 */
function stopBackend() {
  if (backendProcess) {
    const pid = backendProcess.pid;
    log(`Stopping backend process tree (pid=${pid})...`);

    if (process.platform === 'win32') {
      try {
        execSync(`taskkill /F /T /PID ${pid}`, { windowsHide: true });
        log(`Taskkill /F /T /PID ${pid} succeeded.`);
      } catch (e) {
        log(`Taskkill failed for PID ${pid}, falling back to .kill(): ${e.message}`);
        try {
          backendProcess.kill('SIGKILL');
        } catch (_) { /* already dead */ }
      }
    } else {
      try {
        backendProcess.kill('SIGTERM');
      } catch (_) { /* already dead */ }
    }

    backendProcess = null;
  } else {
    log('No backend process to stop.');
  }
}

async function waitForBackend(retries = 90, delayMs = 1000) {
  // 🔧 修复3：先等一下让 PyInstaller onefile 解压完成
  log(`Waiting for backend to start (max ${retries * delayMs / 1000}s)...`);

  // 先额外等 2 秒让 PyInstaller 解压
  await new Promise((resolve) => setTimeout(resolve, 2000));

  for (let attempt = 0; attempt < retries; attempt += 1) {
    try {
      const response = await fetch(backendReadyUrl);
      if (response.ok) {
        log(`Backend ready after ${attempt + 1} attempts`);
        return;
      }
    } catch (_error) {
      // Backend is still starting.
    }

    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }

  throw new Error('Backend did not become ready in time.');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  renderWindowMessage('ScriptMaster 启动中', '正在检查本地后端服务...', 'loading').catch((error) => {
    log(`Loading placeholder failed: ${error.stack || error.message}`);
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    log(`Page failed to load: errorCode=${errorCode} errorDescription=${errorDescription}`);
    showFatalError('页面加载失败', `errorCode=${errorCode}\n${errorDescription}`);
  });

  mainWindow.webContents.on('render-process-gone', (event, details) => {
    log(`Renderer process crashed: reason=${details.reason} exitCode=${details.exitCode}`);
    showFatalError('渲染进程异常退出', `reason=${details.reason}\nexitCode=${details.exitCode}`);
  });

  mainWindow.webContents.on('console-message', (event, level, message) => {
    if (level <= 2) { // Only log warning and error
      log(`[renderer ${['verbose','info','warning','error'][level]}] ${message}`);
    }
  });

  mainWindow.on('closed', () => {
    log('Main window closed.');
    mainWindow = null;
  });
}

function loadFrontend() {
  const frontendPath = getFrontendEntry();
  log(`Loading frontend from: ${frontendPath}`);
  log(`Frontend file exists: ${fs.existsSync(frontendPath)}`);

  return mainWindow.loadFile(frontendPath).then(() => {
    log('Frontend loaded successfully.');
  }).catch((error) => {
    log(`Frontend load failed: ${error.stack || error.message}`);
    showFatalError('前端页面加载失败', error.stack || error.message);
  });
}

app.on('ready', async () => {
  log(`App ready. isPackaged=${app.isPackaged} appPath=${app.getAppPath()} resourcesPath=${process.resourcesPath}`);
  createWindow();

  // 🔧 修复1：先清理旧后端
  killExistingBackend();

  // 启动新后端
  startBackend();

  try {
    await waitForBackend();
    await loadFrontend();
  } catch (error) {
    log(`Startup failed: ${error.stack || error.message}`);
    showFatalError('后端启动失败', error.stack || error.message);
  }
});

app.on('quit', () => {
  log('App quitting, stopping backend...');
  stopBackend();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.handle('open-external', async (_event, url) => {
  await shell.openExternal(url);
});

ipcMain.handle('get-app-version', () => app.getVersion());

process.on('uncaughtException', (error) => {
  log(`uncaughtException: ${error.stack || error.message}`);
});

process.on('unhandledRejection', (error) => {
  log(`unhandledRejection: ${error && error.stack ? error.stack : error}`);
});
