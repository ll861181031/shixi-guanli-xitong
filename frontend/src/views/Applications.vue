<template>
  <div class="applications">
    <el-card>
      <template #header>
        <span>申请管理</span>
      </template>
      
      <el-table :data="applications" v-loading="loading" border>
        <el-table-column prop="student_name" label="学生姓名" />
        <el-table-column prop="student_id_number" label="学号" />
        <el-table-column prop="position_title" label="岗位标题" />
        <el-table-column prop="position_company" label="公司名称" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="success"
              @click="handleReview(row, 'approved')"
            >
              通过
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="danger"
              @click="handleReview(row, 'rejected')"
            >
              拒绝
            </el-button>
            <el-button size="small" @click="handleView(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchApplications"
        style="margin-top: 20px"
      />
    </el-card>
    
    <!-- 查看详情对话框 -->
    <el-dialog v-model="detailVisible" title="申请详情" width="600px">
      <el-descriptions :column="2" border v-if="currentApplication">
        <el-descriptions-item label="学生姓名">{{ currentApplication.student_name }}</el-descriptions-item>
        <el-descriptions-item label="学号">{{ currentApplication.student_id_number }}</el-descriptions-item>
        <el-descriptions-item label="岗位标题">{{ currentApplication.position_title }}</el-descriptions-item>
        <el-descriptions-item label="公司名称">{{ currentApplication.position_company }}</el-descriptions-item>
        <el-descriptions-item label="申请动机" :span="2">
          {{ currentApplication.motivation }}
        </el-descriptions-item>
        <el-descriptions-item label="简历" :span="2">
          {{ currentApplication.resume }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
    
    <!-- 审核对话框 -->
    <el-dialog v-model="reviewVisible" title="审核申请" width="500px">
      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="审核结果">
          <el-radio-group v-model="reviewForm.status">
            <el-radio label="approved">通过</el-radio>
            <el-radio label="rejected">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核意见">
          <el-input v-model="reviewForm.review_comment" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const applications = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const currentApplication = ref(null)

const reviewForm = reactive({
  status: 'approved',
  review_comment: ''
})

function getStatusType(status) {
  const map = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status) {
  const map = {
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝'
  }
  return map[status] || status
}

async function fetchApplications() {
  loading.value = true
  try {
    const response = await api.get('/applications', {
      params: { page: page.value, per_page: perPage.value }
    })
    if (response.data.success) {
      applications.value = response.data.data.items
      total.value = response.data.data.total
    }
  } catch (error) {
    ElMessage.error('获取申请列表失败')
  } finally {
    loading.value = false
  }
}

function handleView(row) {
  currentApplication.value = row
  detailVisible.value = true
}

function handleReview(row, status) {
  currentApplication.value = row
  reviewForm.status = status
  reviewForm.review_comment = ''
  reviewVisible.value = true
}

async function submitReview() {
  try {
    await api.post(`/applications/${currentApplication.value.id}/review`, reviewForm)
    ElMessage.success('审核成功')
    reviewVisible.value = false
    fetchApplications()
  } catch (error) {
    ElMessage.error('审核失败')
  }
}

onMounted(() => {
  fetchApplications()
})
</script>

