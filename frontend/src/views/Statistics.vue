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
            <span>周报提交率统计</span>
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
            <span>签到趋势</span>
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

async function loadReportSubmissionRate() {
  try {
    const response = await api.get('/statistics/report-submission-rate')
    if (response.data.success) {
      const data = response.data.data
      const names = data.map(item => item.student_name)
      const rates = data.map(item => item.submission_rate)
      
      reportChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: names },
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
      params: { days: 30 }
    })
    if (response.data.success) {
      const data = response.data.data
      const dates = data.map(item => item.date)
      const counts = data.map(item => item.count)
      
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: dates },
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
    loadReportSubmissionRate()
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
</style>

