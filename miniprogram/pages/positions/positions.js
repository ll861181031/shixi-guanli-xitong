const api = require('../../utils/api')

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
    statusOptions: STATUS_OPTIONS
  },

  onLoad() {
    this.loadLocations()
    this.loadPositions()
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
    this.loadPositions().finally(() => {
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

  async loadPositions() {
    this.setData({ loading: true })
    try {
      const result = await api.get('/positions', this.buildQueryParams())
      if (result.success) {
        const list = (result.data.items || []).map(decoratePosition)
        this.setData({ positions: list })
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

  onSearch() {
    this.loadPositions()
  },

  applyFilters() {
    this.loadPositions()
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
      this.loadPositions()
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
  }
})

