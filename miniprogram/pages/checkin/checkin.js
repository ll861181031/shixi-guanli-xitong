const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    position: null,
    hasApproved: false,
    location: null,
    locationText: '',
    distance: 0,
    allowedRadius: 0,
    status: '',
    statusText: '',
    loading: false,
    loadingPosition: false,
    todayCheckin: null,
    todayStatusText: '今日未签到',
    todayTimeText: '',
    permissionDenied: false,
    errorMessage: '',
    emptyReason: '',
  },

  onLoad() {
    this.initPage()
  },

  onShow() {
    // 返回页面时刷新今日状态
    this.loadTodayStatus()
  },

  async initPage() {
    await this.loadPosition()
    await this.loadTodayStatus()
  },

  async loadPosition() {
    this.setData({ loadingPosition: true })
    try {
      // 拉取更多申请，前端挑选已通过的
      const appRes = await api.get('/applications', { per_page: 50 })
      const items = appRes?.data?.items || appRes?.data?.data?.items || []
      const approved = items.find(item => item.status === 'approved')
      if (!approved) {
        this.setData({
          hasApproved: false,
          emptyReason: '您还没有已通过的申请，暂不可签到'
        })
        return
      }
      const posRes = await api.get(`/positions/${approved.position_id}`)
      const pos = posRes?.data?.data || posRes?.data
      if (pos) {
        this.setData({
          position: pos,
          hasApproved: true,
          allowedRadius: pos.checkin_radius || 200
        })
      } else {
        this.setData({
          hasApproved: false,
          emptyReason: '加载岗位信息失败，请稍后重试'
        })
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
      this.setData({ emptyReason: '加载岗位信息失败，请稍后重试' })
    } finally {
      this.setData({ loadingPosition: false })
    }
  },

  async loadTodayStatus() {
    try {
      const today = new Date().toISOString().slice(0, 10)
      const res = await api.get('/checkins', { start_date: today, end_date: today, per_page: 1 })
      const items = res?.data?.items || []
      if (items.length > 0) {
        const record = items[0]
        const statusMap = {
          normal: '正常',
          abnormal: '异常',
          late: '迟到',
          not_signed: '未签'
        }
        this.setData({
          todayCheckin: record,
          todayStatusText: statusMap[record.status] || '已签到',
          todayTimeText: record.checkin_time ? record.checkin_time.slice(11, 19) : ''
        })
      } else {
        this.setData({
          todayCheckin: null,
          todayStatusText: '今日未签到',
          todayTimeText: ''
        })
      }
    } catch (err) {
      console.warn('加载今日签到状态失败', err)
    }
  },

  async getLocation() {
    if (!this.data.position) {
      this.setData({ emptyReason: '请先选择或通过岗位申请' })
      return
    }
    try {
      wx.showLoading({ title: '获取位置中...', mask: true })
      const res = await wx.getLocation({
        type: 'gcj02',
        isHighAccuracy: true,
        highAccuracyExpireTime: 8000
      })
      const lat = Number(res.latitude)
      const lng = Number(res.longitude)
      const latText = isNaN(lat) ? (res.latitude || '') : lat.toFixed(6)
      const lngText = isNaN(lng) ? (res.longitude || '') : lng.toFixed(6)
      this.setData({
        location: {
          latitude: lat,
          longitude: lng
        },
        locationText: `${latText}, ${lngText}`,
        permissionDenied: false
      })
      wx.hideLoading()
    } catch (error) {
      wx.hideLoading()
      this.setData({ permissionDenied: true })
        wx.showModal({
        title: '需要定位权限',
        content: '请允许获取位置信息以完成签到，可前往设置开启定位权限。',
        confirmText: '去设置',
        success: (res) => {
          if (res.confirm) {
            wx.openSetting()
          }
        }
      })
    }
  },

  async submitCheckin() {
    if (!this.data.position) {
      wx.showToast({ title: '未绑定岗位', icon: 'none' })
      return
    }
    if (!this.data.location) {
      wx.showToast({
        title: '请先获取当前位置',
        icon: 'none'
      })
      return
    }
    try {
      wx.showLoading({ title: '签到中...', mask: true })
      const result = await api.post('/checkins', {
        position_id: this.data.position.id,
        latitude: this.data.location.latitude,
        longitude: this.data.location.longitude
      })
      wx.hideLoading()
      // 成功或迟到/异常已在后端区分，这里以 success 为准
      wx.showModal({
          title: '签到成功',
        content: result.message || '已记录签到',
        confirmText: '查看记录',
        cancelText: '关闭',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/checkin-history/checkin-history' })
          }
      }
      })
      this.loadTodayStatus()
    } catch (error) {
      wx.hideLoading()
      const errCode = error?.error_code || error?.code
      // 结构化错误优先
      if (errCode === 'OUT_OF_RANGE') {
        const data = error?.data || {}
        wx.showModal({
          title: '超出签到范围',
          content: `当前距离 ${data.distance || ''} 米，允许 ${data.allowed || ''} 米内，请到达指定范围后重试`,
          showCancel: false
        })
      } else if (errCode === 'ALREADY_CHECKED_IN') {
        wx.showModal({
          title: '今日已签到',
          content: '今日只能签到一次',
          confirmText: '查看记录',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/checkin-history/checkin-history' })
            }
          }
        })
      } else if (errCode === 'NOT_IN_CHECKIN_WINDOW') {
        wx.showModal({
          title: '当前非签到时段',
          content: '请在规定时间内完成签到',
          showCancel: false
        })
      } else {
        wx.showToast({
          title: error?.message || '签到失败，请稍后再试',
          icon: 'none'
        })
      }
    }
  },

  goToPositions() {
    wx.navigateTo({ url: '/pages/positions/positions' })
  },

  goToHistory() {
    wx.navigateTo({ url: '/pages/checkin-history/checkin-history' })
  },

  retryLoad() {
    this.initPage()
  }
})

