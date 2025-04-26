## 项目描述
一个简单、高效的 X/Twitter 视频下载工具，支持快速从 Twitter 和 X.com 下载视频。

测试地址: https://x.luode.vip/#/

![home.png](static%2Fhome.png)

## 安装步骤

### 安装依赖
```bash
pip install -r requirements.txt
pip install --upgrade yt-dlp
```

## 提取cookies
### 选择一个浏览器登录你的X账号
```shell
# edge浏览器提取cookies
yt-dlp --cookies-from-browser edge --cookies cookies.txt
# chrome浏览器提取cookies
yt-dlp --cookies-from-browser chrome --cookies cookies.txt

```

测试确保提取cookies的步骤可用, 后面才进入程序
```shell
yt-dlp --cookies cookies.txt "https://x.com/kedaibiaozzz_/status/1904109099547349245?s=46"
```

## 运行应用
```bash
python main.py
```

访问 `http://127.0.0.1:7777`

## docker安装
请把提取cookies.txt放置在 /usr/local/src/x-down 目录下面

```shell
docker run -d \
--network host \
--restart=always \
-v /usr/local/src/x-down:/app/config \
-v /usr/local/src/x-down/data:/app/data \
--name x-down  \
luode0320/x-down:latest
```

## 使用方法
1. 打开网页
2. 粘贴 X/Twitter 视频链接
3. 点击下载

## 许可证
MIT License

## 免责声明
仅供学习和个人使用，请尊重版权
