const api = require('../../utils/api')

Page({
  data: {
    reports: []
  },

  onLoad() {
    this.loadReports()
  },

  onPullDownRefresh() {
    this.loadReports()
    wx.stopPullDownRefresh()
  },

  async loadReports() {
    try {
      const result = await api.get('/weekly-reports')
      if (result.success) {
        this.setData({
          reports: result.data.items
        })
      }
    } catch (error) {
      console.error('加载周报列表失败:', error)
    }
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/report-detail/report-detail?id=${id}`
    })
  }
})

