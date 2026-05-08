# x-down 运维手册（1分钟版）

## 1. 刷新 Cookies

离线扩展：

- 扩展目录：`tools/get-cookies-txt-locally/chrome-extension`
- 在 `edge://extensions` 或 `chrome://extensions` 开启开发者模式并加载该目录
- 在已登录 X 的页面导出 `Netscape` 格式 `cookies.txt`
- 覆盖 `config/cookies.txt`

## 2. 立刻验证 Cookies

```powershell
yt-dlp --cookies config/cookies.txt --skip-download "https://x.com/ElamGeorgi53648/status/2051980304672309702?s=20"
```

判定标准：

```
[twitter] Extracting URL: https://x.com/ElamGeorgi53648/status/2051980304672309702?s=20
[twitter] 2051980304672309702: Downloading GraphQL JSON
[twitter] 2051980304672309702: Downloading m3u8 information
WARNING: ffmpeg not found. The downloaded format may not be the best available. Installing ffmpeg is strongly recommended: https://github.com/yt-dlp/yt-dlp#dependencies
[info] 2051655915372462080: Downloading 1 format(s): http-2176
```

- 成功：能解析到推文媒体信息（无认证错误）
- 失败：出现 `Could not authenticate you`，返回步骤 1 重新导出
