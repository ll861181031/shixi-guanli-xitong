const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    user: null,
    stats: {
      applicationStatus: '',
      checkinCount: 0,
      reportCount: 0,
      unreadMessages: 0
    },
    applicationStatusText: '未申请',
    applicationStatusType: 'default',
    applicationStatusDesc: '尚未提交申请'
  },

  onLoad() {
    this.setData({ user: app.globalData.user })
    this.loadStats()
  },

  onShow() {
    this.setData({ user: app.globalData.user })
    this.loadStats()
  },

  navigateTo(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      if (url.startsWith('/pages/')) {
        wx.navigateTo({ url })
      } else {
        wx.switchTab({ url })
      }
    }
  },

  async loadStats() {
    try {
      // 申请状态
      const appRes = await api.get('/applications', { per_page: 20 })
      const appItems = appRes?.data?.items || []
      // 优先展示已通过，其次最新一条
      const approved = appItems.find(item => item.status === 'approved')
      const status = approved?.status || appItems[0]?.status || ''
      let statusText = '未申请'
      let statusType = 'default'
      let statusDesc = '尚未提交申请'
      if (status === 'approved') {
        statusText = '已通过'
        statusType = 'success'
        statusDesc = '请留意岗位通知'
      } else if (status === 'pending') {
        statusText = '待审核'
        statusType = 'warning'
        statusDesc = '教师审核中'
      } else if (status === 'rejected') {
        statusText = '已拒绝'
        statusType = 'danger'
        statusDesc = '可重新选择岗位'
      }
      this.setData({
        'stats.applicationStatus': status,
        applicationStatusText: statusText,
        applicationStatusType: statusType,
        applicationStatusDesc: statusDesc
      })

      // 签到统计
      const checkinRes = await api.get('/checkins/statistics')
      if (checkinRes.success) {
        this.setData({
          'stats.checkinCount': checkinRes.data?.total || 0
        })
      }

      // 周报数量
      const reportRes = await api.get('/weekly-reports', { per_page: 1 })
      if (reportRes.success) {
        this.setData({
          'stats.reportCount': reportRes.data?.total || 0
        })
      }

      // 未读消息数
      const msgRes = await api.get('/users/messages', { is_read: false, per_page: 1 })
      if (msgRes.success) {
        this.setData({
          'stats.unreadMessages': msgRes.data?.total || 0
        })
      }
    } catch (error) {
      console.error('加载统计失败:', error)
    }
  },

  async logout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.globalData.token = ''
          app.globalData.user = null
          wx.removeStorageSync('token')
          wx.removeStorageSync('user')
          wx.reLaunch({
            url: '/pages/login/login'
          })
        }
      }
    })
  }
})

