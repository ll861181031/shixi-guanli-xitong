const api = require('../../utils/api')
const app = getApp()

const SALARY_MIN = 0
const SALARY_MAX = 20000
const SALARY_STEP = 500

const DURATION_OPTIONS = [
  { label: '不限', value: '' },
  { label: '1个月以内', value: '1个月以内' },
  { label: '1-3个月', value: '1-3个月' },
  { label: '3-6个月', value: '3-6个月' },
  { label: '6个月以上', value: '6个月以上' }
]

const STATUS_OPTIONS = [
  { label: '全部', value: '' },
  { label: '在招', value: '1' },
  { label: '招满', value: '0' },
  { label: '暂停', value: '2' }
]

const STATUS_TEXT = {
  0: '招满',
  1: '在招',
  2: '暂停'
}

function formatSalaryText(position) {
  const min = position.min_salary
  const max = position.max_salary
  if (typeof min === 'number' && typeof max === 'number') {
    return `${min}-${max}元/月`
  }
  if (typeof min === 'number') {
    return `≥${min}元/月`
  }
  if (typeof max === 'number') {
    return `≤${max}元/月`
  }
  return '面议'
}

function decoratePosition(item) {
  return {
    ...item,
    salaryText: item.salary_range_text || formatSalaryText(item),
    durationText: item.internship_duration || '未指定',
    statusText: STATUS_TEXT[item.status] || '未知状态'
  }
}

