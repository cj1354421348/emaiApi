import requests
import time
import json

# 测试邮件API功能

# API服务器地址
BASE_URL = "http://198.18.0.1:5000"

def create_email():
    """创建一个新的邮箱账户"""
    print("创建新的邮箱账户...")
    
    try:
        # 发送POST请求创建邮箱
        response = requests.post(f"{BASE_URL}/api/email")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                email_address = data.get("email")
                print(f"成功创建邮箱: {email_address}")
                return email_address
            else:
                print(f"创建邮箱失败: {data.get('error', '未知错误')}")
                return None
        else:
            print(f"请求失败: 状态码 {response.status_code}, 响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求出错: {str(e)}")
        return None

def test_get_email_content(email_address):
    """测试获取邮件内容"""
    print(f"测试获取邮件内容: {email_address}")
    
    try:
        # 发送GET请求获取邮件内容
        response = requests.get(f"{BASE_URL}/api/email/{email_address}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"成功: {data}")
            return data
        else:
            print(f"失败: 状态码 {response.status_code}, 响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求出错: {str(e)}")
        return None

def continuous_email_check(email_address, max_attempts=200, interval=5):
    """持续检查邮件内容"""
    print(f"开始持续检查邮件: {email_address}")
    print(f"最大尝试次数: {max_attempts}, 间隔: {interval}秒")
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n第 {attempt} 次尝试获取邮件...")
        
        try:
            # 发送GET请求获取邮件内容
            response = requests.get(f"{BASE_URL}/api/email/{email_address}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"成功获取邮件内容: {data}")
                    return data
                else:
                    print(f"未收到邮件: {data.get('error', '未知错误')}")
            else:
                print(f"请求失败: 状态码 {response.status_code}, 响应: {response.text}")
                
        except Exception as e:
            print(f"请求出错: {str(e)}")
        
        # 如果不是最后一次尝试，则等待
        if attempt < max_attempts:
            print(f"等待 {interval} 秒后再次尝试...")
            time.sleep(interval)
    
    print(f"\n已达到最大尝试次数 {max_attempts}，未收到邮件")
    return None

if __name__ == "__main__":
    # 创建一个新的邮箱账户
    print("=== 创建邮箱账户 ===")
    email_address = create_email()
    #email_address  = "zoshopho552_cunowos@wdzzh.ggff.net"
    if email_address:
        print(f"\n请向 {email_address} 发送一封邮件进行测试")
        
        # 测试持续获取邮件内容
        print("\n=== 测试持续获取邮件内容 ===")
        continuous_email_check(email_address, max_attempts=200, interval=5)
    else:
        print("无法创建邮箱账户，测试无法继续")