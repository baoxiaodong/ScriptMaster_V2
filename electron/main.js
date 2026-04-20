const { app, BrowserWindow, ipcMain, shell } = require('electron');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const port = 8000;
const backendReadyUrl = `http://127.0.0.1:${port}/`;

let backendProcess = null;
let mainWindow = null;

function log(message) {
  try {
    const logPath = path.join(app.getPath('userData'), 'main-process.log');
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    fs.appendFileSync(logPath, `[${new Date().toISOString()}] ${message}\n`);
  } catch (_error) {
    // Ignore logging failures.
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

  backendProcess.on('exit', (code) => {
    log(`Backend exited with code ${code}`);
    backendProcess = null;
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
}

async function waitForBackend(retries = 90, delayMs = 1000) {
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

  mainWindow.loadFile(getFrontendEntry());

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  log(`App ready. isPackaged=${app.isPackaged} appPath=${app.getAppPath()} resourcesPath=${process.resourcesPath}`);
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
