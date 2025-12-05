<template>
  <div class="positions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>岗位管理</span>
          <div class="header-actions" v-if="canManage">
            <el-button
              type="danger"
              size="small"
              :disabled="selectedPositionIds.length === 0"
              @click="handleBatchDelete"
            >
              批量删除
            </el-button>
            <el-button type="primary" size="small" @click="handleCreate">新增岗位</el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="positions"
        v-loading="loading"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="岗位标题" />
        <el-table-column prop="company_name" label="公司名称" />
        <el-table-column prop="location" label="工作地点" />
        <el-table-column label="薪资范围">
          <template #default="{ row }">
            {{ formatSalary(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="internship_duration" label="实习时长" />
        <el-table-column prop="current_students" label="当前学生数" />
        <el-table-column prop="max_students" label="最大学生数" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchPositions"
        style="margin-top: 20px"
      />
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="form" label-width="100px">
        <el-form-item label="岗位标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="公司名称">
          <el-input v-model="form.company_name" />
        </el-form-item>
        <el-form-item label="工作地点">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="form.latitude" :precision="6" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="form.longitude" :precision="6" />
        </el-form-item>
        <el-form-item label="岗位描述">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="岗位要求">
          <el-input v-model="form.requirements" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="薪资范围">
          <div class="salary-range">
    <el-input-number
      v-model="form.min_salary"
      :min="0"
      :step="500"
      controls-position="right"
      :value-on-clear="null"
      placeholder="最低薪资"
    />
    <span class="salary-sep">~</span>
    <el-input-number
      v-model="form.max_salary"
      :min="0"
      :step="500"
      controls-position="right"
      :value-on-clear="null"
      placeholder="最高薪资"
    />
  </div>
        </el-form-item>
        <el-form-item label="实习时长">
          <el-select
            v-model="form.internship_duration"
            placeholder="请选择/输入"
            filterable
            allow-create
            clearable
          >
            <el-option
              v-for="item in durationOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="最大学生数">
          <el-input-number v-model="form.max_students" :min="1" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.value"
            >
              {{ item.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const loading = ref(false)
const positions = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const dialogTitle = ref('新增岗位')
const editingId = ref(null)
const selectedPositionIds = ref([])

const authStore = useAuthStore()
const canManage = computed(() => authStore.user?.role === 'admin')

const statusOptions = [
  { label: '在招', value: 1, tag: 'success' },
  { label: '招满', value: 0, tag: 'info' },
  { label: '暂停', value: 2, tag: 'warning' }
]

const durationOptions = ['1个月以内', '1-3个月', '3-6个月', '6个月以上']

const statusMap = statusOptions.reduce((acc, cur) => {
  acc[cur.value] = cur
  return acc
}, {})

function getStatusText(status) {
  return statusMap[status]?.label || '未知'
}

function getStatusTag(status) {
  return statusMap[status]?.tag || 'info'
}

function formatSalary(row) {
  if (row?.salary_range_text) {
    return row.salary_range_text
  }
  const min = row?.min_salary
  const max = row?.max_salary
  if (min != null && max != null) {
    return `${min}-${max}元/月`
  }
  if (min != null) {
    return `≥${min}元/月`
  }
  if (max != null) {
    return `≤${max}元/月`
  }
  return '面议'
}

function getDefaultForm() {
  return {
    title: '',
    company_name: '',
    location: '',
    latitude: 0,
    longitude: 0,
    description: '',
    requirements: '',
    max_students: 1,
    min_salary: null,
    max_salary: null,
    internship_duration: '',
    status: 1
  }
}

const form = reactive(getDefaultForm())

function resetForm() {
  Object.assign(form, getDefaultForm())
}

async function fetchPositions() {
  loading.value = true
  try {
    const response = await api.get('/positions', {
      params: { page: page.value, per_page: perPage.value }
    })
    if (response.data.success) {
      positions.value = response.data.data.items
      total.value = response.data.data.total
    }
  } catch (error) {
    ElMessage.error('获取岗位列表失败')
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  editingId.value = null
  dialogTitle.value = '新增岗位'
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  editingId.value = row.id
  dialogTitle.value = '编辑岗位'
  resetForm()
  Object.assign(form, {
    title: row.title,
    company_name: row.company_name,
    location: row.location,
    latitude: row.latitude,
    longitude: row.longitude,
    description: row.description,
    requirements: row.requirements,
    max_students: row.max_students,
    min_salary: row.min_salary,
    max_salary: row.max_salary,
    internship_duration: row.internship_duration,
    status: row.status ?? 1
  })
  dialogVisible.value = true
}

function buildPayload() {
  return {
    title: form.title,
    company_name: form.company_name,
    location: form.location,
    latitude: form.latitude,
    longitude: form.longitude,
    description: form.description,
    requirements: form.requirements,
    max_students: form.max_students,
    min_salary: form.min_salary,
    max_salary: form.max_salary,
    internship_duration: form.internship_duration,
    status: form.status
  }
}

async function handleSubmit() {
  if (
    form.min_salary != null &&
    form.max_salary != null &&
    form.min_salary > form.max_salary
  ) {
    ElMessage.error('最低薪资不能高于最高薪资')
    return
  }

  const payload = buildPayload()

  try {
    if (editingId.value) {
      await api.put(`/positions/${editingId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/positions', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchPositions()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该岗位吗？', '提示', {
      type: 'warning'
    })
    await api.delete(`/positions/${row.id}`)
    ElMessage.success('删除成功')
    fetchPositions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function handleSelectionChange(selection) {
  selectedPositionIds.value = selection.map(item => item.id)
}

async function handleBatchDelete() {
  if (!selectedPositionIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedPositionIds.value.length} 个岗位吗？`, '提示', {
      type: 'warning'
    })
    await api.post('/positions/batch-delete', { ids: selectedPositionIds.value })
    ElMessage.success('批量删除成功')
    selectedPositionIds.value = []
    fetchPositions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '批量删除失败')
    }
  }
}

onMounted(() => {
  fetchPositions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.salary-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.salary-sep {
  color: #999;
}
</style>

