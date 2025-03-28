import logging
import os
import sys
import json
import traceback
from threading import Event, Lock
from collections import defaultdict
import schedule
import yt_dlp
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template
from flask import Response, send_file

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

PROXY = None

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(data_dir, exist_ok=True)

app = Flask(__name__, static_folder='static', static_url_path='/static')
if CORS:
    CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有域


# 线程池（最多允许 2 条线程）
thread_pool = ThreadPoolExecutor(max_workers=2)
# 全局变量管理下载任务
download_tasks = defaultdict(dict)
download_lock = Lock()

# 计算文件夹总大小的函数
def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for file in filenames:
            file_path = os.path.join(dirpath, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)  # 累加文件大小
    return total_size

# 删除data_dir下所有文件的函数
def clean_data_dir():
    try:
        # 计算文件夹总大小（以字节为单位）
        folder_size = get_folder_size(data_dir)
        one_gb = 1 * 1024 * 1024 * 1024  # 1GB 的字节数

        # 如果文件夹大小未超过 1GB，则跳过清理
        if folder_size <= one_gb:
            return

        # 获取当前时间
        current_time = time.time()
        one_hour_ago = current_time - 3600  # 一小时前的时间戳（3600秒 = 1小时）

        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            if os.path.isfile(file_path):
                # 获取文件的创建时间或修改时间
                file_timestamp = os.path.getctime(file_path)  # 或者使用 os.path.getmtime(file_path)
                # 如果文件时间戳早于一小时前，则删除
                if file_timestamp < one_hour_ago:
                    os.remove(file_path)
                    logger.info(f"已删除文件: {file_path} (创建时间: {datetime.fromtimestamp(file_timestamp)})")
    except Exception as e:
        logger.error(f"清理目录时出错: {str(e)}")


# 每小时清理一次
schedule.every().hour.do(clean_data_dir)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return f"Error: {str(e)}", 500


@app.route('/check_video', methods=['GET'])
def check_video():
    try:
        url = request.args.get('url')
        logger.info(f"检查视频请求 - URL: {url}")

        if not url:
            logger.error("缺少 URL 参数")
            return jsonify({'error': '缺少URL参数'}), 400

        twitter_url = url.replace('x.com', 'twitter.com')

        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cookies_file = os.path.join(script_dir, 'config', 'cookies.txt')

        if not os.path.exists(cookies_file):
            logger.error(f"Cookies 文件未找到: {cookies_file}")
            return jsonify({'error': 'Cookies 文件未找到'}), 400

        ydl_opts = {
            'cookiefile': cookies_file,
            'cookiestyle': 'netscape',
            'format': 'best[ext=mp4]',
            'extract_flat': False,
            'quiet': True,
            'socket_timeout': 10,
            'retries': 3,
            'ignoreerrors': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"开始获取视频信息: {twitter_url}")
            info_dict = ydl.extract_info(twitter_url, download=False)

            if not info_dict:
                logger.error("无法获取视频信息")
                return jsonify({'error': '无法解析视频信息'}), 400

            # 获取视频大小（MB）
            file_size_bytes = info_dict.get('filesize') or info_dict.get('filesize_approx')
            file_size_mb = None
            if file_size_bytes:
                file_size_mb = round(file_size_bytes / (1024 * 1024) / 2, 2)  # 转换为MB并保留2位小数, 预估数据/2

            # 获取视频标题
            video_title = info_dict.get('title', '未知标题')

            # 获取视频时长（秒）
            duration = info_dict.get('duration')
            duration_str = None
            if duration:
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{int(minutes)}分{int(seconds)}秒"

            # 构建返回数据
            video_info = {
                'title': video_title,
                'size_mb': file_size_mb,
                'duration': duration_str,
                'url': twitter_url,
                'can_download': file_size_mb <= 500 if file_size_mb else True  # 是否允许下载（小于500MB）
            }

            logger.info(f"视频信息获取成功: {video_info}")
            return jsonify(video_info)

    except Exception as e:
        logger.error(f"检查视频时出错: {traceback.format_exc()}")
        return jsonify({'error': f'获取视频信息失败: {str(e)}'}), 500

