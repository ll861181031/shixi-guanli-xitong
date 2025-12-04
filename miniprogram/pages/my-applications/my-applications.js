const api = require('../../utils/api')

Page({
  data: {
    applications: []
  },

  onLoad() {
    this.loadApplications()
  },

  onPullDownRefresh() {
    this.loadApplications()
    wx.stopPullDownRefresh()
  },

  async loadApplications() {
    try {
      const result = await api.get('/applications')
      if (result.success) {
        this.setData({
          applications: result.data.items
        })
      }
    } catch (error) {
      console.error('加载申请列表失败:', error)
    }
  },

  getStatusText(status) {
    const map = {
      pending: '待审核',
      approved: '已通过',
      rejected: '已拒绝'
    }
    return map[status] || status
  },

  getStatusColor(status) {
    const map = {
      pending: '#e6a23c',
      approved: '#67c23a',
      rejected: '#f56c6c'
    }
    return map[status] || '#999'
  }
})

