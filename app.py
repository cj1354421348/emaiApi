from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from mail_client import MailTmClient
import threading
import time
from loguru import logger
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 存储邮箱客户端实例的字典
email_clients = {}
# 用于线程安全的锁
clients_lock = threading.Lock()


@app.route('/api/email/<email_address>', methods=['GET'])
def get_email_content(email_address):
    """获取指定邮箱的邮件内容"""
    try:
        # 检查是否已有该邮箱的客户端实例
        with clients_lock:
            if email_address in email_clients:
                client = email_clients[email_address]
            else:
                # 创建邮箱客户端实例（用于现有账户）
                try:
                    client = MailTmClient(email=email_address)
                    email_clients[email_address] = client
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "email": email_address,
                        "error": f"无法初始化邮箱客户端: {str(e)}"
                    }), 500

        # 获取邮件内容
        message = client.wait_for_message(60)  # 等待60秒
        if message:
            # 提取邮件正文部分（完整HTML）
            html_content = ""
            if isinstance(message, dict) and 'html' in message and message['html'] and len(message['html']) > 0:
                html_content = message['html'][0]
            elif isinstance(message, str):
                # 如果返回的是字符串，直接使用
                html_content = message
            
            return jsonify({
                "success": True,
                "email": email_address,
                "content": html_content
            })
        else:
            return jsonify({
                "success": False,
                "email": email_address,
                "error": "未收到邮件或超时"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "email": email_address,
            "error": str(e)
        }), 500


@app.route('/api/email', methods=['POST'])
def get_or_create_email():
    """获取或创建指定邮箱账户（支持向后兼容）"""
    try:
        # 检查请求体是否为空（向后兼容原调用方式）
        if not request.is_json or not request.get_json():
            # 原来的调用方式：创建随机新账户
            client = MailTmClient()
            email_address = client.get_email()
            
            # 保存客户端实例
            with clients_lock:
                email_clients[email_address] = client
            
            return jsonify({
                "success": True,
                "email": email_address,
                "message": "创建随机新邮箱账户（向后兼容模式）"
            })
        
        # 新调用方式：提供指定邮箱地址
        email_address = request.json.get('email')
        if not email_address:
            return jsonify({
                "success": False,
                "error": "邮箱地址是必需的"
            }), 400
        
        # 检查是否已有该邮箱的客户端实例
        with clients_lock:
            if email_address in email_clients:
                client = email_clients[email_address]
                return jsonify({
                    "success": True,
                    "email": email_address,
                    "message": "使用现有邮箱账户"
                })
            else:
                # 尝试通过邮箱地址查找现有账户
                try:
                    from smtp_api import SMTPDevAPI
                    api = SMTPDevAPI()
                    account_data = api.get_account_by_email(email_address)
                    
                    if account_data:
                        # 找到现有账户，直接返回（不创建新客户端实例）
                        return jsonify({
                            "success": True,
                            "email": email_address,
                            "message": "使用现有邮箱账户"
                        })
                    else:
                        # 账户不存在，创建新账户
                        client = MailTmClient(email_address.split('@')[0])
                        email_clients[email_address] = client
                        return jsonify({
                            "success": True,
                            "email": email_address,
                            "message": "创建新邮箱账户"
                        })
                        
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "email": email_address,
                        "error": f"处理邮箱账户时出错: {str(e)}"
                    }), 500
                
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# WebSocket相关变量
ws_connections = {}  # {email: [sid1, sid2, ...]} - WebSocket连接映射
connection_emails = {}  # {sid: email} - 连接到邮箱的映射
monitoring_threads = {}  # 邮件监控线程

