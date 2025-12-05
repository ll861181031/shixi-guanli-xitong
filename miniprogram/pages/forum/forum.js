const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    categories: [],
    activeCategoryId: null,
    keyword: '',
    posts: [],
    page: 1,
    perPage: 20,
    hasMore: true,
    loading: false,
    refreshing: false,
    emptyText: '暂无帖子',
  },

  onLoad() {
    this.initPage()
  },

  async initPage() {
    await this.loadCategories()
    this.resetAndLoad()
  },

  onPullDownRefresh() {
    this.setData({ refreshing: true })
    this.resetAndLoad().finally(() => {
      wx.stopPullDownRefresh()
      this.setData({ refreshing: false })
    })
  },

  onReachBottom() {
    if (this.data.loading || !this.data.hasMore) return
    this.loadPosts(this.data.page + 1)
  },

  async loadCategories() {
    try {
      const res = await api.get('/forum/categories')
      const list = res?.data || res?.data?.data || []
      this.setData({
        categories: [{ id: null, name: '全部' }, ...list]
      })
    } catch (err) {
      console.error('加载分类失败', err)
      wx.showToast({ title: '分类加载失败', icon: 'none' })
    }
  },

  async resetAndLoad() {
    this.setData({ page: 1, hasMore: true, posts: [] })
    await this.loadPosts(1)
  },

  async loadPosts(page) {
    if (this.data.loading || !this.data.hasMore && page !== 1) return
    this.setData({ loading: true })
    try {
      const params = {
        page,
        per_page: this.data.perPage,
      }
      if (this.data.activeCategoryId) {
        params.category_id = this.data.activeCategoryId
      }
      if (this.data.keyword) {
        params.keyword = this.data.keyword.trim()
      }
      const res = await api.get('/forum/posts', params)
      const data = res?.data?.data || res?.data
      const items = data?.items || []
      const merged = page === 1 ? items : [...this.data.posts, ...items]
      this.setData({
        posts: merged,
        page,
        hasMore: merged.length < (data?.total || 0)
      })
    } catch (err) {
      console.error('加载帖子失败', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  onCategoryTap(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ activeCategoryId: id || null })
    this.resetAndLoad()
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  onSearchConfirm() {
    this.resetAndLoad()
  },

  goToPublish() {
    wx.navigateTo({ url: '/pages/forum-publish/forum-publish' })
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/forum-detail/forum-detail?id=${id}` })
  }
})

