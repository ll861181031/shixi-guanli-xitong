const api = require('../../utils/api')

Page({
  data: {
    report: null
  },

  onLoad(options) {
    if (options.id) {
      this.loadReport(options.id)
    }
  },

  async loadReport(id) {
    try {
      const result = await api.get(`/weekly-reports/${id}`)
      if (result.success) {
        this.setData({
          report: result.data.data
        })
      }
    } catch (error) {
      console.error('加载周报详情失败:', error)
    }
  }
})

