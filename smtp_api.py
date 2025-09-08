import requests
from loguru import logger
from config import Config


class SMTPDevAPI:
    """SMTP.dev邮件服务器API客户端"""
    
    BASE_URL = Config.MAIL_TM_BASE_URL
    DEFAULT_HEADERS = {
        "X-API-KEY": Config.MAIL_TM_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.session.timeout = 10
    
    def create_account(self, email, password):
        """
        创建新账户
        
        Args:
            email (str): 邮箱地址
            password (str): 密码
            
        Returns:
            dict: 账户信息或None（失败时）
        """
        json_data = {
            "address": email,
            "password": password,
        }
        
        try:
            response = self.session.post(
                f"{self.BASE_URL}/accounts",
                json=json_data
            )
            
            if response.status_code in [200, 201]:
                account_data = response.json()
                logger.info(f"账户创建成功: {email}")
                return account_data
            else:
                logger.error(f"账户创建失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"创建账户请求出错: {str(e)}")
            return None
    
    def get_account_by_email(self, email):
        """
        通过邮箱地址查找账户
        
        Args:
            email (str): 邮箱地址
            
        Returns:
            dict: 账户信息或None（未找到时）
        """
        try:
            # 获取所有账户列表
            response = self.session.get(f"{self.BASE_URL}/accounts")
            
            if response.status_code == 200:
                accounts = response.json()
                
                # 查找匹配的邮箱地址
                for account in accounts:
                    if account.get("address") == email:
                        # 获取完整账户信息
                        account_id = account["id"]
                        detail_response = self.session.get(
                            f"{self.BASE_URL}/accounts/{account_id}"
                        )
                        
                        if detail_response.status_code == 200:
                            return detail_response.json()
                        else:
                            logger.error(f"获取账户详情失败: {detail_response.status_code}")
                            return account
                
                logger.info(f"未找到邮箱地址 {email} 对应的账户")
                return None
            else:
                logger.error(f"获取账户列表失败: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"查找账户请求出错: {str(e)}")
            return None
    
    def get_mailboxes(self, account_id):
        """
        获取账户的邮箱列表
        
        Args:
            account_id (str): 账户ID
            
        Returns:
            list: 邮箱列表或None（失败时）
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/accounts/{account_id}/mailboxes"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取邮箱列表失败: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取邮箱列表请求出错: {str(e)}")
            return None
    
    def get_messages(self, account_id, mailbox_id):
        """
        获取邮箱中的消息列表
        
        Args:
            account_id (str): 账户ID
            mailbox_id (str): 邮箱ID
            
        Returns:
            list: 消息列表或None（失败时）
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/accounts/{account_id}/mailboxes/{mailbox_id}/messages"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取消息列表失败: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取消息列表请求出错: {str(e)}")
            return None
    
    def get_message_detail(self, account_id, mailbox_id, message_id):
        """
        获取消息详情
        
        Args:
            account_id (str): 账户ID
            mailbox_id (str): 邮箱ID
            message_id (str): 消息ID
            
        Returns:
            dict: 消息详情或None（失败时）
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/accounts/{account_id}/mailboxes/{mailbox_id}/messages/{message_id}"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取消息详情失败: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取消息详情请求出错: {str(e)}")
            return None