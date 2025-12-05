const api = require('../../utils/api')

function formatDate(date) {
  return date.toISOString().slice(0, 10)
}

Page({
  data: {
    checkins: [],
    calendarDays: [],
    monthLabel: '',
    today: formatDate(new Date()),
  },

  onLoad() {
    this.loadCheckins()
  },

  onPullDownRefresh() {
    this.loadCheckins().finally(() => wx.stopPullDownRefresh())
  },

  buildCalendarMap(records, year, month) {
    const map = {}
    records.forEach(r => {
      if (r.checkin_date) {
        map[r.checkin_date] = r.status
      }
    })
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const days = []
    const todayStr = this.data.today
    for (let d = 1; d <= lastDay.getDate(); d++) {
      const dateStr = formatDate(new Date(year, month, d))
      let status = map[dateStr] || 'not_signed'
      // 未来日期不展示状态
      if (dateStr > todayStr) status = 'future'
      days.push({
        day: d,
        dateStr,
        status,
      })
    }
    return days
  },

  async loadCheckins() {
    try {
      const now = new Date()
      const start = formatDate(new Date(now.getFullYear(), now.getMonth(), 1))
      const end = formatDate(new Date(now.getFullYear(), now.getMonth() + 1, 0))
      const result = await api.get('/checkins', { per_page: 200, start_date: start, end_date: end })
      const items = result?.data?.items || []
      const calendarDays = this.buildCalendarMap(items, now.getFullYear(), now.getMonth())
      this.setData({
        checkins: items,
        calendarDays,
        monthLabel: `${now.getFullYear()}年${now.getMonth() + 1}月`
      })
    } catch (error) {
      console.error('加载签到记录失败:', error)
      wx.showToast({ title: '加载签到记录失败', icon: 'none' })
    }
  }
})

