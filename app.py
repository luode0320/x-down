import logging
import os
import sys
import subprocess
import json
import traceback
import re
import yt_dlp
from flask import Flask, request, jsonify, render_template
from flask import send_from_directory, Response, send_file

try:
    from flask_cors import CORS
except ImportError:
    print("未找到 flask_cors 模块。请运行 'pip install flask-cors' 安装。")
    CORS = None

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

ARIA2C_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aria2', 'aria2-1.36.0-win-64bit-build1', 'aria2c.exe')
PROXY = None

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(data_dir, exist_ok=True)

app = Flask(__name__, static_folder='static', static_url_path='/static')
if CORS:
    CORS(app)


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

        twitter_url = url.replace('x.com', 'twitter.com')

        def generate():
            try:
                cookies_file = os.path.abspath('cookies.txt')

                if not os.path.exists(cookies_file):
                    logger.error(f"Cookies 文件未找到: {cookies_file}")
                    yield f"data: {json.dumps({'error': 'Cookies 文件未找到'})}\n\n"
                    return
                else:
                    logger.info(f"使用 Cookies 文件: {cookies_file}")

                ydl_opts = {
                    'cookiefile': os.path.abspath('cookies.txt'),
                    'cookiestyle': 'netscape',
                    'format': 'best[ext=mp4]',
                    'outtmpl': os.path.join(data_dir, '%(title).80s.%(ext)s'),
                    'extract_flat': False,
                    'quiet': False,
                    'socket_timeout': 10,
                    'retries': 3,
                    'concurrent_fragments': 16,
                    'progress_hooks': [lambda d: logger.info(
                        f"进度: {d.get('_percent_str', 'N/A')} | 速度: {d.get('_speed_str', 'N/A')}"
                    )],
                    'ignoreerrors': False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info(f"开始下载: {twitter_url}")
                    info_dict = ydl.extract_info(twitter_url, download=False)
                    if not info_dict:
                        logger.error("无法获取视频信息")
                        yield f"data: {json.dumps({'error': '无法解析视频信息'})}\n\n"
                        return

                    logger.info(f"视频标题: {info_dict.get('title')}")
                    ydl.download([twitter_url])
                    downloaded_file = ydl.prepare_filename(info_dict)

                    if os.path.exists(downloaded_file):
                        # 返回文件名而不是完整路径
                        filename = os.path.basename(downloaded_file)
                        yield f"data: {json.dumps({'percent': 100, 'filename': filename})}\n\n"
                    else:
                        logger.error("文件未生成，可能下载中断")
                        yield f"data: {json.dumps({'error': '文件生成失败'})}\n\n"

            except Exception as e:
                logger.error(f"处理错误: {traceback.format_exc()}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        logger.error(f"全局错误: {traceback.format_exc()}")
        return jsonify({'error': '服务器处理错误'}), 500


# 新增路由用于文件下载
@app.route('/get_file/<filename>')
def get_file(filename):
    try:
        file_path = os.path.join(data_dir, filename)
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        logger.error(f"文件下载错误: {str(e)}")
        return jsonify({'error': '文件下载失败'}), 500


if __name__ == '__main__':
    print("启动 Flask 应用...")
    print(f"Python 版本: {sys.version}")

    try:
        import flask

        print(f"Flask 版本: {flask.__version__}")
        print("尝试配置应用...")

        file_handler = logging.FileHandler('flask_debug.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        print("开始运行应用...")
        app.run(
            host='0.0.0.0',
            port=7777,
            debug=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"启动失败，错误信息: {e}")
        print(f"详细错误追踪: {traceback.format_exc()}")
        with open('startup_error.log', 'w', encoding='utf-8') as f:
            f.write(f"启动失败，错误信息: {e}\n")
            f.write(f"详细错误追踪: {traceback.format_exc()}")