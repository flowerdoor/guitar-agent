# 弦上教练

一个面向完全零基础用户的本地吉他教学桌面应用。应用使用 PySide6 构建界面、SQLite 保存进度，并通过 DeepSeek API 流式提供连续中文教学对话。

## 1. 准备环境

项目需要 Python 3.11 或更高版本。建议在 PowerShell 中创建独立虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## 2. 配置 DeepSeek

打开项目根目录的 `config.local.json`，只填写 `api_key`：

```json
{
  "api_key": "你的 DeepSeek API Key",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "timeout_seconds": 45
}
```

`config.local.json` 已被忽略，不应提交或分享。没有 API Key 时应用仍能打开，课程、设置和练习记录可以离线使用，只有智能对话不可用。

## 3. 启动应用

```powershell
python -m app
```

首次启动会在 `data/guitar_agent.db` 创建本地数据库。右侧显示当前课程；完成练习后，进度、时长和备注会立即保存。“切换”按钮可以前跳或回退课程进度，已有练习历史不会被删除。聊天框支持 `Ctrl+Enter` 发送。

## 4. 运行测试

```powershell
python -m pytest
```

测试使用临时数据库和模拟网络，不会调用真实 DeepSeek API，也不会读取你的 API Key。

## 5. 本地知识库（RAG）

`data/knowledge` 中的 Markdown 文件会在应用启动时自动加载。每次提问前，应用会按标题切分文档、从中检索最相关的几段，并只将这些段落作为参考资料发送给模型。

当前已包含 `guitar_music_theory.md`，覆盖吉他基础乐理、指板、节奏、和弦与常见演奏知识。添加新的 `.md` 文件后，重启应用即可纳入检索。知识库内容不会写入本地对话数据库。

## 6. 构建 Windows 应用

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

构建产物位于 `dist\GuitarCoach`。打开同目录下自动生成的 `config.local.json` 并填写 API Key。打包版数据库保存在 `%LOCALAPPDATA%\GuitarCoach\guitar_agent.db`。

## 架构边界

- `app/core`：课程、提示词和智能体流程，不依赖 Qt。
- `app/data`：SQLite 数据访问，每次操作使用独立连接，可由后台线程调用。
- `app/services`：DeepSeek HTTP 适配器。
- `app/ui`：桌面界面和后台请求线程。

未来接入 ESP32 时，让板端通过串口、蓝牙或 Wi-Fi 发送练习事件；教学逻辑和 DeepSeek 调用继续运行在电脑或其他联网主机上。
