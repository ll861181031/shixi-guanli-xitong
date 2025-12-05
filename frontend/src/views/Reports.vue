<template>
  <div class="reports">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>周报管理</span>
          <el-button
            type="danger"
            size="small"
            :disabled="selectedIds.length === 0"
            @click="confirmBatchDelete"
          >批量删除</el-button>
        </div>
      </template>
      
      <el-table :data="reports" v-loading="loading" border @selection-change="onSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="student_name" label="学生姓名" />
        <el-table-column prop="student_id_number" label="学号" />
        <el-table-column prop="position_title" label="岗位标题" />
        <el-table-column prop="week_number" label="周次" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'reviewed' ? 'success' : 'warning'">
              {{ row.status === 'reviewed' ? '已批改' : '待批改' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="评分" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="row.status === 'submitted'"
              size="small"
              type="primary"
              @click="handleReview(row)"
            >
              批改
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchReports"
        style="margin-top: 20px"
      />
    </el-card>
    
    <!-- 查看/批改对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form :model="reviewForm" label-width="100px" v-if="currentReport">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学生姓名">{{ currentReport.student_name }}</el-descriptions-item>
          <el-descriptions-item label="学号">{{ currentReport.student_id_number }}</el-descriptions-item>
          <el-descriptions-item label="岗位标题">{{ currentReport.position_title }}</el-descriptions-item>
          <el-descriptions-item label="周次">{{ currentReport.week_number }}</el-descriptions-item>
        </el-descriptions>
        <el-form-item label="周报内容" style="margin-top: 20px">
          <el-input v-model="currentReport.content" type="textarea" :rows="6" readonly />
        </el-form-item>
        <el-form-item v-if="currentReport.attachment_name" label="附件">
          <el-link :href="getAttachmentUrl(currentReport.attachment_path)" target="_blank">
            {{ currentReport.attachment_name }}
          </el-link>
        </el-form-item>
        <el-form-item v-if="currentReport.status === 'submitted'" label="评分">
          <el-input-number v-model="reviewForm.score" :min="0" :max="100" />
        </el-form-item>
        <el-form-item v-if="currentReport.status === 'submitted'" label="批改意见">
          <el-input v-model="reviewForm.comment" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item v-if="currentReport.status === 'reviewed'" label="评分">
          <span>{{ currentReport.score }}</span>
        </el-form-item>
        <el-form-item v-if="currentReport.status === 'reviewed'" label="批改意见">
          <span>{{ currentReport.comment }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button
          v-if="currentReport?.status === 'submitted'"
          type="primary"
          @click="submitReview"
        >
          提交批改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const reports = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const dialogTitle = ref('周报详情')
const currentReport = ref(null)
const selectedIds = ref([])

const reviewForm = reactive({
  score: 0,
  comment: ''
})

function getAttachmentUrl(path) {
  if (!path) return ''
  return `/api/uploads/${path}`
}

async function fetchReports() {
  loading.value = true
  try {
    const response = await api.get('/weekly-reports', {
      params: { page: page.value, per_page: perPage.value }
    })
    if (response.data.success) {
      reports.value = response.data.data.items
      total.value = response.data.data.total
    }
  } catch (error) {
    ElMessage.error('获取周报列表失败')
  } finally {
    loading.value = false
  }
}

function onSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
}

async function confirmBatchDelete() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请选择周报')
    return
  }
  try {
    await ElMessageBox.confirm('确认删除选中的周报？此操作不可恢复', '提示', { type: 'warning' })
    await api.post('/weekly-reports/batch-delete', { ids: selectedIds.value })
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchReports()
  } catch (e) {
    // 已提示
  }
}

function handleView(row) {
  currentReport.value = { ...row }
  dialogTitle.value = '周报详情'
  dialogVisible.value = true
}

function handleReview(row) {
  currentReport.value = { ...row }
  reviewForm.score = 0
  reviewForm.comment = ''
  dialogTitle.value = '批改周报'
  dialogVisible.value = true
}

async function submitReview() {
  try {
    await api.post(`/weekly-reports/${currentReport.value.id}/review`, reviewForm)
    ElMessage.success('批改成功')
    dialogVisible.value = false
    fetchReports()
  } catch (error) {
    ElMessage.error('批改失败')
  }
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
}
.card-header > :last-child {
  margin-left: auto;
}
</style>
