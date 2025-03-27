import logging
import os
import sys
import subprocess
import json
import traceback
import re
import yt_dlp
from flask import Flask, request, jsonify, render_template
from flask import send_from_directory, Response

# 尝试导入 flask_cors，如果失败则给出友好提示
try:
    from flask_cors import CORS
except ImportError:
    print("未找到 flask_cors 模块。请运行 'pip install flask-cors' 安装。")
    CORS = None  # 提供一个备选方案

# 设置更详细的日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('app.log', encoding='utf-8')  # 同时写入日志文件
    ]
)
logger = logging.getLogger(__name__)

# 设置 aria2c 路径
ARIA2C_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aria2', 'aria2-1.36.0-win-64bit-build1', 'aria2c.exe')

# 设置代理，如果需要的话
PROXY = None

# 在函数顶部添加（或替换原有temp_dir定义）
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(data_dir, exist_ok=True)  # 确保目录存在

app = Flask(__name__, static_folder='static', static_url_path='/static')
if CORS:
    CORS(app)  # 启用 CORS

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route('/download', methods=['GET'])
def download_video():
    try:
        url = request.args.get('url')
        logger.info(f"下载请求 - URL: {url}")

        if not url:
            logger.error("缺少 URL 参数")
            return jsonify({'error': '缺少必要的下载参数'}), 400

        # 转换 URL 为 Twitter 域名
        twitter_url = url.replace('x.com', 'twitter.com')

        def generate():
            try:
                cookies_file = os.path.abspath('cookies.txt')

                # 严格检查 cookies 文件
                if not os.path.exists(cookies_file):
                    logger.error(f"Cookies 文件未找到: {cookies_file}")
                    yield f"data: {json.dumps({'error': 'Cookies 文件未找到'})}\n\n"
                    return
                else:
                    logger.info(f"使用 Cookies 文件: {cookies_file}")

                ydl_opts = {
                    # 替换原来的 'cookies' 参数为以下两种方式之一：

                    # 方式1：直接使用浏览器 cookies（推荐）
                    # 'cookies_from_browser': ('chrome',),  # 自动从Chrome获取
                    # 方式2：使用文件（确保格式正确）：
                    'cookiefile': os.path.abspath('cookies.txt'),
                    'cookiestyle': 'netscape',

                    'format': 'best[ext=mp4]',
                    'outtmpl': os.path.join(data_dir, '%(title).80s.%(ext)s'),

                    # 关键修复 1：禁用 extract_flat（否则无法解析视频）
                    'extract_flat': False,

                    # 关键修复 2：强制启用调试日志
                    'quiet': False,

                    # 网络优化
                    'socket_timeout': 10,
                    'retries': 3,
                    'concurrent_fragments': 16,

                    # 进度回调
                    'progress_hooks': [lambda d: logger.info(
                        f"进度: {d.get('_percent_str', 'N/A')} | 速度: {d.get('_speed_str', 'N/A')}"
                    )],

                    # 错误处理
                    'ignoreerrors': False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"开始下载: {twitter_url}")

                    try:
                        # 关键修复 3：先获取信息再下载（分步调试）
                        info_dict = ydl.extract_info(twitter_url, download=False)
                        if not info_dict:
                            logger.error("无法获取视频信息")
                            yield f"data: {json.dumps({'error': '无法解析视频信息'})}\n\n"
                            return

                        logger.info(f"视频标题: {info_dict.get('title')}")

                        # 开始下载
                        ydl.download([twitter_url])
                        downloaded_file = ydl.prepare_filename(info_dict)

                        if os.path.exists(downloaded_file):
                            yield f"data: {json.dumps({'percent': 100, 'file': downloaded_file})}\n\n"
                        else:
                            logger.error("文件未生成，可能下载中断")
                            yield f"data: {json.dumps({'error': '文件生成失败'})}\n\n"

                    except yt_dlp.utils.DownloadError as e:
                        logger.error(f"下载错误: {str(e)}")
                        yield f"data: {json.dumps({'error': f'下载失败: {str(e)}'})}\n\n"

            except Exception as e:
                logger.error(f"处理错误: {traceback.format_exc()}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"全局错误: {traceback.format_exc()}")
        return jsonify({'error': '服务器处理错误'}), 500


def extract_video_id(url):
    # 使用正则表达式提取 Twitter/X 视频 ID
    match = re.search(r'/status/(\d+)', url)
    if match:
        return match.group(1)
    return None


if __name__ == '__main__':
    print("启动 Flask 应用...")
    print(f"Python 版本: {sys.version}")
    
    try:
        import flask
        print(f"Flask 版本: {flask.__version__}")
        
        # 添加更多的调试信息
        print("尝试配置应用...")
        
        # 确保日志输出到文件
        file_handler = logging.FileHandler('flask_debug.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        # 运行应用
        print("开始运行应用...")
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            use_reloader=False  # 禁用重载器以便更好地捕获错误
        )
    except Exception as e:
        print(f"启动失败，错误信息: {e}")
        print(f"详细错误追踪: {traceback.format_exc()}")
        # 将错误写入日志文件
        with open('startup_error.log', 'w', encoding='utf-8') as f:
            f.write(f"启动失败，错误信息: {e}\n")
            f.write(f"详细错误追踪: {traceback.format_exc()}")
