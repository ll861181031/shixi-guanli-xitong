<template>
  <div class="forum-categories">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>分类管理</span>
          <el-button type="primary" size="small" @click="openDialog()">新增分类</el-button>
        </div>
      </template>

      <el-table :data="list" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-switch v-model="row.status" :active-value="1" :inactive-value="0" @change="toggleStatus(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import api from '@/utils/api'

const list = ref([])
const dialogVisible = ref(false)
const form = reactive({ id: null, name: '', status: 1 })

const dialogTitle = computed(() => (form.id ? '编辑分类' : '新增分类'))

onMounted(() => {
  fetchList()
})

async function fetchList() {
  const res = await api.get('/forum/categories')
  list.value = res.data.data || res.data || []
}

function openDialog(row) {
  if (row) {
    form.id = row.id
    form.name = row.name
    form.status = row.status
  } else {
    form.id = null
    form.name = ''
    form.status = 1
  }
  dialogVisible.value = true
}

async function save() {
  if (!form.name) {
    ElMessage.error('请输入名称')
    return
  }
  if (form.id) {
    await api.put(`/forum/categories/${form.id}`, { name: form.name, status: form.status })
  } else {
    await api.post('/forum/categories', { name: form.name, status: form.status })
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  fetchList()
}

async function deleteCategory(row) {
  try {
    await ElMessageBox.confirm('删除后不可恢复，确认删除？', '提示', { type: 'warning' })
    await api.delete(`/forum/categories/${row.id}`)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    // 已提示
  }
}

async function toggleStatus(row) {
  await api.put(`/forum/categories/${row.id}`, { status: row.status })
  ElMessage.success('状态已更新')
}
</script>

<style scoped>
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

