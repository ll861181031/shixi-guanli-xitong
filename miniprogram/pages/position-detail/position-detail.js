const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    position: null,
    hasApplied: false
  },

  onLoad(options) {
    if (options.id) {
      this.loadPosition(options.id)
      this.checkApplication(options.id)
    }
  },

  async loadPosition(id) {
    try {
      const result = await api.get(`/positions/${id}`)
      if (result.success) {
        this.setData({ position: result.data.data })
      }
    } catch (error) {
      console.error('加载岗位详情失败:', error)
    }
  },

  async checkApplication(positionId) {
    try {
      const result = await api.get('/applications', { position_id: positionId })
      if (result.success && result.data.items.length > 0) {
        this.setData({ hasApplied: true })
      }
    } catch (error) {
      console.error('检查申请状态失败:', error)
    }
  },

  async apply() {
    if (!app.globalData.user.student_id) {
      wx.showModal({
        title: '提示',
        content: '请先绑定学号',
        showCancel: false,
        success: () => {
          wx.navigateTo({
            url: '/pages/profile/profile'
          })
        }
      })
      return
    }

    try {
      wx.showLoading({ title: '提交中...' })
      const result = await api.post('/applications', {
        position_id: this.data.position.id,
        motivation: '希望获得实习机会'
      })
      wx.hideLoading()
      
      if (result.success) {
        wx.showToast({
          title: '申请成功',
          icon: 'success'
        })
        this.setData({ hasApplied: true })
      }
    } catch (error) {
      wx.hideLoading()
      console.error('申请失败:', error)
    }
  }
})

