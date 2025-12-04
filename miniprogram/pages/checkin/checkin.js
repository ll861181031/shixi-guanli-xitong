const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    position: null,
    location: null,
    distance: 0,
    status: ''
  },

  onLoad() {
    this.loadPosition()
  },

  async loadPosition() {
    try {
      // 获取已批准的申请
      const appRes = await api.get('/applications', { status: 'approved', per_page: 1 })
      if (appRes.success && appRes.data.items.length > 0) {
        const application = appRes.data.items[0]
        const posRes = await api.get(`/positions/${application.position_id}`)
        if (posRes.success) {
          this.setData({ position: posRes.data.data })
        }
      } else {
        wx.showToast({
          title: '您还没有已通过的申请',
          icon: 'none'
        })
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
    }
  },

  async getLocation() {
    try {
      wx.showLoading({ title: '获取位置中...' })
      
      const res = await wx.getLocation({
        type: 'gcj02'
      })
      
      this.setData({
        location: {
          latitude: res.latitude,
          longitude: res.longitude
        }
      })
      
      // 计算距离
      if (this.data.position) {
        const distance = this.calculateDistance(
          res.latitude,
          res.longitude,
          this.data.position.latitude,
          this.data.position.longitude
        )
        
        let status = 'normal'
        if (distance > 500) {
          status = 'abnormal'
        } else if (distance > 200) {
          status = 'warning'
        }
        
        this.setData({
          distance: distance,
          status: status
        })
      }
      
      wx.hideLoading()
    } catch (error) {
      wx.hideLoading()
      if (error.errMsg.includes('auth deny')) {
        wx.showModal({
          title: '提示',
          content: '需要授权位置信息才能签到',
          showCancel: false
        })
      }
    }
  },

  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000 // 地球半径（米）
    const dLat = (lat2 - lat1) * Math.PI / 180
    const dLon = (lon2 - lon1) * Math.PI / 180
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    return Math.round(R * c)
  },

  async submitCheckin() {
    if (!this.data.location) {
      wx.showToast({
        title: '请先获取位置',
        icon: 'none'
      })
      return
    }

    try {
      wx.showLoading({ title: '签到中...' })
      
      const result = await api.post('/checkins', {
        position_id: this.data.position.id,
        latitude: this.data.location.latitude,
        longitude: this.data.location.longitude
      })
      
      wx.hideLoading()
      
      if (result.success) {
        wx.showToast({
          title: '签到成功',
          icon: 'success'
        })
        
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      }
    } catch (error) {
      wx.hideLoading()
      console.error('签到失败:', error)
    }
  }
})

