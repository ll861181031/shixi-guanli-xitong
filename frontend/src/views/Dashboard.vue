<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ overview.students?.total || 0 }}</div>
            <div class="stat-label">学生总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ overview.positions?.active || 0 }}</div>
            <div class="stat-label">活跃岗位</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ overview.applications?.pending || 0 }}</div>
            <div class="stat-label">待审核申请</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-value">{{ overview.checkins?.abnormal || 0 }}</div>
            <div class="stat-label">异常签到</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>近两周签到趋势</span>
          </template>
          <div ref="trendRef" style="height: 320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>岗位分布（按已接收）</span>
          </template>
          <div ref="positionRef" style="height: 320px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>周报提交率（按岗位）</span>
          </template>
          <div ref="reportRef" style="height: 320px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>待办事项</span>
          </template>
          <el-empty v-if="todoItems.length === 0" description="暂无待办" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="item in todoItems"
              :key="item.title"
              :timestamp="item.tip"
              :type="item.type"
            >
              {{ item.title }}
            </el-timeline-item>
          </el-timeline>
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

const overview = ref({
  students: {},
  positions: {},
  applications: {},
  checkins: {},
  reports: {}
})
const todoItems = ref([])

const trendRef = ref(null)
const positionRef = ref(null)
const reportRef = ref(null)
let trendChart = null
let positionChart = null
let reportChart = null

async function fetchOverview() {
  try {
    const response = await api.get('/statistics/overview')
    if (response.data.success) {
      overview.value = response.data.data
      buildTodo()
    }
  } catch (error) {
    ElMessage.error('获取数据失败')
  }
}

function buildTodo() {
  const items = []
  const pendingApp = overview.value.applications?.pending || 0
  const abnormalCheckins = overview.value.checkins?.abnormal || 0
  const submittedReports = overview.value.reports?.submitted || 0
  if (pendingApp > 0) {
    items.push({ title: `待审核申请 ${pendingApp} 个`, tip: '申请', type: 'warning' })
  }
  if (abnormalCheckins > 0) {
    items.push({ title: `异常签到 ${abnormalCheckins} 条`, tip: '签到', type: 'danger' })
  }
  if (submittedReports > 0) {
    items.push({ title: `待批改周报 ${submittedReports} 篇`, tip: '周报', type: 'primary' })
  }
  todoItems.value = items
}

async function loadCheckinTrend() {
  try {
    const res = await api.get('/statistics/checkin-trend', { params: { days: 14, group_by: 'day' } })
    if (res.data.success) {
      const data = res.data.data || []
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: data.map(i => i.label) },
        yAxis: { type: 'value' },
        series: [{ type: 'line', data: data.map(i => i.count), smooth: true, areaStyle: {} }]
      })
    }
  } catch (e) {
    // ignore
  }
}

async function loadPositionDistribution() {
  try {
    const res = await api.get('/statistics/position-distribution')
    if (res.data.success) {
      const data = res.data.data || []
      positionChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { top: 'bottom' },
        series: [{
          type: 'pie',
          radius: ['30%', '60%'],
          data: data.map(d => ({ name: d.position_title, value: d.student_count || 0 }))
        }]
      })
    }
  } catch (e) {
    // ignore
  }
}

async function loadReportRate() {
  try {
    const res = await api.get('/statistics/weekly-report-rate', { params: { group_by: 'position' } })
    if (res.data.success) {
      const data = res.data.data || []
      reportChart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: data.map(i => i.label) },
        yAxis: { type: 'value', max: 100 },
        series: [{
          type: 'bar',
          data: data.map(i => i.rate),
          itemStyle: { color: '#67c23a' }
        }]
      })
    }
  } catch (e) {
    // ignore
  }
}

function initCharts() {
  if (trendRef.value && !trendChart) trendChart = echarts.init(trendRef.value)
  if (positionRef.value && !positionChart) positionChart = echarts.init(positionRef.value)
  if (reportRef.value && !reportChart) reportChart = echarts.init(reportRef.value)
}

onMounted(() => {
  nextTick(() => {
    initCharts()
    fetchOverview()
    loadCheckinTrend()
    loadPositionDistribution()
    loadReportRate()
  })
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}

.stat-item {
  padding: 20px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>

