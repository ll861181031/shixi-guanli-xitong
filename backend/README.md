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

错误时返回相应的HTTP状态码和错误信息。常见约定：

- 认证缺失/过期：401，`message: 登录已过期`，需携带 `Authorization: Bearer <token>`
- 权限不足：403，`message: 权限不足`，教师需具备具体模块权限（如 `positions`/`applications`/`reports`/`checkins`/`statistics`/`forum`）
- 校验错误：400，`error_code` 可能为 `INVALID_PARAM` / 业务自定义（如 `ALREADY_APPLIED`、`OUT_OF_RANGE` 等）
- 结构化错误：部分接口在 `data` 中附带细节（如距离超限 `data: { distance, allowed }`）

分页/过滤约定：
- 通用参数：`page`（默认1）、`per_page`（默认10或20），返回 `items/total/page/per_page/pages`
- 关键词：`keyword`（岗位/论坛支持标题/内容模糊）
- 时间范围：`start_time/end_time`（ISO，如 `2025-12-05T00:00:00`）
- 状态/分类过滤：如 `status`、`category_id`、岗位的 `location/min_salary/max_salary/internship_duration`

角色与权限：
- 角色：`student` / `teacher` / `admin`
- 学生：仅能操作个人相关（申请、签到、周报、论坛发帖/评论等）
- 教师：需在 `users.permissions` 中具备对应模块权限方可访问；无权限返回 403
- 管理员：可访问所有模块

论坛上传/限制：
- 图片上传：`POST /api/forum/upload`，仅 jpg/png，单张 ≤5MB
- 发帖：标题 5-50 字，内容 ≥20 字，最多 3 张图片，可选分类；默认状态 pending，需审核
- 评论：1-200 字，防敏感词（如开启 `FORUM_SENSITIVE_CHECK_ENABLED`）

