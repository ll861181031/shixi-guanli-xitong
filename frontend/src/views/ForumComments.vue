<template>
  <div class="forum-comments">
    <el-card>
      <template #header>
        <div class="header-actions">
          <div class="filters">
            <el-input v-model="filters.post_id" placeholder="帖子ID" clearable style="width: 160px" @keyup.enter="fetchList" />
            <el-button type="primary" @click="fetchList">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
          <div>
            <el-button type="danger" size="small" :disabled="multipleSelection.length===0" @click="batchDelete">批量删除</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="post_id" label="帖子ID" width="100" />
        <el-table-column prop="user_name" label="评论者" width="120" />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteComment(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :page-size="pagination.per_page"
          :total="pagination.total"
          :current-page="pagination.page"
          @current-change="changePage"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import api from '@/utils/api'

const list = ref([])
const pagination = reactive({ page: 1, per_page: 10, total: 0 })
const filters = reactive({ post_id: '' })
const multipleSelection = ref([])

onMounted(() => {
  fetchList()
})

function buildParams(page) {
  const params = { page, per_page: pagination.per_page }
  if (filters.post_id) params.post_id = filters.post_id
  return params
}

async function fetchList(page = 1) {
  try {
    const res = await api.get('/forum/comments', { params: buildParams(page) })
    const data = res.data.data
    list.value = data.items
    pagination.page = data.page
    pagination.per_page = data.per_page
    pagination.total = data.total
  } catch (e) {
    // global handler
  }
}

function resetFilters() {
  filters.post_id = ''
  fetchList(1)
}

function changePage(p) {
  fetchList(p)
}

function handleSelectionChange(val) {
  multipleSelection.value = val
}

async function deleteComment(row) {
  await ElMessageBox.confirm('确认删除该评论？', '提示', { type: 'warning' })
  await api.delete(`/forum/comments/${row.id}`)
  ElMessage.success('已删除')
  fetchList(pagination.page)
}

async function batchDelete() {
  if (multipleSelection.value.length === 0) return
  await ElMessageBox.confirm('确认批量删除选中评论？', '提示', { type: 'warning' })
  for (const row of multipleSelection.value) {
    await api.delete(`/forum/comments/${row.id}`)
  }
  ElMessage.success('批量删除完成')
  multipleSelection.value = []
  fetchList(pagination.page)
}
</script>

<style scoped>
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}
.pager {
  margin-top: 16px;
  text-align: right;
}
</style>

