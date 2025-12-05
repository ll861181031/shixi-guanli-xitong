const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    username: '',
    password: ''
  },

  onLoad(options) {
    // 检查是否已登录
    if (app.globalData.token) {
      wx.switchTab({
        url: '/pages/forum/forum'
      })
    }
  },

  // 用户名密码登录
  async handleLogin() {
    try {
      if (!this.data.username || !this.data.password) {
        wx.showToast({
          title: '请输入用户名和密码',
          icon: 'none'
        })
        return
      }

      wx.showLoading({ title: '登录中...' })
      const result = await api.post('/auth/student-login', {
        username: this.data.username,
        password: this.data.password
      })

      wx.hideLoading()

      if (result.success) {
        app.globalData.token = result.data.token
        app.globalData.user = result.data.user
        wx.setStorageSync('token', result.data.token)
        wx.setStorageSync('user', result.data.user)

        wx.showToast({
          title: '登录成功',
          icon: 'success'
        })

        setTimeout(() => {
          wx.switchTab({
            url: '/pages/forum/forum'
          })
        }, 300)
      }
    } catch (error) {
      wx.hideLoading()
      console.error('登录失败:', error)
    }
  },
  onUsernameInput(e) {
    this.setData({ username: e.detail.value })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  }
})

