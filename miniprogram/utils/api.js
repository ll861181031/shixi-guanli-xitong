const app = getApp()

function request(url, method = 'GET', data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.baseURL + url,
      method: method,
      data: data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': app.globalData.token ? `Bearer ${app.globalData.token}` : ''
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          if (res.data && res.data.success !== false) {
            resolve(res.data)
          } else {
            wx.showToast({
              title: res.data?.message || '请求失败',
              icon: 'none'
            })
            reject(res.data)
          }
        } else if (res.statusCode === 401) {
          // token过期，清除登录信息
          app.globalData.token = ''
          app.globalData.user = null
          wx.removeStorageSync('token')
          wx.removeStorageSync('user')
          wx.showToast({
            title: '登录已过期',
            icon: 'none'
          })
          wx.reLaunch({
            url: '/pages/login/login'
          })
          reject(res)
        } else {
          wx.showToast({
            title: res.data?.message || '请求失败',
            icon: 'none'
          })
          reject(res)
        }
      },
      fail(err) {
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

module.exports = {
  get: (url, data) => request(url, 'GET', data),
  post: (url, data) => request(url, 'POST', data),
  put: (url, data) => request(url, 'PUT', data),
  delete: (url, data) => request(url, 'DELETE', data)
}

