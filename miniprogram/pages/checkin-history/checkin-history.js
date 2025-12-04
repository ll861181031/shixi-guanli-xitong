const api = require('../../utils/api')

Page({
  data: {
    checkins: []
  },

  onLoad() {
    this.loadCheckins()
  },

  onPullDownRefresh() {
    this.loadCheckins()
    wx.stopPullDownRefresh()
  },

  async loadCheckins() {
    try {
      const result = await api.get('/checkins', { per_page: 50 })
      if (result.success) {
        this.setData({
          checkins: result.data.items
        })
      }
    } catch (error) {
      console.error('加载签到记录失败:', error)
    }
  }
})

