<template>
  <div class="positions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>岗位管理</span>
          <el-button type="primary" @click="handleCreate">新增岗位</el-button>
        </div>
      </template>
      
      <el-table :data="positions" v-loading="loading" border>
        <el-table-column prop="title" label="岗位标题" />
        <el-table-column prop="company_name" label="公司名称" />
        <el-table-column prop="location" label="工作地点" />
        <el-table-column prop="current_students" label="当前学生数" />
        <el-table-column prop="max_students" label="最大学生数" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '已关闭' }}
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
        <el-form-item label="最大学生数">
          <el-input-number v-model="form.max_students" :min="1" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="活跃" value="active" />
            <el-option label="已关闭" value="closed" />
          </el-select>
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
import { ref, reactive, onMounted } from 'vue'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const positions = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const dialogTitle = ref('新增岗位')
const editingId = ref(null)

const form = reactive({
  title: '',
  company_name: '',
  location: '',
  latitude: 0,
  longitude: 0,
  description: '',
  requirements: '',
  max_students: 1,
  status: 'active'
})

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
  Object.assign(form, {
    title: '',
    company_name: '',
    location: '',
    latitude: 0,
    longitude: 0,
    description: '',
    requirements: '',
    max_students: 1,
    status: 'active'
  })
  dialogVisible.value = true
}

function handleEdit(row) {
  editingId.value = row.id
  dialogTitle.value = '编辑岗位'
  Object.assign(form, row)
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    if (editingId.value) {
      await api.put(`/positions/${editingId.value}`, form)
      ElMessage.success('更新成功')
    } else {
      await api.post('/positions', form)
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
</style>