class EmailMonitor:
    """邮件监控类，用于WebSocket实时推送"""
    
    def __init__(self, email_address, client):
        self.email_address = email_address
        self.client = client
        self.is_running = False
        
    def start_monitoring(self):
        """开始监控邮件"""
        self.is_running = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
        return thread
        
    def stop_monitoring(self):
        """停止监控邮件"""
        self.is_running = False
        
    def _monitor_loop(self):
        """邮件监控循环"""
        logger.info(f"WebSocket开始监控邮箱: {self.email_address}")
        
        while self.is_running:
            try:
                # 检查新邮件
                message = self.client.get_latest_message()
                if message:
                    # 有新邮件，推送给WebSocket客户端
                    self._push_new_email(message)
                    
                time.sleep(2)  # 每2秒检查一次
                
            except Exception as e:
                logger.error(f"WebSocket邮件监控出错 {self.email_address}: {e}")
                time.sleep(5)
                
        logger.info(f"WebSocket停止监控邮箱: {self.email_address}")
        
    def _push_new_email(self, message):
        """推送新邮件到WebSocket客户端"""
        try:
            email_data = {
                'type': 'new_mail',
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'email': self.email_address,
                    'subject': message.get('subject', ''),
                    'from': message.get('from', {}),
                    'date': message.get('date', ''),
                    'html': message.get('html', []),
                    'text': message.get('text', [])
                }
            }
            
            # 推送给所有连接该邮箱的WebSocket客户端
            with clients_lock:
                if self.email_address in ws_connections:
                    for sid in ws_connections[self.email_address]:
                        socketio.emit('email_notification', email_data, room=sid)
                        logger.info(f"WebSocket推送新邮件到客户端 {sid}")
                        
        except Exception as e:
            logger.error(f"WebSocket推送邮件失败: {e}")

# WebSocket事件处理器
@socketio.on('connect')
def handle_connect():
    """处理WebSocket连接"""
    logger.info(f"WebSocket客户端连接: {request.sid}")
    emit('connection_response', {
        'type': 'connected',
        'timestamp': datetime.now().isoformat(),
        'message': 'WebSocket连接成功，请发送认证信息'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """处理WebSocket断开连接"""
    sid = request.sid
    logger.info(f"WebSocket客户端断开: {sid}")
    
    with clients_lock:
        if sid in connection_emails:
            email = connection_emails[sid]
            if email in ws_connections:
                ws_connections[email].remove(sid)
                if not ws_connections[email]:
                    # 该邮箱没有其他WebSocket连接，停止监控
                    del ws_connections[email]
                    if email in monitoring_threads:
                        monitoring_threads[email].stop_monitoring()
                        del monitoring_threads[email]
                        logger.info(f"停止WebSocket监控邮箱: {email}")
            del connection_emails[sid]

@socketio.on('authenticate')
def handle_authenticate(data):
    """处理WebSocket认证"""
    try:
        email_address = data.get('email')
        if not email_address:
            emit('auth_response', {
                'type': 'auth_error',
                'timestamp': datetime.now().isoformat(),
                'message': '邮箱地址是必需的'
            })
            return
            
        sid = request.sid
        logger.info(f"WebSocket认证: {sid} -> {email_address}")
        
        with clients_lock:
            # 确保邮箱客户端存在
            if email_address not in email_clients:
                try:
                    client = MailTmClient(email=email_address)
                    email_clients[email_address] = client
                except Exception as e:
                    emit('auth_response', {
                        'type': 'auth_error',
                        'timestamp': datetime.now().isoformat(),
                        'message': f'无法初始化邮箱客户端: {str(e)}'
                    })
                    return
            
            # 添加WebSocket连接映射
            if email_address not in ws_connections:
                ws_connections[email_address] = []
            ws_connections[email_address].append(sid)
            connection_emails[sid] = email_address
            
            # 启动邮件监控（如果还没有启动）
            if email_address not in monitoring_threads:
                monitor = EmailMonitor(email_address, email_clients[email_address])
                monitor.start_monitoring()
                monitoring_threads[email_address] = monitor
                logger.info(f"启动WebSocket邮件监控: {email_address}")
        
        join_room(email_address)
        
        emit('auth_response', {
            'type': 'auth_success',
            'timestamp': datetime.now().isoformat(),
            'message': f'WebSocket认证成功，开始监控邮箱: {email_address}'
        })
        
    except Exception as e:
        logger.error(f"WebSocket认证处理出错: {e}")
        emit('auth_response', {
            'type': 'auth_error',
            'timestamp': datetime.now().isoformat(),
            'message': f'认证失败: {str(e)}'
        })

@socketio.on('heartbeat')
def handle_heartbeat():
    """处理WebSocket心跳"""
    emit('heartbeat_response', {
        'type': 'heartbeat',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    import os
    logger.info("启动邮件API服务器 (HTTP + WebSocket)...")
    
    # 设置环境变量明确指定为开发环境
    os.environ['FLASK_ENV'] = 'development'
    
    # 使用更安全的启动方式
    socketio.run(
        app, 
        debug=True, 
        host='0.0.0.0', 
        port=5000, 
        allow_unsafe_werkzeug=True,
        use_reloader=True,
        log_output=False  # 减少日志输出
    )