<template>
  <div class="statistics">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>出勤率统计</span>
          </template>
          <div ref="attendanceChartRef" style="height: 400px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>周报提交率统计</span>
              <el-radio-group v-model="weeklyRateGroupBy" size="small" @change="loadWeeklyReportRate">
                <el-radio-button label="position">按岗位</el-radio-button>
                <el-radio-button label="student">按学生</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="reportChartRef" style="height: 400px"></div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>岗位分布</span>
          </template>
          <div ref="positionChartRef" style="height: 400px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>签到趋势</span>
              <el-radio-group v-model="checkinGranularity" size="small" @change="loadCheckinTrend">
                <el-radio-button label="day">按日</el-radio-button>
                <el-radio-button label="week">按周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChartRef" style="height: 400px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const attendanceChartRef = ref(null)
const reportChartRef = ref(null)
const positionChartRef = ref(null)
const trendChartRef = ref(null)

let attendanceChart = null
let reportChart = null
let positionChart = null
let trendChart = null

const checkinGranularity = ref('day')
const weeklyRateGroupBy = ref('position')

async function loadAttendanceRate() {
  try {
    const response = await api.get('/statistics/attendance-rate')
    if (response.data.success) {
      const data = response.data.data
      const names = data.map(item => item.student_name)
      const rates = data.map(item => item.attendance_rate)
      
      attendanceChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: names },
        yAxis: { type: 'value', max: 100 },
        series: [{
          data: rates,
          type: 'bar',
          itemStyle: { color: '#409eff' }
        }]
      })
    }
  } catch (error) {
    ElMessage.error('获取出勤率数据失败')
  }
}

async function loadWeeklyReportRate() {
  try {
    const response = await api.get('/statistics/weekly-report-rate', {
      params: { group_by: weeklyRateGroupBy.value }
    })
    if (response.data.success) {
      const data = response.data.data
      const labels = data.map(item => item.label)
      const rates = data.map(item => item.rate)
      const tips = data.map((item) => {
        if (weeklyRateGroupBy.value === 'position') {
          return `${item.submitted_students}/${item.total_students}`
        }
        return `${item.report_count}`
      })
      reportChart.setOption({
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const index = params[0].dataIndex
            const extra = weeklyRateGroupBy.value === 'position'
              ? `提交学生：${tips[index]}`
              : `提交周报：${tips[index]}`
            return `${labels[index]}<br/>提交率：${rates[index]}%<br/>${extra}`
          }
        },
        xAxis: { type: 'category', data: labels },
        yAxis: { type: 'value', max: 100 },
        series: [{
          data: rates,
          type: 'bar',
          itemStyle: { color: '#67c23a' }
        }]
      })
    }
  } catch (error) {
    ElMessage.error('获取周报提交率数据失败')
  }
}

async function loadPositionDistribution() {
  try {
    const response = await api.get('/statistics/position-distribution')
    if (response.data.success) {
      const data = response.data.data
      const names = data.map(item => item.position_title)
      const values = data.map(item => item.student_count)
      
      positionChart.setOption({
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          data: names.map((name, index) => ({
            value: values[index],
            name: name
          }))
        }]
      })
    }
  } catch (error) {
    ElMessage.error('获取岗位分布数据失败')
  }
}

async function loadCheckinTrend() {
  try {
    const response = await api.get('/statistics/checkin-trend', {
      params: { days: 30, group_by: checkinGranularity.value }
    })
    if (response.data.success) {
      const data = response.data.data
      const labels = data.map(item => item.label)
      const counts = data.map(item => item.count)
      
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: labels },
        yAxis: { type: 'value' },
        series: [{
          data: counts,
          type: 'line',
          smooth: true,
          itemStyle: { color: '#e6a23c' }
        }]
      })
    }
  } catch (error) {
    ElMessage.error('获取签到趋势数据失败')
  }
}

onMounted(async () => {
  await nextTick()
  
  if (attendanceChartRef.value) {
    attendanceChart = echarts.init(attendanceChartRef.value)
    loadAttendanceRate()
  }
  
  if (reportChartRef.value) {
    reportChart = echarts.init(reportChartRef.value)
    loadWeeklyReportRate()
  }
  
  if (positionChartRef.value) {
    positionChart = echarts.init(positionChartRef.value)
    loadPositionDistribution()
  }
  
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    loadCheckinTrend()
  }
})
</script>

<style scoped>
.statistics {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
</style>

