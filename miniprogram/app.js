App({
  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      this.globalData.user = wx.getStorageSync('user')
    }
  },
  
  globalData: {
    token: '',
    user: null,
    baseURL: 'http://127.0.0.1:5000/api' // 开发环境，生产环境需要改为实际域名
  }
})

