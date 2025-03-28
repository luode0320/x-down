## 项目描述
一个简单、高效的 X/Twitter 视频下载工具，支持快速从 Twitter 和 X.com 下载视频。
![home.png](static%2Fhome.png)

## 安装步骤

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

请确保提取cookies的测试步骤可用跑通, 后面才进入程序

## 运行应用
```bash
python main.py
```

访问 `http://localhost:7777`

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
