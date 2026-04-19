# ScriptMaster 封装指南

本指南将帮助您将 ScriptMaster 项目封装成 Windows 可执行安装包（.exe）。

## 目录结构

```
electron/
├── main.js          # Electron 主进程
├── preload.js       # 预加载脚本
├── icon.ico         # 应用图标
└── README.md        # 封装指南
```

## 准备工作

1. **安装 Node.js**
   - 下载并安装 Node.js 18.x 或更高版本
   - 验证安装：`node -v` 和 `npm -v`

2. **安装依赖**
   - 在项目根目录执行：
     ```bash
     npm install electron electron-builder express python-shell
     ```

3. **构建前端项目**
   - 在 `frontend` 目录执行：
     ```bash
     npm install
     npm run build
     ```

## 配置文件

### 1. electron-package.json

已创建 `electron-package.json` 文件，包含以下配置：
- 应用名称：ScriptMaster
- 版本：2.0.0
- 构建目标：Windows 64位
- 安装程序类型：NSIS
- 图标：electron/icon.ico

### 2. main.js

已创建 `main.js` 文件，实现以下功能：
- 启动 Electron 应用
- 启动 Python 后端服务
- 加载前端页面
- 处理应用生命周期

### 3. preload.js

已创建 `preload.js` 文件，用于在渲染进程和主进程之间建立通信桥梁。

## 构建步骤

1. **复制配置文件**
   - 将 `electron-package.json` 复制为 `package.json`：
     ```bash
     copy electron-package.json package.json
     ```

2. **安装依赖**
   - 执行：
     ```bash
     npm install
     ```

3. **构建安装包**
   - 执行：
     ```bash
     npm run build:win
     ```

4. **查看构建结果**
   - 构建完成后，安装包将生成在 `dist-electron` 目录中

## 运行步骤

1. **安装应用**
   - 双击 `dist-electron/ScriptMaster Setup x.x.x.exe` 进行安装

2. **运行应用**
   - 安装完成后，从开始菜单或桌面快捷方式启动 ScriptMaster

3. **使用应用**
   - 应用启动后，会自动启动后端服务并加载前端页面
   - 您可以像使用普通应用一样使用 ScriptMaster

## 注意事项

1. **Python 依赖**
   - 应用会自动检测并使用系统中的 Python 环境
   - 确保系统已安装 Python 3.8 或更高版本
   - 确保已安装项目所需的 Python 依赖（可通过 `pip install -r requirements.txt` 安装）

2. **端口占用**
   - 应用默认使用 8000 端口
   - 确保该端口未被其他应用占用

3. **防火墙**
   - 首次运行时，可能会弹出防火墙提示，请允许应用访问网络

4. **卸载**
   - 可以通过控制面板的程序卸载功能卸载应用
   - 卸载时会自动清理相关文件

## 故障排除

1. **应用无法启动**
   - 检查系统是否安装了 Python
   - 检查 8000 端口是否被占用
   - 查看应用日志（位于用户目录的 `AppData/Roaming/ScriptMaster/logs`）

2. **后端服务无法启动**
   - 检查 Python 依赖是否安装
   - 检查 `main.py` 是否存在且可执行

3. **前端页面无法加载**
   - 检查 `frontend/dist` 目录是否存在
   - 检查后端服务是否正常运行
