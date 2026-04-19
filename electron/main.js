const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const express = require('express');
const fs = require('fs');

// 创建Express应用
const expressApp = express();
const port = 8000;

// 加载Python后端
const { PythonShell } = require('python-shell');

// 配置Express中间件
expressApp.use(express.json());
expressApp.use(express.urlencoded({ extended: true }));

// 静态文件服务
expressApp.use(express.static(path.join(__dirname, '../frontend/dist')));

// 启动Python后端
let pythonProcess;

function startPythonBackend() {
  pythonProcess = PythonShell.run('main.py', {
    scriptPath: path.join(__dirname, '..'),
    args: ['--host', '0.0.0.0', '--port', port.toString()]
  }, (err) => {
    if (err) {
      console.error('Python backend error:', err);
    }
  });

  pythonProcess.on('message', (message) => {
    console.log('Python backend message:', message);
  });
}

// 停止Python后端
function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill();
  }
}

// 创建主窗口
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  // 加载前端应用
  mainWindow.loadURL(`http://localhost:${port}`);

  // 打开开发者工具
  // mainWindow.webContents.openDevTools();

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

// 应用启动时
app.on('ready', () => {
  // 启动Python后端
  startPythonBackend();
  
  // 延迟创建窗口，确保后端已启动
  setTimeout(createWindow, 2000);
});

// 应用关闭时
app.on('quit', () => {
  stopPythonBackend();
});

// 所有窗口关闭时
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 激活应用时
app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});