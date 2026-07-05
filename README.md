# 一坨屎都能包装成金子的找工作包装网站

一个用于“把大白话翻译成职场高阶表达”的简历与面试话术包装网站骨架。

## 技术栈

- 前端：Vue 3 + Vite
- 后端：Python + Django
- 数据库：暂不接入数据库

## 目录结构

```text
backend/
  apps/copywriter/       # 话术包装 API
  config/                # Django 配置
  manage.py
frontend/
  src/                   # Vue 页面
requirements.txt
start-backend.bat
start-frontend.bat
```

## 启动

先安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd install
```

推荐一键启动：

```powershell
.\start-dev.bat
```

它会打开两个窗口，分别运行后端和前端。关闭对应窗口即可停止服务。

单独启动后端：

```powershell
.\start-backend.bat
```

单独启动前端：

```powershell
.\start-frontend.bat
```

查看或停止服务：

```powershell
.\check-env.bat
.\status-dev.bat
.\stop-dev.bat
```

默认地址：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/api/health/

## 第三方大模型

面试话术模块优先调用 OpenAI-compatible 的第三方大模型接口。复制 `.env.example` 为 `.env`，填入自己的 API Key 后重启后端即可。

默认配置示例为 DeepSeek：

```text
AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
AI_API_KEY=你的 API Key
```

如果没有配置 API Key，系统会自动退回本地兜底引擎。
