## x-down (Direct-Only)

一个仅做 **X/Twitter 视频直连解析** 的工具：

- 后端仅解析媒体直链
- 不落盘
- 不中转视频流量

## 技术栈

- FastAPI
- yt-dlp
- pytest

## 快速开始

```bash
pip install -r requirements.txt
```

## 提取并配置 Cookies（必需）

[请参考cookies.md](cookies.md)

## 启动服务：

```bash
python main.py
```

访问：`http://127.0.0.1:7777`

## API

### 健康检查

`GET /healthz`

返回：

```json
{ "status": "ok" }
```

### 解析直链

`POST /api/v1/resolve`

请求：

```json
{
  "url": "https://x.com/<user>/status/<id>",
  "prefer": "mp4"
}
```

响应示例：

```json
{
  "id": "res_abc123",
  "tweet_url": "https://twitter.com/<user>/status/<id>",
  "title": "...",
  "duration": 25,
  "resolved_at": "2026-05-08T12:00:00+00:00",
  "expires_at": "2026-05-08T12:05:00+00:00",
  "variants": [
    {
      "quality": "720p",
      "mime": "video/mp4",
      "url": "https://video.twimg.com/...",
      "size_bytes": 12345678
    }
  ]
}
```

## 环境变量

- `RESOLVE_TTL_SECONDS`：解析结果有效期（默认 `300` 秒）
- `YTDLP_SOCKET_TIMEOUT`：yt-dlp 超时（默认 `15`）
- `YTDLP_RETRIES`：yt-dlp 重试次数（默认 `2`）
- `YTDLP_COOKIES_FILE`：cookies 文件路径（默认 `config/cookies.txt`）

## 测试

```bash
pytest -q
```

## 运维手册

- 快速值班操作请看：[OPS.md](OPS.md)

## 常见问题

### 1. `No video could be found in this tweet`

- 该推文可能不是视频推文
- 推文可能对匿名/当前登录态不可见
- 可先在浏览器登录态下手动确认该推文确实包含视频

### 2. `Could not authenticate you`

- `config/cookies.txt` 已失效或与当前账号状态不一致
- 重新登录 X 并刷新 cookies 后重试

### 3. `Could not copy Chrome cookie database`

- 关闭所有 `chrome/msedge/msedgewebview2` 进程后重试
- 或直接使用上面的离线扩展导出方式

## 免责声明

仅供学习研究。请遵守目标平台条款与所在地区法律法规，尊重版权。
