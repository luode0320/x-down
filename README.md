# X/Twitter Video Downloader

## 项目描述
一个简单、高效的 X/Twitter 视频下载工具，支持快速从 Twitter 和 X.com 下载视频。

## 特性
- 支持 X/Twitter 视频下载
- 桌面直接保存
- 高性能下载
- 实时下载进度
- 简洁的 Web 界面

## 技术栈
- Python 3.10+
- Flask
- yt-dlp
- HTML5
- JavaScript

## 安装步骤

### 前提条件
- Python 3.10 或更高版本
- pip
- FFmpeg

### 克隆仓库
```bash
git clone https://github.com/yourusername/x-video-downloader.git
cd x-video-downloader
```

### 创建虚拟环境
```bash
python3 -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## 提取cookies
### 选择一个浏览器登录你的X账号
```shell
# edge浏览器提取cookies
yt-dlp --cookies-from-browser edge --cookies cookies.txt
# chrome浏览器提取cookies
yt-dlp --cookies-from-browser chrome --cookies cookies.txt
# 测试你生成的cookies
yt-dlp --cookies cookies.txt "https://x.com/kedaibiaozzz_/status/1904109099547349245?s=46"
```

### 这是不用保存 cookies 文件直接命令下载
```shell
# chrome浏览器
yt-dlp --cookies-from-browser chrome "https://x.com/kedaibiaozzz_/status/1904109099547349245?s=46"
# edge浏览器
yt-dlp --cookies-from-browser edge "https://x.com/kedaibiaozzz_/status/1904109099547349245?s=46"
```

请确保提取cookies的测试步骤可用跑通, 后面才进入程序

## 运行应用
```bash
python app.py
```

访问 `http://localhost:5000`

## 使用方法
1. 打开网页
2. 粘贴 X/Twitter 视频链接
3. 点击下载
4. 视频将保存到桌面

## 版本
- v1.0.0 - 初始发布

## 许可证
MIT License

## 免责声明
仅供学习和个人使用，请尊重版权
