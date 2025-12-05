const api = require('../../utils/api')
const app = getApp()

const MAX_IMAGES = 3
const MAX_IMAGE_SIZE = 5 * 1024 * 1024 // 5MB

Page({
  data: {
    categories: [],
    form: {
      title: '',
      content: '',
      category_id: null,
      images: []
    },
    categoryName: '',
    loading: false
  },

  onLoad() {
    this.loadCategories()
  },

  async loadCategories() {
    try {
      const res = await api.get('/forum/categories')
      const list = res?.data || res?.data?.data || []
      this.setData({
        categories: list
      })
    } catch (err) {
      wx.showToast({ title: '分类加载失败', icon: 'none' })
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onCategoryChange(e) {
    const idx = e.detail.value
    const category = this.data.categories[idx]
    if (category) {
      this.setData({ 'form.category_id': category.id, categoryName: category.name })
    }
  },

  async chooseImages() {
    try {
      const remain = MAX_IMAGES - this.data.form.images.length
      if (remain <= 0) {
        wx.showToast({ title: `最多${MAX_IMAGES}张`, icon: 'none' })
        return
      }
      const res = await wx.chooseImage({ count: remain })
      const files = res.tempFiles || []
      const overSize = files.find(f => f.size > MAX_IMAGE_SIZE)
      if (overSize) {
        wx.showToast({ title: '单张不超过5MB', icon: 'none' })
        return
      }
      this.setData({ 'form.images': [...this.data.form.images, ...files.map(f => f.path)] })
    } catch (err) {
      console.error('选择图片失败', err)
    }
  },

  removeImage(e) {
    const idx = e.currentTarget.dataset.idx
    const imgs = [...this.data.form.images]
    imgs.splice(idx, 1)
    this.setData({ 'form.images': imgs })
  },

  validateForm() {
    const { title, content, category_id } = this.data.form
    if (!title || title.length < 5 || title.length > 50) {
      wx.showToast({ title: '标题5-50字', icon: 'none' })
      return false
    }
    if (!content || content.length < 20) {
      wx.showToast({ title: '内容至少20字', icon: 'none' })
      return false
    }
    if (!category_id) {
      wx.showToast({ title: '请选择分类', icon: 'none' })
      return false
    }
    return true
  },

  async uploadImagesIfNeeded() {
    const uploaded = []
    for (const path of this.data.form.images) {
      try {
        const res = await new Promise((resolve, reject) => {
          wx.uploadFile({
            url: `${app.globalData.baseURL}/forum/upload`,
            filePath: path,
            name: 'file',
            header: {
              Authorization: app.globalData.token ? `Bearer ${app.globalData.token}` : ''
            },
            success: (resp) => {
              let data = resp.data
              try { data = typeof data === 'string' ? JSON.parse(data) : data } catch (e) {}
              if (resp.statusCode >= 200 && resp.statusCode < 300 && data?.success !== false) {
                resolve(data?.data?.path || data?.path)
              } else {
                reject(new Error(data?.message || '上传失败'))
              }
            },
            fail: reject
          })
        })
        if (res) uploaded.push(res)
      } catch (err) {
        wx.showToast({ title: err?.message || '上传失败，请重试', icon: 'none' })
        throw err
      }
    }
    return uploaded
  },

  async submit() {
    if (!this.validateForm()) return
    this.setData({ loading: true })
    try {
      const images = await this.uploadImagesIfNeeded()
      const payload = {
        title: this.data.form.title.trim(),
        content: this.data.form.content.trim(),
        category_id: this.data.form.category_id,
        images
      }
      const res = await api.post('/forum/posts', payload)
      wx.showToast({ title: '已提交审核', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1000)
    } catch (err) {
      console.error('发布失败', err)
      wx.showToast({ title: err?.message || '发布失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  }
})

