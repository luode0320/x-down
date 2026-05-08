# x-down 运维手册（1分钟版）

## 1. 刷新 Cookies

优先命令方式：

```powershell
yt-dlp --cookies-from-browser edge --cookies config/cookies.txt
```

若报 `Could not copy Chrome cookie database`：

```powershell
Get-Process chrome,msedge,msedgewebview2 -ErrorAction SilentlyContinue | Stop-Process -Force
yt-dlp --cookies-from-browser "edge:Default" --cookies config/cookies.txt
```

若仍失败，使用离线扩展：

- 扩展目录：`tools/get-cookies-txt-locally/chrome-extension`
- 在 `edge://extensions` 或 `chrome://extensions` 开启开发者模式并加载该目录
- 在已登录 X 的页面导出 `Netscape` 格式 `cookies.txt`
- 覆盖 `config/cookies.txt`

## 2. 立刻验证 Cookies

```powershell
yt-dlp --cookies config/cookies.txt --skip-download "https://x.com/<user>/status/<id>"
```

判定标准：

- 成功：能解析到推文媒体信息（无认证错误）
- 失败：出现 `Could not authenticate you`，返回步骤 1 重新导出

## 3. 启动/重启服务

```powershell
python main.py
```

健康检查：

```powershell
curl http://127.0.0.1:7777/healthz
```

预期返回：

```json
{"status":"ok"}
```

## 4. API 快速自检

```powershell
curl -X POST http://127.0.0.1:7777/api/v1/resolve ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://x.com/<user>/status/<id>\",\"prefer\":\"mp4\"}"
```

## 5. 故障速查

- `Cookies file not found`：确认 `config/cookies.txt` 存在
- `Could not authenticate you`：cookies 失效，重新登录导出
- `No video could be found in this tweet`：可能不是视频推文，或该推文对当前登录态不可见
- `This tweet is not publicly accessible`：推文受限/删除/不可访问
