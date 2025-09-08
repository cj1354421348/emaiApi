import requests
from loguru import logger
import time
import random
from config import Config


class WordGenerator:
    def __init__(self):
        # 常用辅音字母
        self.consonants = "bcdfghjklmnpqrstvwxyz"
        # 元音字母
        self.vowels = "aeiou"
        # 常用的字母组合
        self.common_pairs = [
            "th",
            "ch",
            "sh",
            "ph",
            "wh",
            "br",
            "cr",
            "dr",
            "fr",
            "gr",
            "pr",
            "tr",
        ]
        # 常用的词尾
        self.common_endings = ["ing", "ed", "er", "est", "ly", "tion", "ment"]
        # 常用的用户名后缀
        self.username_suffixes = [
            "123",
            "888",
            "666",
            "777",
            "999",
            "pro",
            "cool",
            "good",
            "best",
        ]

    def generate_syllable(self):
        """生成一个音节"""
        if random.random() < 0.3 and self.common_pairs:  # 30% 概率使用常用字母组合
            return random.choice(self.common_pairs) + random.choice(self.vowels)
        else:
            return random.choice(self.consonants) + random.choice(self.vowels)

    def generate_word(self, min_length=4, max_length=8):
        """生成一个随机单词"""
        word = ""
        target_length = random.randint(min_length, max_length)

        # 添加音节直到达到目标长度附近
        while len(word) < target_length - 2:
            word += self.generate_syllable()

        # 可能添加常用词尾
        if random.random() < 0.3 and len(word) < max_length - 2:
            word += random.choice(self.common_endings)
        elif len(word) < target_length:
            word += random.choice(self.consonants)

        return word.lower()

    def generate_random_username(self, min_length=3, max_length=8):
        """生成随机用户名"""
        username = self.generate_word(min_length, max_length)

        # 50% 的概率添加数字或特殊后缀
        if random.random() < 0.5:
            if random.random() < 0.7:  # 70% 概率添加数字
                username += str(random.randint(0, 999)).zfill(random.randint(2, 3))
            else:  # 30% 概率添加特殊后缀
                username += random.choice(self.username_suffixes)

        return username

    def generate_combined_username(self, num_words=1, separator="_"):
        """生成完整的组合用户名"""
        # 首先生成基础用户名
        base_username = self.generate_random_username()

        # 生成额外的随机单词
        words = [self.generate_word() for _ in range(num_words)]

        # 随机决定用户名放在前面还是后面
        if random.random() < 0.5:
            words.append(base_username)
        else:
            words.insert(0, base_username)

        return separator.join(words)


