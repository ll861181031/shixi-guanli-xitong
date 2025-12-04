const api = require('../../utils/api')

Page({
  data: {
    position: null,
    weekNumber: 1,
    content: '',
    attachment: null
  },

  onLoad() {
    this.loadPosition()
  },

  async loadPosition() {
    try {
      const appRes = await api.get('/applications', { status: 'approved', per_page: 1 })
      if (appRes.success && appRes.data.items.length > 0) {
        const application = appRes.data.items[0]
        const posRes = await api.get(`/positions/${application.position_id}`)
        if (posRes.success) {
          this.setData({ position: posRes.data.data })
        }
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
    }
  },

  onWeekNumberInput(e) {
    this.setData({ weekNumber: parseInt(e.detail.value) || 1 })
  },

  onContentInput(e) {
    this.setData({ content: e.detail.value })
  },

  async uploadAttachment() {
    try {
      const res = await wx.chooseMessageFile({
        count: 1,
        type: 'file'
      })
      
      if (res.tempFiles && res.tempFiles.length > 0) {
        const file = res.tempFiles[0]
        wx.showLoading({ title: '上传中...' })
        
        // 这里需要实现文件上传
        // 由于小程序文件上传需要formData，这里简化处理
        wx.showToast({
          title: '文件上传功能需要后端支持',
          icon: 'none'
        })
        
        wx.hideLoading()
      }
    } catch (error) {
      console.error('选择文件失败:', error)
    }
  },

  async submitReport() {
    if (!this.data.content) {
      wx.showToast({
        title: '请输入周报内容',
        icon: 'none'
      })
      return
    }

    try {
      wx.showLoading({ title: '提交中...' })
      
      const result = await api.post('/weekly-reports', {
        position_id: this.data.position.id,
        week_number: this.data.weekNumber,
        content: this.data.content,
        attachment_path: this.data.attachment?.path,
        attachment_name: this.data.attachment?.name
      })
      
      wx.hideLoading()
      
      if (result.success) {
        wx.showToast({
          title: '提交成功',
          icon: 'success'
        })
        
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      }
    } catch (error) {
      wx.hideLoading()
      console.error('提交失败:', error)
    }
  }
})

