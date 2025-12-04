# 学生实习信息管理系统 - 微信小程序

## 功能

- 微信登录和学号绑定
- 查看实习岗位
- 提交实习申请
- 基于地理围栏的签到
- 提交周报（含附件）
- 查看批改意见
- 接收消息提醒

## 配置

1. 使用微信开发者工具打开项目
2. 修改 `app.js` 中的 `baseURL` 为实际后端地址
3. 在微信公众平台配置服务器域名
4. 配置小程序 AppID

## 页面说明

- `pages/login/login` - 登录页面
- `pages/index/index` - 首页
- `pages/positions/positions` - 岗位列表
- `pages/position-detail/position-detail` - 岗位详情
- `pages/application/application` - 提交申请
- `pages/my-applications/my-applications` - 我的申请
- `pages/checkin/checkin` - 签到
- `pages/checkin-history/checkin-history` - 签到记录
- `pages/weekly-report/weekly-report` - 提交周报
- `pages/my-reports/my-reports` - 我的周报
- `pages/report-detail/report-detail` - 周报详情
- `pages/messages/messages` - 消息列表
- `pages/profile/profile` - 个人中心

## 权限配置

小程序需要申请以下权限：
- 位置信息（用于签到功能）
- 文件上传（用于周报附件）

## 注意事项

1. 生产环境需要配置合法域名
2. 需要在小程序后台配置服务器域名白名单
3. 文件上传功能需要后端支持

