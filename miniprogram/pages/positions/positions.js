const api = require('../../utils/api')

Page({
  data: {
    positions: [],
    loading: false,
    keyword: ''
  },

  onLoad() {
    this.loadPositions()
  },

  onPullDownRefresh() {
    this.loadPositions()
    wx.stopPullDownRefresh()
  },

  async loadPositions() {
    this.setData({ loading: true })
    try {
      const result = await api.get('/positions', {
        per_page: 20
      })
      if (result.success) {
        this.setData({
          positions: result.data.items
        })
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
    } finally {
      this.setData({ loading: false })
    }
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  async onSearch() {
    this.setData({ loading: true })
    try {
      const result = await api.get('/positions', {
        keyword: this.data.keyword,
        per_page: 20
      })
      if (result.success) {
        this.setData({
          positions: result.data.items
        })
      }
    } catch (error) {
      console.error('搜索失败:', error)
    } finally {
      this.setData({ loading: false })
    }
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/position-detail/position-detail?id=${id}`
    })
  }
})

