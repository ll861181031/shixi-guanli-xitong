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
    }
  },

  onLoad() {
    this.checkLogin()
  },

  onShow() {
    if (app.globalData.user) {
      this.setData({ user: app.globalData.user })
      this.loadStats()
    }
  },

  checkLogin() {
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      })
    } else {
      this.setData({ user: app.globalData.user })
      this.loadStats()
    }
  },

  async loadStats() {
    try {
      // 获取申请状态
      const appRes = await api.get('/applications', { per_page: 1 })
      if (appRes.success && appRes.data.items.length > 0) {
        this.setData({
          'stats.applicationStatus': appRes.data.items[0].status
        })
      }

      // 获取签到统计
      const checkinRes = await api.get('/checkins/statistics')
      if (checkinRes.success) {
        this.setData({
          'stats.checkinCount': checkinRes.data.data.total || 0
        })
      }

      // 获取周报数量
      const reportRes = await api.get('/weekly-reports', { per_page: 1 })
      if (reportRes.success) {
        this.setData({
          'stats.reportCount': reportRes.data.data.total || 0
        })
      }

      // 获取未读消息数
      const msgRes = await api.get('/users/messages', { is_read: false, per_page: 1 })
      if (msgRes.success) {
        this.setData({
          'stats.unreadMessages': msgRes.data.data.total || 0
        })
      }
    } catch (error) {
      console.error('加载统计失败:', error)
    }
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
  }
})

