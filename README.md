# 临时邮箱API服务

这是一个基于SMTP.dev服务的临时邮箱API服务，提供创建邮箱和接收邮件的功能。

## 主要功能

- 创建临时邮箱账户
- 获取邮件内容（支持等待新邮件）
- 支持指定邮箱地址直接使用
- 自动处理邮件去重，确保只返回新邮件

## 快速开始

### 1. 环境配置

1. 复制 `.env.example` 到 `.env` 并配置以下参数：
   ```
   MAIL_TM_API_KEY=your_api_key_here
   MAIL_TM_BASE_URL=https://api.smtp.dev
   MAIL_TM_DOMAIN=your_domain.ggff.net
   DEFAULT_PASSWORD=secure_password
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 2. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动。

## API接口说明

### 创建或获取邮箱账户

**POST /api/email**

创建新邮箱账户或使用现有账户。

#### 请求方式1：创建随机新账户（向后兼容）
```bash
curl -X POST http://localhost:5000/api/email
```

#### 请求方式2：指定邮箱地址
```bash
curl -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d '{"email": "myuser@wdzzh.ggff.net"}'
```

#### 响应示例
```json
{
  "success": true,
  "email": "myuser@wdzzh.ggff.net",
  "message": "使用现有邮箱账户"
}
```

### 获取邮件内容

**GET /api/email/{email_address}**

获取指定邮箱的最新邮件内容，支持自动等待新邮件。

```bash
curl http://localhost:5000/api/email/user@wdzzh.ggff.net
```

#### 功能特点：
- 自动等待新邮件（最长60秒）
- 只返回未处理的新邮件
- 不会重复返回旧邮件
- 超时后返回404错误

#### 响应示例
```json
{
  "success": true,
  "email": "user@wdzzh.ggff.net",
  "content": "<html><body><h1>邮件内容</h1>...</body></html>"
}
```

## 使用示例

### 完整使用流程

```bash
# 1. 创建邮箱账户
EMAIL=$(curl -s -X POST http://localhost:5000/api/email | jq -r '.email')
echo "创建的邮箱: $EMAIL"

# 2. 向邮箱发送测试邮件（使用其他邮件客户端）

# 3. 获取邮件内容（自动等待新邮件）
curl "http://localhost:5000/api/email/$EMAIL"
```

### 指定邮箱使用流程

```bash
# 1. 使用指定邮箱
EMAIL="testuser@wdzzh.ggff.net"
curl -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\"}"

# 2. 获取邮件内容
curl "http://localhost:5000/api/email/$EMAIL"
```

## 测试脚本

项目包含多个测试脚本：

- `test_api.py` - 基本功能测试
- `test_existing_email.py` - 现有邮箱测试
- `test_new_email_wait.py` - 新邮件等待功能测试
- `test_wait_fix.py` - 邮件等待修复验证测试

运行测试：
```bash
python test_api.py
python test_existing_email.py
python test_new_email_wait.py
python test_wait_fix.py
```

## 注意事项

1. **API配额**：SMTP.dev API有请求频率限制，请注意使用频率
2. **邮件延迟**：邮件到达可能有几秒延迟，请使用等待功能
3. **域名限制**：只能使用配置的域名创建账户
4. **安全考虑**：API密钥应妥善保管，不要泄露