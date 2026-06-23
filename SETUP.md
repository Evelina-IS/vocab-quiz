# 部署指南

## 1. 创建 GitHub OAuth App

1. 访问 https://github.com/settings/developers
2. 点击 **New OAuth App**
3. 填写：
   - **Application name**: `大英四单词默写`
   - **Homepage URL**: 你的部署地址（本地测试用 `http://localhost:5000`）
   - **Authorization callback URL**: `你的部署地址/api/auth/github/callback`
4. 创建后，复制 **Client ID** 和生成 **Client Secret**

## 2. 本地运行

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 GITHUB_CLIENT_ID 和 GITHUB_CLIENT_SECRET

# 运行
python app.py
```

访问 http://localhost:5000

## 3. 部署到 Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/xxx)

或手动：

```bash
# 安装 Railway CLI
brew install railway

# 登录
railway login

# 部署
cd backend
railway init
railway up

# 设置环境变量
railway variables set SECRET_KEY=xxx
railway variables set GITHUB_CLIENT_ID=xxx
railway variables set GITHUB_CLIENT_SECRET=xxx
```

## 4. 部署到 Render

1. 在 https://render.com 创建 New Web Service
2. 连接你的 GitHub 仓库
3. 配置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 app:create_app()`
   - 添加环境变量 `SECRET_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`

## 5. 部署后

部署成功后，回到 GitHub OAuth App 设置，将 **Homepage URL** 和 **Callback URL** 更新为实际的部署地址。