class MailTmClient:
    baseurl = Config.MAIL_TM_BASE_URL
    api_key = Config.MAIL_TM_API_KEY

    def __init__(self, user=None):
        # 初始化token为None，防止未设置时引发属性错误
        self.token = None
        self.acount = None
        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json"
        }
        self.mailboxid = None
        self.accountid = None

        if user is None:
            generator = WordGenerator()
            user = generator.generate_combined_username(1)

        # 重试机制
        for attempt in range(3):
            try:
                domain = self.get_domains()
                if not domain:
                    logger.warning(f"尝试 {attempt + 1}/3: 获取域名失败，重试中...")
                    time.sleep(2)
                    continue

                logger.info("Get domain:" + domain)
                self.acount = user + "@" + domain
                logger.info("Get acount:" + self.acount)

                # 尝试创建账户
                account_result = self.acounts(self.acount)
                if not account_result:
                    # 如果创建账户失败，尝试查找现有账户
                    logger.info(f"创建账户失败，尝试查找现有账户: {self.acount}")
                    existing_account = self.get_account_by_email(self.acount)
                    if existing_account:
                        account_result = existing_account
                        logger.info(f"找到现有账户: {self.acount}")
                    else:
                        logger.warning(f"尝试 {attempt + 1}/3: 创建账户失败，重试中...")
                        time.sleep(2)
                        continue

                self.accountid = account_result["id"]
                logger.info("Get accountid:" + self.accountid)
                
                # 如果account_result包含mailboxes字段，直接使用
                if "mailboxes" in account_result:
                    mailboxes = account_result["mailboxes"]
                else:
                    # 否则获取邮箱列表
                    mailboxes_response = requests.get(
                        f"{self.baseurl}/accounts/{self.accountid}/mailboxes",
                        headers=self.headers,
                        timeout=10
                    )
                    if mailboxes_response.status_code == 200:
                        mailboxes = mailboxes_response.json()
                    else:
                        logger.error(f"获取邮箱列表失败: 状态码 {mailboxes_response.status_code}")
                        continue

                for mailbox in mailboxes:
                    if mailbox["path"] == "INBOX":
                        self.mailboxid = mailbox["id"]
                        logger.info("Get mailboxid:" + self.mailboxid)
                        break
                if not self.mailboxid:
                    logger.error("未找到INBOX邮箱")
                    continue

                token_result = self.get_token()
                if not token_result:
                    logger.warning(f"尝试 {attempt + 1}/3: 获取令牌失败，重试中...")
                    time.sleep(2)
                    continue

                # 成功初始化
                break
            except Exception as e:
                logger.error(f"初始化邮箱客户端出错 (尝试 {attempt + 1}/3): {str(e)}")
                if attempt < 2:  # 如果不是最后一次尝试，则等待后重试
                    time.sleep(3)
                else:
                    raise Exception(f"初始化邮箱客户端失败，已重试3次: {str(e)}")

    def get_email(self):
        return self.acount

    def get_domains(self):
        return Config.MAIL_TM_DOMAIN

    def acounts(self, acount):
        try:
            json_data = {
                "address": acount,
                "password": Config.DEFAULT_PASSWORD,
            }
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            response = requests.post(
                f"{self.baseurl}/accounts", headers=headers, json=json_data, timeout=10
            )

            # 如果账户已存在，返回None但不报错
            if response.status_code == 422:
                error_data = response.json()
                if "address: This value is already used" in str(error_data):
                    logger.info(f"账户已存在: {acount}")
                    return None

            if response.status_code != 201 and response.status_code != 200:
                logger.error(f"创建账户失败: 状态码 {response.status_code}")
                if response.text:
                    logger.info("acounts:" + response.text)
                return None

            if not response.text:
                logger.error("创建账户失败: 空响应")
                return None

            logger.info("acounts:" + response.text)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"创建账户请求出错: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"解析账户响应出错: {str(e)}")
            return None

    def get_token(self):
        try:
            response = requests.get(
                f"{self.baseurl}/tokens", headers=self.headers, timeout=10
            )

            if response.status_code != 200:
                logger.error(f"获取令牌失败: 状态码 {response.status_code}")
                if response.text:
                    logger.info("get_token:" + response.text)
                return None

            if not response.text:
                logger.error("获取令牌失败: 空响应")
                return None

            logger.info("get_token:" + response.text)
            response_data = response.json()

            self.token = response_data[0]["id"]
            logger.info(f"token: {self.token}")
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"获取令牌请求出错: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"解析令牌响应出错: {str(e)}")
            return None

    def getmessage(self):
        try:
            # 先检查token是否存在
            if not hasattr(self, "token") or self.token is None:
                logger.error("获取消息失败: token未初始化")
                return None

            response = requests.get(
                f"{self.baseurl}/accounts/{self.accountid}/mailboxes/{self.mailboxid}/messages", headers=self.headers, timeout=10
            )

            if response.status_code != 200:
                logger.error(f"获取消息失败: 状态码 {response.status_code}")
                return None

            response_data = response.json()

            if response_data and len(response_data) > 0:
                # 获取第一封邮件
                message = response_data[0]
                logger.info("Get message:" + message["intro"])
                # 获取完整邮件内容
                message_id = message["id"]
                full_message_response = requests.get(
                    f"{self.baseurl}/accounts/{self.accountid}/mailboxes/{self.mailboxid}/messages/{message_id}", 
                    headers=self.headers, 
                    timeout=10
                )
                
                if full_message_response.status_code == 200:
                    full_message_data = full_message_response.json()
                    return full_message_data
                else:
                    # 如果获取完整邮件失败，返回完整响应数据
                    logger.error(f"获取完整邮件失败: 状态码 {full_message_response.status_code}")
                    return message
            else:
                print("返回空")
                return None
        except Exception as e:
            logger.error(f"获取消息时出错: {str(e)}")
            return None

    def wait_getmessage(self, max_wait_time=60):  # 缩短默认等待时间为60秒
        # 先检查token是否初始化
        if not hasattr(self, "token") or self.token is None:
            logger.error("等待消息失败: token未初始化")
            return None
        print("1")
        start_time = time.time()
        check_count = 0

        while True:
            try:
                message = self.getmessage()
                if message is not None:
                    return message

                # 检查是否超时
                if time.time() - start_time > max_wait_time:
                    logger.error(f"等待消息超时，已等待{max_wait_time}秒")
                    return None

                check_count += 1
                if check_count > 15:  # 如果检查超过15次仍未收到邮件，认为邮箱有问题
                    logger.warning(f"多次检查未收到邮件，邮箱可能有问题: {self.acount}")
                    return None

                logger.info(f"等待邮件中... ({check_count}/15)")
                time.sleep(2)  # 增加等待时间，减轻请求频率
            except Exception as e:
                logger.error(f"等待消息时出错: {str(e)}")
                # 如果是token相关错误，直接返回None
                if "token" in str(e).lower():
                    logger.error("token错误，放弃当前邮箱")
                    return None
                time.sleep(2)

    def get_all_accounts(self):
        response = requests.get(
            f"{self.baseurl}/accounts", headers=self.headers, timeout=10
        )
        return response.json()

    def delete_account(self, accountid):
        headers = {
            "X-API-KEY": self.api_key
        }
        response = requests.delete(
            f"{self.baseurl}/accounts/{accountid}", headers=headers, timeout=10
        )

    def delete_all_accounts(self):
        accounts = self.get_all_accounts()
        for account in accounts:
            time.sleep(3)
            self.delete_account(account["id"])
            print(f"删除账户 {account['id']} 成功")

    @staticmethod
    def get_account_by_email(email_address, api_key=None):
        """
        通过邮箱地址查找账户信息
        
        Args:
            email_address (str): 邮箱地址
            api_key (str, optional): API密钥
            
        Returns:
            dict: 账户信息或None（如果未找到）
        """
        try:
            # 使用默认API密钥如果未提供
            if api_key is None:
                api_key = Config.MAIL_TM_API_KEY
            
            baseurl = Config.MAIL_TM_BASE_URL
            headers = {
                "X-API-KEY": api_key,
                "Accept": "application/json"
            }
            
            # 获取账户列表
            accounts_response = requests.get(f"{baseurl}/accounts", headers=headers, timeout=10)
            if accounts_response.status_code != 200:
                logger.error(f"获取账户列表失败: 状态码 {accounts_response.status_code}")
                return None
                
            accounts_data = accounts_response.json()
            
            # 查找匹配的邮箱地址
            for account in accounts_data:
                if account.get("address") == email_address:
                    # 获取完整的账户信息
                    account_id = account["id"]
                    full_account_response = requests.get(
                        f"{baseurl}/accounts/{account_id}",
                        headers=headers,
                        timeout=10
                    )
                    if full_account_response.status_code == 200:
                        return full_account_response.json()
                    else:
                        # 如果无法获取完整信息，返回基本账户信息
                        return account
                    
            # 未找到匹配的账户
            logger.info(f"未找到邮箱地址 {email_address} 对应的账户")
            return None
            
        except Exception as e:
            logger.error(f"通过邮箱地址查找账户时出错: {str(e)}")
            return None

    @staticmethod
    def get_messages_by_account(account_id, mailbox_id, api_key=None):
        """
        通过账户ID和邮箱ID直接获取邮件内容
        
        Args:
            account_id (str): Mail.tm账户ID
            mailbox_id (str): Mail.tm邮箱ID
            api_key (str, optional): API密钥
            
        Returns:
            list: 邮件列表或None（如果出错）
        """
        try:
            # 使用默认API密钥如果未提供
            if api_key is None:
                api_key = Config.MAIL_TM_API_KEY
            
            baseurl = Config.MAIL_TM_BASE_URL
            headers = {
                "X-API-KEY": api_key,
                "Accept": "application/json"
            }
            
            # 获取邮件列表
            messages_response = requests.get(
                f"{baseurl}/accounts/{account_id}/mailboxes/{mailbox_id}/messages",
                headers=headers,
                timeout=10
            )
            
            if messages_response.status_code != 200:
                logger.error(f"获取邮件列表失败: 状态码 {messages_response.status_code}")
                return None
                
            messages_data = messages_response.json()
            
            # 获取每封邮件的详细内容
            detailed_messages = []
            for message in messages_data:
                message_id = message["id"]
                full_message_response = requests.get(
                    f"{baseurl}/accounts/{account_id}/mailboxes/{mailbox_id}/messages/{message_id}",
                    headers=headers,
                    timeout=10
                )
                
                if full_message_response.status_code == 200:
                    full_message_data = full_message_response.json()
                    detailed_messages.append(full_message_data)
                else:
                    # 如果获取完整邮件失败，添加原始消息数据
                    detailed_messages.append(message)
            
            return detailed_messages
            
        except Exception as e:
            logger.error(f"通过账户获取邮件时出错: {str(e)}")
            return None

    @staticmethod
    def get_messages_by_email(email_address, api_key=None):
        """
        通过邮箱地址直接获取邮件内容
        
        Args:
            email_address (str): 邮箱地址
            api_key (str, optional): API密钥
            
        Returns:
            list: 邮件列表或None（如果出错）
        """
        try:
            # 使用默认API密钥如果未提供
            if api_key is None:
                api_key = Config.MAIL_TM_API_KEY
            
            # 首先通过邮箱地址查找账户信息
            account = MailTmClient.get_account_by_email(email_address, api_key)
            if not account:
                logger.error(f"未找到邮箱地址 {email_address} 对应的账户")
                return None
                
            account_id = account["id"]
            
            # 获取邮箱列表以找到INBOX
            baseurl = Config.MAIL_TM_BASE_URL
            headers = {
                "X-API-KEY": api_key,
                "Accept": "application/json"
            }
            
            mailboxes_response = requests.get(
                f"{baseurl}/accounts/{account_id}/mailboxes",
                headers=headers,
                timeout=10
            )
            
            if mailboxes_response.status_code != 200:
                logger.error(f"获取邮箱列表失败: 状态码 {mailboxes_response.status_code}")
                return None
                
            mailboxes_data = mailboxes_response.json()
            
            # 查找INBOX邮箱
            inbox = None
            for mailbox in mailboxes_data:
                if mailbox.get("path") == "INBOX":
                    inbox = mailbox
                    break
                    
            if not inbox:
                logger.error(f"未找到邮箱地址 {email_address} 的INBOX")
                return None
                
            mailbox_id = inbox["id"]
            
            # 获取邮件内容
            messages = MailTmClient.get_messages_by_account(account_id, mailbox_id, api_key)
            return messages
            
        except Exception as e:
            logger.error(f"通过邮箱地址获取邮件时出错: {str(e)}")
            return None