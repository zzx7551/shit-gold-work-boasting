# 一坨屎都能包装成金子的找工作包装网站

一个帮助用户把朴素表达改写成更适合简历和面试场景表达的网站。项目采用 Vue 3 + Vite 前端、Python + Django 后端，当前版本不接入数据库。

## 目录结构

```text
backend/
  apps/copywriter/       # 面试话术 API、简历 PDF 导出
  config/                # Django 配置、URL、WSGI、CORS
  manage.py
frontend/
  src/                   # Vue 页面与样式
render.yaml              # Render 后端部署配置
requirements.txt         # Python 依赖
package.json             # 前端依赖与脚本
```

## 本地启动

安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm.cmd install
```

一键启动：

```powershell
.\start-dev.bat
```

默认地址：

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/api/health/

## 环境变量

复制 `.env.example` 为 `.env`，然后填入自己的配置。本地开发至少需要：

```text
AI_PROVIDER=deepseek
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=你的模型名
AI_API_KEY=你的 API Key
```

不要把 `.env` 提交到 GitHub。项目里的 `.gitignore` 已经默认忽略 `.env`。

## Render 部署 Django 后端

1. 把项目上传到 GitHub。
2. 登录 Render，选择 `New +`，再选 `Web Service`。
3. 绑定你的 GitHub 仓库。
4. 如果 Render 识别到 `render.yaml`，可以按 Blueprint 创建；也可以手动填：
   - Runtime：`Python`
   - Build Command：`pip install -r requirements.txt`
   - Start Command：`cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
5. 在 Render 的 Environment 里配置：
   - `DJANGO_DEBUG=False`
   - `DJANGO_SECRET_KEY=一串足够长的随机字符串`
   - `DJANGO_ALLOWED_HOSTS=你的后端域名`，例如 `xxx.onrender.com`
   - `CORS_ALLOWED_ORIGINS=你的 Vercel 前端域名`，例如 `https://xxx.vercel.app`
   - `AI_PROVIDER=deepseek`
   - `AI_BASE_URL=https://api.deepseek.com`
   - `AI_MODEL=你的模型名`
   - `AI_API_KEY=你的 API Key`
6. 部署完成后，打开：

```text
https://你的后端域名/api/health/
```

看到 `status: ok` 就说明后端活了。

## Vercel 部署 Vue 前端

1. 登录 Vercel，选择 `Add New Project`。
2. 绑定同一个 GitHub 仓库。
3. Framework Preset 选择 `Vite`。
4. Build Command 使用：

```text
npm run build
```

5. Output Directory 使用：

```text
dist
```

6. 在 Vercel 的 Environment Variables 里配置：

```text
VITE_API_BASE_URL=https://你的后端域名
```

注意不要在后面加 `/`，例如：

```text
VITE_API_BASE_URL=https://xxx.onrender.com
```

7. 部署完成后，把 Vercel 给你的前端域名填回 Render 的 `CORS_ALLOWED_ORIGINS`，然后重新部署一次后端。

## 部署后的调用关系

```text
用户浏览器
  -> Vercel 前端
  -> Render Django API
  -> 第三方文字模型 API
```

只要 Render 后端配置了 `AI_API_KEY`，线上面试话术功能就会继续生效。API Key 放在 Render 环境变量里，前端用户看不到。
