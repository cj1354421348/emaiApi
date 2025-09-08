from flask import Flask, jsonify, request
from mail_client import MailTmClient
import threading

app = Flask(__name__)

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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)