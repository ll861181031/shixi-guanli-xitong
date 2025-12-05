const api = require('../../utils/api')
const app = getApp()

const STATUS_TEXT = {
  0: '招满',
  1: '在招',
  2: '暂停'
}

function formatSalaryText(position) {
  if (position.salary_range_text) {
    return position.salary_range_text
  }
  const min = position.min_salary
  const max = position.max_salary
  if (typeof min === 'number' && typeof max === 'number') {
    return `${min}-${max}元/月`
  }
  if (typeof min === 'number') {
    return `≥${min}元/月`
  }
  if (typeof max === 'number') {
    return `≤${max}元/月`
  }
  return '面议'
}

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
        const position = result.data.data
        position.salaryText = formatSalaryText(position)
        position.durationText = position.internship_duration || '未指定'
        position.statusText = STATUS_TEXT[position.status] || '未知状态'
        position.canApply = position.status === 1
        this.setData({ position })
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
    if (!this.data.position?.canApply) {
      wx.showToast({
        title: '该岗位暂不可申请',
        icon: 'none'
      })
      return
    }

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