@app.route('/download', methods=['GET'])
def download_video():
    try:
        url = request.args.get('url')
        session_id = request.args.get('session_id')  # 前端生成的会话ID
        logger.info(f"下载请求 - URL: {url}")
        logger.error(f"下载请求 - Id: {session_id}")

        if not url:
            logger.error("缺少 URL 参数")
            return jsonify({'error': '缺少必要的下载参数'}), 400

        twitter_url = url.replace('x.com', 'twitter.com')

        # 创建停止事件
        stop_event = Event()
        with download_lock:
            download_tasks[session_id] = {'stop_event': stop_event}

        def generate():
            try:
                # 获取脚本所在目录的绝对路径
                script_dir = os.path.dirname(os.path.abspath(__file__))
                cookies_file = os.path.join(script_dir, 'config', 'cookies.txt')

                if not os.path.exists(cookies_file):
                    logger.error(f"Cookies 文件未找到: {cookies_file}")
                    yield f"data: {json.dumps({'error': 'Cookies 文件未找到'})}\n\n"
                    return
                else:
                    logger.info(f"使用 Cookies 文件: {cookies_file}")

                # 创建一个队列用于传递进度信息
                from queue import Queue
                progress_queue = Queue()

                # 定义进度钩子函数
                def progress_hook(d):
                    if stop_event.is_set():
                        logger.error(f"中断下载: {session_id}")
                        d['fd'].close()  # 关闭文件下载句柄

                    if d['status'] == 'downloading':
                        percent = d.get('_percent_str', 'N/A').strip()
                        speed = d.get('_speed_str', 'N/A').strip()
                        eta = d.get('_eta_str', 'N/A').strip()
                        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')

                        file_size_mb = 'N/A'
                        if total_bytes:
                            file_size_mb = f"{total_bytes / (1024 * 1024):.2f} MB"

                        # 将速度从 MiB/s 转换为 MB/s
                        try:
                            speed_in_mib = float(speed.replace("MiB/s", "").strip())
                            speed_in_mb = speed_in_mib * (1024 * 1024) / (1000 * 1000)
                            speed_formatted = f"{speed_in_mb:.2f} MB/s"  # 格式化为两位小数
                        except ValueError:
                            speed_formatted = "0.00 MB/s"

                        # 打印进度到后台日志
                        logger.info(f"下载进度: {percent}, 速度: {speed_formatted}, 剩余时间: {eta}, 视频大小: {file_size_mb}")

                        # 将进度信息放入队列
                        progress_data = json.dumps({
                            'status': 'downloading',
                            'percent': percent,
                            'speed': speed_formatted,
                            'eta': eta,
                            'size': file_size_mb,
                        })
                        progress_queue.put(f"data: {progress_data}\n\n")

                ydl_opts = {
                    'cookiefile': cookies_file,
                    'cookiestyle': 'netscape',
                    'format': 'best[ext=mp4]',
                    'outtmpl': os.path.join(data_dir, '%(title).80s.%(ext)s'),
                    'extract_flat': False,
                    'quiet': False,
                    'socket_timeout': 10,
                    'retries': 3,
                    'concurrent_fragments': 16,
                    'progress_hooks': [progress_hook],  # 使用普通函数作为钩子
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
                    downloaded_file = ydl.prepare_filename(info_dict)

                    # 启动下载任务
                    def download_task():
                        try:
                            ydl.download([twitter_url])
                        except Exception as e:
                            logger.error(f"下载错误: {session_id}")
                            progress_queue.put(f"data: {json.dumps({'error': str(e)})}\n\n")

                    # 使用线程运行下载任务，避免阻塞主生成器

                    # 提交下载任务到线程池
                    future = thread_pool.submit(download_task)

                    # 持续从队列中读取进度信息并推送到前端
                    while not future.done() or not progress_queue.empty():
                        while not progress_queue.empty():
                            yield progress_queue.get()
                        time.sleep(0.1)

                    # 等待下载任务完成
                    future.result()

                    # 校验文件是否存在且完整
                    if os.path.exists(downloaded_file):
                        file_size = os.path.getsize(downloaded_file)
                        expected_size = info_dict.get('filesize', None)
                        if expected_size and file_size != expected_size:
                            logger.error(f"文件大小不匹配: 实际大小={file_size}, 预期大小={expected_size}")
                            yield f"data: {json.dumps({'error': '文件下载不完整'})}\n\n"
                        else:
                            filename = os.path.basename(downloaded_file)
                            yield f"data: {json.dumps({'status': 'finished', 'percent': '100%', 'filename': filename})}\n\n"
                    else:
                        logger.error("文件未生成，可能下载中断")
                        yield f"data: {json.dumps({'error': '文件生成失败'})}\n\n"

            except Exception as e:
                logger.error(f"处理错误: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                with download_lock:
                    if session_id in download_tasks:
                        del download_tasks[session_id]

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


@app.route('/cancel_download', methods=['GET'])
def cancel_download():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': '缺少session_id'}), 400

    logger.error(f"请求中断下载 - Id: {session_id}")
    with download_lock:
        if session_id in download_tasks:
            download_tasks[session_id]['stop_event'].set()
            del download_tasks[session_id]
            return jsonify({'status': 'cancelled'})

    return jsonify({'error': 'session not found'}), 404


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
        app.run(host='0.0.0.0', port=7777, debug=True, use_reloader=False)
    except Exception as e:
        print(f"启动失败，错误信息: {e}")
        print(f"详细错误追踪: {traceback.format_exc()}")
        with open('startup_error.log', 'w', encoding='utf-8') as f:
            f.write(f"启动失败，错误信息: {e}\n")
            f.write(f"详细错误追踪: {traceback.format_exc()}")