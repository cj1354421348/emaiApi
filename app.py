from flask import Flask, jsonify, request
from mail_client import MailTmClient
import threading
import time

app = Flask(__name__)

# 存储邮箱客户端实例的字典
email_clients = {}
# 用于线程安全的锁
clients_lock = threading.Lock()


@app.route('/api/email/<email_address>', methods=['GET'])
def get_email_content(email_address):
    try:
        # 检查是否已有该邮箱的客户端实例
        with clients_lock:
            if email_address in email_clients:
                client = email_clients[email_address]
            else:
                # 创建新的邮箱客户端实例
                # 注意：这里需要确保邮箱地址是通过MailTm服务创建的
                # 如果是外部邮箱地址，可能无法获取邮件
                try:
                    client = MailTmClient(email_address.split('@')[0])
                    email_clients[email_address] = client
                except Exception as e:
                    return jsonify({
                        "success": False,
                        "email": email_address,
                        "error": f"无法创建邮箱客户端: {str(e)}"
                    }), 500

        # 获取邮件内容
        message = client.wait_getmessage(60)  # 等待60秒
        print("app:获取邮件内容")
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


# 添加一个创建邮箱的接口
@app.route('/api/email', methods=['POST'])
def create_email():
    try:
        # 创建新的邮箱账户
        client = MailTmClient()
        email_address = client.get_email()
        
        # 保存客户端实例
        with clients_lock:
            email_clients[email_address] = client
        
        return jsonify({
            "success": True,
            "email": email_address
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)