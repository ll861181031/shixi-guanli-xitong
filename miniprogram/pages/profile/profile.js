const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    user: null
  },

  onLoad() {
    this.setData({ user: app.globalData.user })
  },

  onShow() {
    this.setData({ user: app.globalData.user })
  },

  navigateTo(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.navigateTo({ url })
    }
  },

  async logout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.globalData.token = ''
          app.globalData.user = null
          wx.removeStorageSync('token')
          wx.removeStorageSync('user')
          wx.reLaunch({
            url: '/pages/login/login'
          })
        }
      }
    })
  }
})

