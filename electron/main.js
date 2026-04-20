const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const port = 8000;
const backendReadyUrl = `http://127.0.0.1:${port}/`;

let backendProcess = null;
let mainWindow = null;

function log(message) {
  try {
    // 日志文件放在安装目录（EXE 所在目录）
    const installDir = path.dirname(app.getPath('exe'));
    const logPath = path.join(installDir, 'main-process.log');
    fs.appendFileSync(logPath, `[${new Date().toISOString()}] ${message}\n`);
  } catch (_error) {
    // Ignore logging failures.
  }
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

  const frontendPath = getFrontendEntry();
  log(`Loading frontend from: ${frontendPath}`);
  log(`Frontend file exists: ${fs.existsSync(frontendPath)}`);

  mainWindow.loadFile(frontendPath).then(() => {
    log('Frontend loaded successfully.');
  }).catch((error) => {
    log(`Frontend load failed: ${error.stack || error.message}`);
  });

  // 🔧 增加窗口加载失败的错误处理
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    log(`Page failed to load: errorCode=${errorCode} errorDescription=${errorDescription}`);
  });

  mainWindow.webContents.on('render-process-gone', (event, details) => {
    log(`Renderer process crashed: reason=${details.reason} exitCode=${details.exitCode}`);
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

app.on('ready', async () => {
  log(`App ready. isPackaged=${app.isPackaged} appPath=${app.getAppPath()} resourcesPath=${process.resourcesPath}`);

  // 🔧 修复1：先清理旧后端
  killExistingBackend();

  // 启动新后端
  startBackend();

  try {
    await waitForBackend();
    createWindow();
  } catch (error) {
    log(`Startup failed: ${error.stack || error.message}`);
    app.quit();
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
