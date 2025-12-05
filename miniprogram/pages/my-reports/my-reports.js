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
      const items = result?.data?.items || result?.data?.data?.items || []
      this.setData({ reports: items })
    } catch (error) {
      console.error('加载周报列表失败:', error)
      wx.showToast({ title: '加载周报失败', icon: 'none' })
    }
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/report-detail/report-detail?id=${id}`
    })
  }
})

