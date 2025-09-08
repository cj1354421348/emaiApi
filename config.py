import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # Mail.tm API配置
    MAIL_TM_API_KEY = os.getenv('MAIL_TM_API_KEY')
    MAIL_TM_BASE_URL = os.getenv('MAIL_TM_BASE_URL')
    MAIL_TM_DOMAIN = os.getenv('MAIL_TM_DOMAIN')
    
    # 默认密码
    DEFAULT_PASSWORD = os.getenv('DEFAULT_PASSWORD')