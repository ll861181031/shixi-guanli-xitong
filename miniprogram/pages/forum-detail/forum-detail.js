const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    postId: null,
    post: null,
    comments: [],
    commentInput: '',
    page: 1,
    perPage: 20,
    hasMore: true,
    loading: false,
    loadingComments: false
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ postId: options.id })
      this.loadPost()
      this.loadComments(1)
    }
  },

  async loadPost() {
    try {
      const res = await api.get(`/forum/posts/${this.data.postId}`)
      const data = res?.data?.data || res?.data
      let images = []
      try {
        images = data?.images ? JSON.parse(data.images) : []
      } catch (e) {
        images = []
      }
      this.setData({ post: { ...data, images } })
    } catch (err) {
      console.error('加载帖子失败', err)
      wx.showToast({ title: '加载帖子失败', icon: 'none' })
    }
  },

  async loadComments(page) {
    if (this.data.loadingComments || (!this.data.hasMore && page !== 1)) return
    this.setData({ loadingComments: true })
    try {
      const res = await api.get(`/forum/posts/${this.data.postId}/comments`, {
        page,
        per_page: this.data.perPage
      })
      const data = res?.data?.data || res?.data
      const items = data?.items || []
      const merged = page === 1 ? items : [...this.data.comments, ...items]
      this.setData({
        comments: merged,
        page,
        hasMore: merged.length < (data?.total || 0)
      })
    } catch (err) {
      console.error('加载评论失败', err)
    } finally {
      this.setData({ loadingComments: false })
    }
  },

  onReachBottom() {
    if (this.data.hasMore) {
      this.loadComments(this.data.page + 1)
    }
  },

  previewImage(e) {
    const current = e.currentTarget.dataset.src
    wx.previewImage({
      current,
      urls: this.data.post?.images || []
    })
  },

  async submitComment() {
    const content = (this.data.commentInput || '').trim()
    if (!content || content.length > 200) {
      wx.showToast({ title: '评论1-200字', icon: 'none' })
      return
    }
    try {
      wx.showLoading({ title: '提交中...', mask: true })
      const res = await api.post(`/forum/posts/${this.data.postId}/comments`, { content })
      wx.hideLoading()
      wx.showToast({ title: '已提交', icon: 'success' })
      this.setData({ commentInput: '', comments: [], page: 1, hasMore: true })
      this.loadComments(1)
      // 更新评论计数
      this.loadPost()
    } catch (err) {
      wx.hideLoading()
      console.error('评论失败', err)
      wx.showToast({ title: err?.message || '评论失败', icon: 'none' })
    }
  },

  onCommentInput(e) {
    this.setData({ commentInput: e.detail.value })
  },

  async likePost() {
    try {
      const res = await api.post(`/forum/posts/${this.data.postId}/like`)
      const likeCount = res?.data?.data?.like_count
      this.setData({ 'post.like_count': likeCount })
    } catch (err) {
      wx.showToast({ title: err?.message || '点赞失败', icon: 'none' })
    }
  }
})

