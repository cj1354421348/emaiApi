# 临时邮箱API接口文档

## 概述

这是一个基于SMTP.dev服务的临时邮箱API，提供邮箱账户管理和邮件接收功能。

**基础URL**：`http://localhost:5000`

## 接口列表

### 1. 获取或创建邮箱账户
**方法**：`POST /api/email`

**描述**：获取指定邮箱账户或创建新账户。支持向后兼容的随机账户创建。

**请求头**：
```
Content-Type: application/json
```

**请求体**（JSON）：
```json
{
  "email": "user@wdzzh.ggff.net"  // 可选，如果不提供则创建随机账户
}
```

**调用示例**：

#### 方式1：创建随机新账户（向后兼容）
```bash
# 空请求体
curl -X POST http://localhost:5000/api/email

# 或空JSON
curl -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 方式2：指定邮箱地址
```bash
curl -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d '{"email": "myuser@wdzzh.ggff.net"}'
```

**响应示例**：

#### 创建随机新账户
```json
{
  "success": true,
  "email": "random_user123@wdzzh.ggff.net",
  "message": "创建随机新邮箱账户（向后兼容模式）"
}
```

#### 使用现有账户
```json
{
  "success": true,
  "email": "myuser@wdzzh.ggff.net",
  "message": "使用现有邮箱账户"
}
```

#### 创建指定新账户
```json
{
  "success": true,
  "email": "myuser@wdzzh.ggff.net",
  "message": "创建新邮箱账户"
}
```

#### 错误响应
```json
{
  "success": false,
  "error": "邮箱地址是必需的"
}
```

**状态码**：
- `200`：成功
- `400`：参数错误（缺少email字段）
- `500`：服务器内部错误

---

### 2. 获取指定邮箱的邮件内容
**方法**：`GET /api/email/{email_address}`

**描述**：获取指定邮箱的最新邮件内容，支持等待新邮件到达。

**路径参数**：
- `email_address`：完整的邮箱地址（如 `user@wdzzh.ggff.net`）

**调用示例**：
```bash
curl http://localhost:5000/api/email/user@wdzzh.ggff.net
```

**响应示例**：

#### 成功获取邮件
```json
{
  "success": true,
  "email": "user@wdzzh.ggff.net",
  "content": "<html><body><h1>邮件内容</h1>...</body></html>"
}
```

#### 未收到邮件
```json
{
  "success": false,
  "email": "user@wdzzh.ggff.net",
  "error": "未收到邮件或超时"
}
```

**状态码**：
- `200`：成功
- `404`：未收到邮件
- `500`：服务器内部错误

---

## 使用流程

### 基本使用流程
1. **创建/获取邮箱**：调用 `POST /api/email` 获取邮箱地址
2. **发送测试邮件**：向获取的邮箱地址发送邮件
3. **获取邮件内容**：调用 `GET /api/email/{email}` 获取邮件内容

### 示例完整流程
```bash
# 1. 创建邮箱账户
EMAIL=$(curl -s -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d '{}' | jq -r '.email')

echo "创建的邮箱: $EMAIL"

# 2. 向邮箱发送测试邮件（使用其他邮件客户端）

# 3. 获取邮件内容
curl "http://localhost:5000/api/email/$EMAIL"
```

### 指定邮箱流程
```bash
# 1. 指定邮箱地址创建/获取账户
EMAIL="testuser@wdzzh.ggff.net"
curl -X POST http://localhost:5000/api/email \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\"}"

# 2. 获取邮件内容
curl "http://localhost:5000/api/email/$EMAIL"
```

---

## 功能特性

### 向后兼容性
- 支持原来的空请求创建随机账户
- 支持新的指定邮箱地址功能
- 客户端代码无需修改即可继续工作

### 账户缓存
- 已创建的客户端实例会被缓存
- 重复请求同一邮箱会复用现有实例
- 提高性能，避免重复账户创建

### 邮件等待机制
- GET接口支持自动等待新邮件（60秒超时）
- 轮询检查新邮件到达
- 只返回未处理的新邮件，避免重复获取旧邮件
- 初始化时记录已有邮件ID，确保新邮件识别准确性

### 错误处理
- 参数验证和用户友好错误消息
- 网络错误和API错误处理
- 详细的错误日志记录

---

## 配置说明

### 环境变量（.env文件）
```
MAIL_TM_API_KEY=your_api_key_here
MAIL_TM_BASE_URL=https://api.smtp.dev
MAIL_TM_DOMAIN=wdzzh.ggff.net
DEFAULT_PASSWORD=thisispassword
```

### 自定义配置
- **API密钥**：`MAIL_TM_API_KEY` - SMTP.dev API密钥
- **基础URL**：`MAIL_TM_BASE_URL` - API服务器地址
- **域名**：`MAIL_TM_DOMAIN` - 使用的邮箱域名
- **默认密码**：`DEFAULT_PASSWORD` - 账户默认密码

---

## 测试建议

### 单元测试
1. 测试随机账户创建
2. 测试指定账户查找
3. 测试邮件内容获取
4. 测试等待新邮件功能

### 集成测试
1. 完整流程测试（创建→发送→获取）
2. 并发请求测试
3. 错误场景测试

### 性能测试
1. 高并发账户创建测试
2. 邮件轮询性能测试
3. 缓存机制有效性测试

---

## 注意事项

1. **API配额**：SMTP.dev API有请求频率限制，请注意使用频率
2. **账户生命周期**：临时账户可能有有效期限制
3. **邮件延迟**：邮件到达可能有几秒延迟，请使用等待功能
4. **域名限制**：只能使用配置的域名创建账户
5. **安全考虑**：API密钥应妥善保管，不要泄露

---

## 故障排除

### 常见错误

#### 400 - 参数错误
- **原因**：JSON请求缺少email字段
- **解决**：确保请求体包含有效的email字段

#### 404 - 未收到邮件
- **原因**：指定邮箱没有新邮件，或等待超时
- **解决**：确认已向邮箱发送邮件，或增加等待时间

#### 500 - 服务器错误
- **原因**：API调用失败或网络问题
- **解决**：检查API密钥、域名配置，查看服务器日志

#### 账户创建失败
- **原因**：邮箱地址已被占用或API配额超限
- **解决**：使用不同的邮箱地址，或联系服务提供商

---

## 版本信息

**当前版本**：v2.1
**更新内容**：
- 添加指定邮箱地址支持
- 向后兼容原有接口
- 模块化API客户端
- 增强错误处理和日志记录
- 修复邮件等待机制，确保只返回新邮件而非旧邮件

**兼容性**：完全向后兼容v1.0接口