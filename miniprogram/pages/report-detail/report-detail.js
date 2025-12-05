const api = require('../../utils/api')

Page({
  data: {
    report: null,
    loading: false
  },

  onLoad(options) {
    if (options.id) {
      this.loadReport(options.id)
    }
  },

  async loadReport(id) {
    try {
      this.setData({ loading: true })
      const result = await api.get(`/weekly-reports/${id}`)
      const data = result?.data?.data || result?.data
      if (data) {
        this.setData({ report: data })
      } else {
        wx.showToast({ title: '未获取到周报详情', icon: 'none' })
      }
    } catch (error) {
      console.error('加载周报详情失败:', error)
      wx.showToast({ title: '加载周报详情失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async openAttachment() {
    if (!this.data.report?.attachment_path) {
      wx.showToast({ title: '暂无附件', icon: 'none' })
      return
    }
    try {
      wx.showLoading({ title: '下载中...', mask: true })
      const downloadRes = await wx.downloadFile({
        url: `${getApp().globalData.baseURL.replace(/\/$/, '')}/${this.data.report.attachment_path}`
      })
      if (downloadRes.statusCode === 200) {
        wx.openDocument({
          filePath: downloadRes.tempFilePath,
          showMenu: true
        })
      } else {
        wx.showToast({ title: '下载附件失败', icon: 'none' })
      }
    } catch (err) {
      console.error('打开附件失败', err)
      wx.showToast({ title: '打开附件失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  }
})

