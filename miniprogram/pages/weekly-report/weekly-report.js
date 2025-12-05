const api = require('../../utils/api')
const app = getApp()

const MAX_FILE_SIZE = 16 * 1024 * 1024 // 16MB，与后端配置保持一致

Page({
  data: {
    position: null,
    weekNumber: 1,
    content: '',
    attachment: null,
    reportId: null
  },

  onLoad(options = {}) {
    if (options.id) {
      const parsedId = parseInt(options.id, 10)
      this.setData({ reportId: Number.isNaN(parsedId) ? null : parsedId })
    }
    this.loadPosition()
  },

  async loadPosition() {
    try {
      const appRes = await api.get('/applications', { status: 'approved', per_page: 1 })
      if (appRes.success && appRes.data.items.length > 0) {
        const application = appRes.data.items[0]
        const posRes = await api.get(`/positions/${application.position_id}`)
        if (posRes.success) {
          this.setData({ position: posRes.data.data })
        }
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
    }
  },

  onWeekNumberInput(e) {
    this.setData({ weekNumber: parseInt(e.detail.value) || 1 })
  },

  onContentInput(e) {
    this.setData({ content: e.detail.value })
  },

  extractFileName(path) {
    if (!path) {
      return `attachment_${Date.now()}`
    }
    const parts = path.split(/[/\\]/)
    const filename = parts[parts.length - 1]
    return filename || `attachment_${Date.now()}`
  },

  normalizeFileMeta(file) {
    if (!file) return null
    return {
      ...file,
      name: file.name || this.extractFileName(file.path)
    }
  },

  isUserCancel(error) {
    return Boolean(error?.errMsg && error.errMsg.includes('cancel'))
  },

  async selectAttachmentFile() {
    try {
      const fileResult = await wx.chooseMessageFile({
        count: 1,
        type: 'all'
      })
      return this.normalizeFileMeta(fileResult.tempFiles?.[0])
    } catch (error) {
      if (this.isUserCancel(error)) {
        return null
      }
      // 兼容低版本或运行环境不支持 chooseMessageFile 时，回退到 chooseImage
      try {
        const imageResult = await wx.chooseImage({ count: 1 })
        if (imageResult.tempFiles?.length) {
          return this.normalizeFileMeta(imageResult.tempFiles[0])
        }
        if (imageResult.tempFilePaths?.length) {
          return this.normalizeFileMeta({
            path: imageResult.tempFilePaths[0],
            size: 0
          })
        }
        return null
      } catch (imageError) {
        if (this.isUserCancel(imageError)) {
          return null
        }
        throw imageError
      }
    }
  },

  uploadFileToServer(file) {
    const token = app.globalData.token
    if (!token) {
      return Promise.reject(new Error('请先登录后再上传附件'))
    }

    return new Promise((resolve, reject) => {
      wx.uploadFile({
        url: `${app.globalData.baseURL}/weekly-reports/upload`,
        filePath: file.path,
        name: 'file',
        header: {
          Authorization: `Bearer ${token}`
        },
        formData: {
          token,
          report_id: this.data.reportId || '',
          original_name: file.name || ''
        },
        success: (res) => {
          let payload = res.data
          try {
            payload = typeof payload === 'string' ? JSON.parse(payload) : payload
          } catch (parseError) {
            reject(new Error('上传响应解析失败'))
            return
          }
          resolve({
            statusCode: res.statusCode,
            data: payload
          })
        },
        fail: reject
      })
    })
  },

  async uploadAttachment() {
    if (!app.globalData.token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return
    }

    try {
      const file = await this.selectAttachmentFile()
      if (!file) {
        return
      }
      let fileSize = file.size
      if (typeof fileSize !== 'number' || fileSize === 0) {
        try {
          const fileInfo = await wx.getFileInfo({ filePath: file.path })
          fileSize = fileInfo.size
        } catch (infoError) {
          fileSize = 0
          console.warn('获取文件大小失败:', infoError)
        }
      }

      if (fileSize && fileSize > MAX_FILE_SIZE) {
        wx.showToast({
          title: '文件大于16MB',
          icon: 'none'
        })
        return
      }

      wx.showLoading({ title: '上传中...', mask: true })
      const response = await this.uploadFileToServer(file)
      wx.hideLoading()

      if (response.statusCode === 200 && response.data?.success) {
        const attachmentData = response.data.data || {}
        this.setData({
          attachment: {
            path: attachmentData.attachment_path,
            name: attachmentData.attachment_name || file.name,
            size: fileSize
          }
        })
        wx.showToast({
          title: '上传成功',
          icon: 'success'
        })
      } else {
        wx.showToast({
          title: response.data?.message || '上传失败',
          icon: 'none'
        })
      }
    } catch (error) {
      wx.hideLoading()
      console.error('上传附件失败:', error)
      const message = error?.message || '上传失败'
      wx.showToast({
        title: message,
        icon: 'none'
      })
    }
  },

  async submitReport() {
    if (!this.data.position) {
      wx.showToast({
        title: '岗位信息加载中，请稍后再试',
        icon: 'none'
      })
      return
    }

    if (!this.data.content) {
      wx.showToast({
        title: '请输入周报内容',
        icon: 'none'
      })
      return
    }

    try {
      wx.showLoading({ title: '提交中...' })
      
      const result = await api.post('/weekly-reports', {
        position_id: this.data.position.id,
        week_number: this.data.weekNumber,
        content: this.data.content,
        attachment_path: this.data.attachment?.path,
        attachment_name: this.data.attachment?.name
      })
      
      wx.hideLoading()
      
      if (result.success) {
        wx.showToast({
          title: '提交成功',
          icon: 'success'
        })
        
        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      }
    } catch (error) {
      wx.hideLoading()
      console.error('提交失败:', error)
    }
  }
})

