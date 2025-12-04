# 学生实习信息管理系统 - 后端

## 技术栈
- Flask 3.0
- SQLAlchemy
- MySQL
- PyJWT
- Flask-CORS

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

1. 创建 MySQL 数据库
2. 复制 `.env.example` 为 `.env` 并配置：
   - `SECRET_KEY`: Flask密钥
   - `JWT_SECRET_KEY`: JWT密钥
   - `DATABASE_URL`: 数据库连接字符串
   - `WX_APPID`: 微信小程序AppID
   - `WX_SECRET`: 微信小程序Secret

或直接修改 `config.py` 文件

## 初始化数据库

```bash
python run.py
flask init-db
```

默认管理员账户：`admin` / `admin123`

## 运行

```bash
python run.py
```

服务将在 http://127.0.0.1:5000 启动

## API 文档

所有API前缀为 `/api`

### 认证
- `POST /api/auth/login` - 管理员/教师登录
- `POST /api/auth/wx-login` - 微信小程序登录
- `POST /api/auth/bind-student-id` - 绑定学号
- `GET /api/auth/me` - 获取当前用户信息

### 岗位管理
- `GET /api/positions` - 获取岗位列表
- `GET /api/positions/:id` - 获取岗位详情
- `POST /api/positions` - 创建岗位（需要管理员/教师权限）
- `PUT /api/positions/:id` - 更新岗位（需要管理员/教师权限）
- `DELETE /api/positions/:id` - 删除岗位（需要管理员/教师权限）

### 申请管理
- `GET /api/applications` - 获取申请列表
- `GET /api/applications/:id` - 获取申请详情
- `POST /api/applications` - 提交申请（需要学生权限）
- `POST /api/applications/:id/review` - 审核申请（需要管理员/教师权限）

### 签到管理
- `GET /api/checkins` - 获取签到记录
- `POST /api/checkins` - 提交签到（需要学生权限）
- `GET /api/checkins/statistics` - 获取签到统计

### 周报管理
- `GET /api/weekly-reports` - 获取周报列表
- `GET /api/weekly-reports/:id` - 获取周报详情
- `POST /api/weekly-reports` - 提交周报（需要学生权限）
- `POST /api/weekly-reports/upload` - 上传附件
- `POST /api/weekly-reports/:id/review` - 批改周报（需要管理员/教师权限）

### 统计查询
- `GET /api/statistics/overview` - 概览统计（需要管理员/教师权限）
- `GET /api/statistics/attendance-rate` - 出勤率统计（需要管理员/教师权限）
- `GET /api/statistics/report-submission-rate` - 周报提交率统计（需要管理员/教师权限）
- `GET /api/statistics/position-distribution` - 岗位分布统计（需要管理员/教师权限）
- `GET /api/statistics/checkin-trend` - 签到趋势（需要管理员/教师权限）

### 用户管理
- `GET /api/users` - 获取用户列表（需要管理员/教师权限）
- `GET /api/users/messages` - 获取消息列表
- `POST /api/users/messages/:id/read` - 标记消息已读

## 认证

所有需要认证的API需要在请求头中添加：
```
Authorization: Bearer <token>
```

## 错误处理

所有API返回格式：
```json
{
  "success": true/false,
  "message": "消息",
  "data": {}
}
```

错误时返回相应的HTTP状态码和错误信息。

