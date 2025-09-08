import time
from loguru import logger
from username_generator import WordGenerator
from smtp_api import SMTPDevAPI
from config import Config


class MailTmClient:
    """简化版邮件客户端，只保留核心功能"""
    
    def __init__(self, user=None):
        """初始化客户端，创建新账户"""
        self.api = SMTPDevAPI()
        self.email = None
        self.account_id = None
        self.mailbox_id = None
        
        if user is None:
            generator = WordGenerator()
            user = generator.generate_combined_username(1)
        
        self._initialize_account(user)
    
    def _initialize_account(self, username):
        """初始化账户"""
        # 创建账户
        account_data = self.api.create_account(
            username + "@" + Config.MAIL_TM_DOMAIN,
            Config.DEFAULT_PASSWORD
        )
        
        if account_data:
            self.email = account_data["address"]
            self.account_id = account_data["id"]
            
            # 获取INBOX邮箱ID
            mailboxes = self.api.get_mailboxes(self.account_id)
            if mailboxes:
                for mailbox in mailboxes:
                    if mailbox["path"] == "INBOX":
                        self.mailbox_id = mailbox["id"]
                        break
            
            logger.info(f"账户初始化成功: {self.email}")
        else:
            raise Exception("无法创建账户")
    
    def get_email(self):
        """获取邮箱地址"""
        return self.email
    
    def get_latest_message(self):
        """获取最新消息"""
        if not all([self.account_id, self.mailbox_id]):
            raise Exception("账户未正确初始化")
        
        # 获取消息列表
        messages = self.api.get_messages(self.account_id, self.mailbox_id)
        if messages and len(messages) > 0:
            # 获取第一封邮件详情
            message_data = self.api.get_message_detail(
                self.account_id, 
                self.mailbox_id, 
                messages[0]["id"]
            )
            return message_data
        
        return None
    
    def wait_for_message(self, timeout=60):
        """等待新消息到达"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            message = self.get_latest_message()
            if message:
                return message
            time.sleep(2)
        
        logger.warning(f"等待消息超时: {timeout}秒")
        return None