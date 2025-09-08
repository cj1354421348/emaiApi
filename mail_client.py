import time
from loguru import logger
from username_generator import WordGenerator
from smtp_api import SMTPDevAPI
from config import Config


class MailTmClient:
    """简化版邮件客户端，只保留核心功能"""
    
    def __init__(self, email=None, username=None):
        """初始化客户端，支持现有账户和创建新账户"""
        self.api = SMTPDevAPI()
        self.email = email
        self.account_id = None
        self.mailbox_id = None
        self.processed_message_ids = set()  # 跟踪已处理的邮件ID
        
        if email:
            # 使用现有邮箱账户
            self._initialize_existing_account(email)
        else:
            # 创建新账户
            if username is None:
                generator = WordGenerator()
                username = generator.generate_combined_username(1)
            self._create_new_account(username)
    
    def _initialize_existing_account(self, email):
        """初始化现有账户"""
        # 通过邮箱地址查找账户
        account_data = self.api.get_account_by_email(email)
        
        if account_data:
            self.email = email
            self.account_id = account_data["id"]
            
            # 获取INBOX邮箱ID
            mailboxes = self.api.get_mailboxes(self.account_id)
            if mailboxes:
                for mailbox in mailboxes:
                    if mailbox["path"] == "INBOX":
                        self.mailbox_id = mailbox["id"]
                        break
            
            if self.mailbox_id:
                logger.info(f"现有账户初始化成功: {self.email}")
                # 初始化时获取已有邮件ID，避免将旧邮件当作新邮件
                self._initialize_processed_messages()
            else:
                raise Exception(f"无法获取邮箱 {email} 的INBOX")
        else:
            raise Exception(f"未找到邮箱账户: {email}")
    
    def _initialize_processed_messages(self):
        """初始化已处理邮件ID集合"""
        if not all([self.account_id, self.mailbox_id]):
            return
            
        try:
            # 获取当前所有邮件ID，避免将它们当作新邮件
            messages = self.api.get_messages(self.account_id, self.mailbox_id)
            if messages:
                for message in messages:
                    self.processed_message_ids.add(message["id"])
            logger.info(f"初始化已完成邮件跟踪，共有 {len(self.processed_message_ids)} 封已存在邮件")
        except Exception as e:
            logger.warning(f"初始化已处理邮件列表失败: {e}")
    
    def _create_new_account(self, username):
        """创建新账户"""
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
            
            if self.mailbox_id:
                logger.info(f"新账户创建成功: {self.email}")
            else:
                raise Exception(f"无法获取新账户 {self.email} 的INBOX")
        else:
            raise Exception("无法创建新账户")
    
    def get_email(self):
        """获取邮箱地址"""
        return self.email
    
    def get_latest_message(self):
        """获取最新未处理的消息"""
        if not all([self.account_id, self.mailbox_id]):
            raise Exception("账户未正确初始化")
        
        # 获取消息列表
        messages = self.api.get_messages(self.account_id, self.mailbox_id)
        if messages:
            # 查找第一个未处理的邮件
            for message in messages:
                message_id = message["id"]
                if message_id not in self.processed_message_ids:
                    # 获取邮件详情
                    message_data = self.api.get_message_detail(
                        self.account_id, 
                        self.mailbox_id, 
                        message_id
                    )
                    # 标记为已处理
                    self.processed_message_ids.add(message_id)
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