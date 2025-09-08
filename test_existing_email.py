import requests
import time
import json

# API服务器地址
BASE_URL = "http://198.18.0.1:5000"

def test_direct_get_existing_email():
    """测试直接获取现有邮箱的邮件内容（无需创建接口）"""
    print("=== 测试直接获取现有邮箱邮件内容 ===")
    
    # 指定一个已存在的邮箱地址（请替换为实际存在的邮箱）
    existing_email = "thixuy_dafrux@wdzzh.ggff.net"  # 请修改为实际存在的邮箱
    
    print(f"测试邮箱: {existing_email}")
    print("直接调用GET接口获取邮件内容（无需先调用POST创建）")
    
    try:
        # 直接发送GET请求获取邮件内容
        response = requests.get(f"{BASE_URL}/api/email/{existing_email}")
        
        print(f"请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✓ 成功！直接获取现有邮箱邮件内容")
                print(f"邮箱: {data.get('email')}")
                print(f"邮件内容长度: {len(data.get('content', ''))}")
                
                # 显示邮件内容预览
                content = data.get('content', '')
                if content:
                    if len(content) > 500:
                        print(f"邮件内容预览:\n{content[:500]}...")
                    else:
                        print(f"邮件内容:\n{content}")
                else:
                    print("邮件内容为空")
                    
                return True
            else:
                print(f"✗ 未收到邮件: {data.get('error', '未知错误')}")
                print("这可能是正常的，如果该邮箱确实没有新邮件")
                return False
        elif response.status_code == 404:
            print("✗ 404 - 未收到邮件或超时")
            print("这可能是正常的，如果该邮箱确实没有新邮件")
            return False
        else:
            print(f"✗ 请求失败: 状态码 {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 网络请求错误: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON解析错误: {str(e)}")
        print(f"响应内容: {response.text}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {str(e)}")
        return False

def test_get_with_waiting(existing_email):
    """测试带等待功能的现有邮箱邮件获取"""
    print(f"\n=== 测试等待现有邮箱新邮件: {existing_email} ===")
    
    print("开始等待新邮件（最多等待30秒）...")
    
    try:
        # 发送GET请求，接口会自动等待60秒
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/email/{existing_email}")
        end_time = time.time()
        
        print(f"请求耗时: {end_time - start_time:.1f} 秒")
        print(f"请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("✓ 成功获取现有邮箱的新邮件！")
                print(f"邮箱: {data.get('email')}")
                print(f"邮件内容长度: {len(data.get('content', ''))}")
                
                # 显示邮件内容
                content = data.get('content', '')
                if content:
                    if len(content) > 300:
                        print(f"邮件内容预览:\n{content[:300]}...")
                    else:
                        print(f"邮件内容:\n{content}")
                return True
            else:
                print(f"✗ 等待超时，未收到新邮件: {data.get('error', '未知错误')}")
                return False
        else:
            print(f"✗ 请求失败: 状态码 {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 网络请求错误: {str(e)}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON解析错误: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ 未知错误: {str(e)}")
        return False

def test_error_scenarios():
    """测试错误场景"""
    print("\n=== 测试错误场景 ===")
    
    # 测试1: 不存在的邮箱
    non_existent_email = "nonexistent@wdzzh.ggff.net"
    print(f"测试1: 不存在的邮箱 {non_existent_email}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/email/{non_existent_email}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("success"):
                print("✓ 正确返回'未收到邮件'错误")
                print(f"错误信息: {data.get('error')}")
            else:
                print("✗ 错误：不存在的邮箱居然返回成功")
        else:
            print(f"状态码: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 测试出错: {str(e)}")
    
    print(f"\n测试2: 无效邮箱格式")
    invalid_email = "invalid-email"
    
    try:
        response = requests.get(f"{BASE_URL}/api/email/{invalid_email}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:200]}...")
    except Exception as e:
        print(f"✗ 测试出错: {str(e)}")

def test_cache_mechanism():
    """测试缓存机制"""
    print("\n=== 测试客户端缓存机制 ===")
    
    test_email = "thixuy_dafrux@wdzzh.ggff.net"
    print(f"测试邮箱: {test_email}")
    
    # 第一次调用 - 应该初始化客户端
    print("\n第一次调用 - 初始化客户端:")
    start_time = time.time()
    response1 = requests.get(f"{BASE_URL}/api/email/{test_email}")
    time1 = time.time() - start_time
    print(f"响应时间: {time1:.2f}秒")
    print(f"状态码: {response1.status_code}")
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"第一次响应: {json.dumps(data1, indent=2)[:200]}...")
    
    # 第二次调用 - 应该使用缓存，响应更快
    print("\n第二次调用 - 使用缓存:")
    start_time = time.time()
    response2 = requests.get(f"{BASE_URL}/api/email/{test_email}")
    time2 = time.time() - start_time
    print(f"响应时间: {time2:.2f}秒")
    print(f"状态码: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"第二次响应: {json.dumps(data2, indent=2)[:200]}...")
        print(f"缓存效果: {'✓ 有效' if time2 < time1 * 0.8 else '✗ 无明显加速'}")

def main():
    """主测试函数"""
    print("临时邮箱API - 现有邮箱直接获取测试")
    print("=" * 50)
    
    # 配置测试邮箱（请根据实际情况修改）
    # 如果您有已存在的测试邮箱，请修改这里的邮箱地址
    EXISTING_EMAIL = "thixuy_dafrux@wdzzh.ggff.net"  # 请替换为实际存在的邮箱
    
    print(f"配置的测试邮箱: {EXISTING_EMAIL}")
    print("注意: 请确保该邮箱在SMTP.dev服务中已存在\n")
    
    # 测试1: 直接获取现有邮箱邮件内容
    success1 = test_direct_get_existing_email()
    
    # 测试2: 带等待功能的获取
    if success1 or input("是否继续测试等待功能? (y/n): ").lower() == 'y':
        test_get_with_waiting(EXISTING_EMAIL)
    
    # 测试3: 错误场景测试
    if input("是否运行错误场景测试? (y/n): ").lower() == 'y':
        test_error_scenarios()
    
    # 测试4: 缓存机制测试
    if input("是否运行缓存机制测试? (y/n): ").lower() == 'y':
        test_cache_mechanism()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("\n总结:")
    print("- 如果邮箱存在且有邮件: 应该能直接获取邮件内容")
    print("- 如果邮箱存在但无新邮件: 返回'未收到邮件或超时'")
    print("- 如果邮箱不存在: 可能返回错误或创建新账户（取决于配置）")

if __name__ == "__main__":
    main()