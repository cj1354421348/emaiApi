#!/usr/bin/env python3
"""
简单的WebSocket客户端测试脚本
测试在原有HTTP API基础上新增的WebSocket功能
"""

import socketio
import time
import requests
from loguru import logger

# 服务器地址
BASE_URL = "http://localhost:5000"

def create_email_http():
    """使用原有HTTP API创建邮箱"""
    try:
        response = requests.post(f"{BASE_URL}/api/email")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("email")
    except Exception as e:
        logger.error(f"HTTP创建邮箱失败: {e}")
    return None

def test_websocket_push(email_address):
    """测试WebSocket实时推送功能"""
    
    # 创建WebSocket客户端
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ WebSocket连接成功")
        
    @sio.event
    def connection_response(data):
        print(f"📡 服务器响应: {data['message']}")
        
    @sio.event
    def auth_response(data):
        if data['type'] == 'auth_success':
            print(f"✅ 认证成功: {data['message']}")
        else:
            print(f"❌ 认证失败: {data['message']}")
            
    @sio.event
    def email_notification(data):
        """收到新邮件通知"""
        print("\n🎉 收到新邮件推送!")
        email_data = data['data']
        print(f"📧 邮箱: {email_data['email']}")
        print(f"📝 主题: {email_data['subject']}")
        print(f"👤 发件人: {email_data['from']}")
        print(f"⏰ 时间: {email_data['date']}")
        
        # 显示部分内容
        html_content = email_data.get('html', [])
        if html_content:
            print(f"📄 内容预览: {html_content[0][:100]}...")
        print("=" * 50)
        
    @sio.event
    def heartbeat_response(data):
        print(f"💓 心跳响应: {data['timestamp']}")
    
    try:
        # 连接WebSocket
        print(f"🔌 连接WebSocket服务器: {BASE_URL}")
        sio.connect(BASE_URL)
        
        # 等待连接建立
        time.sleep(1)
        
        # 发送认证信息
        print(f"🔐 认证邮箱: {email_address}")
        sio.emit('authenticate', {'email': email_address})
        
        # 等待认证完成
        time.sleep(2)
        
        print(f"\n📱 WebSocket实时监控已启动")
        print(f"📮 请向 {email_address} 发送邮件进行测试")
        print("💡 系统将实时推送新邮件，按 Ctrl+C 退出\n")
        
        # 定期发送心跳
        last_heartbeat = time.time()
        
        while True:
            # 每30秒发送一次心跳
            if time.time() - last_heartbeat > 30:
                sio.emit('heartbeat')
                last_heartbeat = time.time()
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断测试")
    except Exception as e:
        print(f"❌ WebSocket测试出错: {e}")
    finally:
        sio.disconnect()
        print("🔌 WebSocket连接已断开")

def main():
    """主函数"""
    print("🧪 WebSocket功能测试")
    print("=" * 40)
    
    # 1. 使用原有HTTP API创建邮箱
    print("📧 使用HTTP API创建邮箱...")
    email_address = create_email_http()
    
    if not email_address:
        print("❌ 无法创建邮箱，请检查HTTP API是否正常")
        return
    
    print(f"✅ 邮箱创建成功: {email_address}")
    
    # 2. 测试WebSocket实时推送
    print("\n🚀 开始WebSocket实时推送测试...")
    test_websocket_push(email_address)
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    main()