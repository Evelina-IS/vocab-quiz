# 📝 大英四单词默写

> 纯前端单词默写工具 · 720个大英四核心词汇 · 支持 GitHub 云端同步

## 功能

- **默写模式** — 看中文写英文 / 看英文写中文，输入框拼写自动判对错
- **单元筛选** — 按第 1~8 单元筛选练习范围
- **错题复习** — 自动记录错题，一键进入错题专练
- **导出错题** — 一键导出错题列表为 `.txt` 文件
- **单词表** — 查看所有单词及对应的默写状态（正确/错误/待默写）
- **进度统计** — 总词数、已默写、正确数、错误数一目了然
- **云端同步** — 用 GitHub 登录，数据保存在服务器，换设备也不丢失

## 使用方式

### 在线使用

访问部署地址（见下方部署指南）

### 本地开发

```bash
# 纯前端版（无后端，数据存浏览器）
open index.html

# 完整版（有后端 + 云端同步）
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 GitHub OAuth 信息
python app.py
```

## 部署

详见 [SETUP.md](SETUP.md)

## 数据来源

单词表基于大英四考试大纲核心词汇，共 720 个单词，分为 8 个单元。

## 技术栈

- **前端**: 纯 HTML + CSS + JavaScript
- **后端**: Flask + SQLAlchemy + SQLite
- **认证**: GitHub OAuth
- **部署**: Docker / Railway / Render

## License

MIT
