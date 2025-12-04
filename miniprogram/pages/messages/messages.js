const api = require('../../utils/api')

Page({
  data: {
    messages: []
  },

  onLoad() {
    this.loadMessages()
  },

  onPullDownRefresh() {
    this.loadMessages()
    wx.stopPullDownRefresh()
  },

  async loadMessages() {
    try {
      const result = await api.get('/users/messages', { per_page: 50 })
      if (result.success) {
        this.setData({
          messages: result.data.items
        })
      }
    } catch (error) {
      console.error('加载消息失败:', error)
    }
  },

  async markRead(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.post(`/users/messages/${id}/read`)
      // 更新本地状态
      const messages = this.data.messages.map(msg => {
        if (msg.id === id) {
          msg.is_read = true
        }
        return msg
      })
      this.setData({ messages })
    } catch (error) {
      console.error('标记已读失败:', error)
    }
  }
})

