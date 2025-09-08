# 简化版临时邮箱API架构设计

## 设计目标
1. 只保留两个核心接口功能
2. 简化代码结构，提高可维护性
3. 保持现有API接口兼容性

## 核心功能
1. POST /api/email - 创建新的临时邮箱账户
2. GET /api/email/<email_address> - 获取指定邮箱的邮件内容

## 架构设计

### 项目结构
```
temp-mail-api/
├── app.py              # Flask应用入口和API接口
├── mail_client.py      # Mail.tm客户端实现
├── username_generator.py  # 用户名生成器
├── config.py           # 配置管理
├── .env                # 环境变量配置
├── .gitignore          # Git忽略文件
└── README.md           # 项目说明文档
```

### 数据流设计
1. 创建邮箱请求 -> MailTmClient创建账户 -> 返回邮箱地址
2. 获取邮件请求 -> MailTmClient获取邮件 -> 返回邮件内容

### 简化策略
1. 移除不必要的功能方法
2. 合并重复的代码逻辑
3. 简化错误处理流程
4. 优化配置管理