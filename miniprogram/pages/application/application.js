const api = require('../../utils/api')

Page({
  data: {
    positionId: null,
    position: null,
    motivation: '',
    resume: ''
  },

  onLoad(options) {
    if (options.position_id) {
      this.setData({ positionId: options.position_id })
      this.loadPosition(options.position_id)
    }
  },

  async loadPosition(id) {
    try {
      const result = await api.get(`/positions/${id}`)
      if (result.success) {
        this.setData({ position: result.data.data })
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
    }
  },

  onMotivationInput(e) {
    this.setData({ motivation: e.detail.value })
  },

  onResumeInput(e) {
    this.setData({ resume: e.detail.value })
  },

  async submit() {
    if (!this.data.motivation) {
      wx.showToast({
        title: '请输入申请动机',
        icon: 'none'
      })
      return
    }

    try {
      wx.showLoading({ title: '提交中...' })
      const result = await api.post('/applications', {
        position_id: this.data.positionId,
        motivation: this.data.motivation,
        resume: this.data.resume
      })
      wx.hideLoading()
      
      if (result.success) {
        wx.showToast({
          title: '申请成功',
          icon: 'success'
        })
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      }
    } catch (error) {
      wx.hideLoading()
      console.error('提交申请失败:', error)
    }
  }
})