Page({
  data: {
    positions: [],
    loading: false,
    loadingMore: false,
    keyword: '',
    locationOptions: ['全部'],
    selectedLocationIndex: 0,
    filters: {
      location: '',
      minSalary: SALARY_MIN,
      maxSalary: SALARY_MAX,
      internshipDuration: '',
      status: ''
    },
    salaryConfig: {
      min: SALARY_MIN,
      max: SALARY_MAX,
      step: SALARY_STEP
    },
    durationOptions: DURATION_OPTIONS,
    statusOptions: STATUS_OPTIONS,
    page: 1,
    perPage: 10,
    hasMore: true,
    totalCount: 0,
    appliedPositionIds: []
  },

  onLoad() {
    this.loadLocations()
    this.loadAppliedPositions().then(() => {
      this.loadPositions(true)
    })
  },

  async loadAppliedPositions() {
    if (!app.globalData.token) {
      this.setData({ appliedPositionIds: [] })
      return
    }
    try {
      // 拉取当前用户的全部申请（学生端已做鉴权，只返回自己的）
      const res = await api.get('/applications', { per_page: 200 })
      if (res.success) {
        const items = res.data?.data?.items || res.data?.items || []
        const ids = items.map(i => i.position_id)
        this.setData({ appliedPositionIds: ids })
      }
    } catch (error) {
      console.warn('加载已申请岗位失败:', error)
      this.setData({ appliedPositionIds: [] })
    }
  },

  async loadLocations() {
    try {
      const result = await api.get('/positions/locations')
      if (result.success) {
        const serverLocations = Array.isArray(result.data) ? result.data : []
        const options = ['全部', ...serverLocations]
        const currentLocation = this.data.filters.location
        const index = options.indexOf(currentLocation)
        this.setData({
          locationOptions: options,
          selectedLocationIndex: index >= 0 ? index : 0
        })
      }
    } catch (error) {
      console.error('加载地点失败:', error)
    }
  },

  onPullDownRefresh() {
    this.loadPositions(true).finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  buildQueryParams() {
    const params = { per_page: 20 }
    const keyword = (this.data.keyword || '').trim()
    if (keyword) {
      params.keyword = keyword
    }

    const { filters, salaryConfig } = this.data
    if (filters.location) {
      params.location = filters.location
    }
    if (filters.internshipDuration) {
      params.internship_duration = filters.internshipDuration
    }
    if (filters.status !== '') {
      params.status = Number(filters.status)
    }
    if (filters.minSalary > salaryConfig.min) {
      params.min_salary = filters.minSalary
    }
    if (filters.maxSalary < salaryConfig.max) {
      params.max_salary = filters.maxSalary
    }
    return params
  },

  async loadPositions(reset = false) {
    if (this.data.loading || this.data.loadingMore) {
      return
    }

    const nextPage = reset ? 1 : this.data.page
    this.setData({
      loading: reset,
      loadingMore: !reset
    })

    try {
      const params = this.buildQueryParams()
      params.page = nextPage
      params.per_page = this.data.perPage
      const result = await api.get('/positions', params)
      if (result.success) {
        const payload = result.data || {}
        const items = Array.isArray(payload.items) ? payload.items : []
        const list = items.map(decoratePosition)
        const withApplied = list.map(p => ({
          ...p,
          applied: this.data.appliedPositionIds.includes(p.id)
        }))
        const merged = reset ? list : this.data.positions.concat(list)
        const total = typeof payload.total === 'number' ? payload.total : merged.length
        const totalPages = payload.pages || Math.ceil(total / this.data.perPage) || 1
        const nextHasMore = nextPage < totalPages
        this.setData({
          positions: reset ? withApplied : this.data.positions.concat(withApplied),
          page: nextPage + 1,
          hasMore: nextHasMore,
          totalCount: total
        })
      }
    } catch (error) {
      console.error('加载岗位失败:', error)
    } finally {
      this.setData({
        loading: false,
        loadingMore: false
      })
    }
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
  },

  onSearch() {
    this.loadPositions(true)
  },

  applyFilters() {
    this.loadPositions(true)
  },

  resetFilters() {
    this.setData({
      keyword: '',
      selectedLocationIndex: 0,
      filters: {
        location: '',
        minSalary: SALARY_MIN,
        maxSalary: SALARY_MAX,
        internshipDuration: '',
        status: ''
      }
    }, () => {
      this.loadPositions(true)
    })
  },

  onLocationChange(e) {
    const index = Number(e.detail.value)
    const location = index === 0 ? '' : this.data.locationOptions[index]
    this.setData({
      selectedLocationIndex: index,
      'filters.location': location
    })
  },

  onDurationChange(e) {
    this.setData({
      'filters.internshipDuration': e.detail.value
    })
  },

  onStatusChange(e) {
    this.setData({
      'filters.status': e.detail.value
    })
  },

  onMinSalaryChange(e) {
    const value = Number(e.detail.value)
    const maxSalary = this.data.filters.maxSalary
    const nextValue = Math.min(Math.max(value, SALARY_MIN), maxSalary)
    this.setData({
      'filters.minSalary': nextValue
    })
  },

  onMaxSalaryChange(e) {
    const value = Number(e.detail.value)
    const minSalary = this.data.filters.minSalary
    const nextValue = Math.max(Math.min(value, SALARY_MAX), minSalary)
    this.setData({
      'filters.maxSalary': nextValue
    })
  },

  navigateToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/position-detail/position-detail?id=${id}`
    })
  },

  async applyPosition(e) {
    const id = e.currentTarget.dataset.id
    if (!app.globalData.token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    if (!app.globalData.user?.student_id) {
      wx.showModal({
        title: '提示',
        content: '请先绑定学号',
        showCancel: false,
        success: () => {
          wx.navigateTo({ url: '/pages/profile/profile' })
        }
      })
      return
    }

    try {
      wx.showLoading({ title: '提交中...' })
      const result = await api.post('/applications', {
        position_id: id,
        motivation: '希望获得实习机会'
      })
      wx.hideLoading()
      if (result.success) {
        wx.showToast({ title: '申请成功', icon: 'success' })
        // 标记本地已申请，避免重复点击
        const updated = this.data.positions.map(p => p.id === id ? { ...p, applied: true } : p)
        this.setData({
          positions: updated,
          appliedPositionIds: Array.from(new Set([...this.data.appliedPositionIds, id]))
        })
      }
    } catch (error) {
      wx.hideLoading()
      const message = error?.message || error?.data?.message || '申请失败'
      wx.showToast({ title: message, icon: 'none' })
      // 如果后端返回已申请，也同步前端状态
      if (message.includes('已申请')) {
        const updated = this.data.positions.map(p => p.id === id ? { ...p, applied: true } : p)
        this.setData({
          positions: updated,
          appliedPositionIds: Array.from(new Set([...this.data.appliedPositionIds, id]))
        })
      }
    }
  },

  onReachBottom() {
    if (!this.data.hasMore || this.data.loadingMore) {
      return
    }
    this.loadPositions()
  },

  openLocation(e) {
    const { latitude, longitude, name } = e.currentTarget.dataset
    const lat = Number(latitude)
    const lng = Number(longitude)
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      wx.showToast({
        title: '暂无法获取位置',
        icon: 'none'
      })
      return
    }
    wx.openLocation({
      latitude: lat,
      longitude: lng,
      name: name || '岗位位置',
      scale: 16
    })
  }
})

