<template>
  <div class="forum-posts">
    <el-card>
      <template #header>
        <div class="header-actions">
          <div class="filters">
            <el-input
              v-model="filters.keyword"
              placeholder="关键词(标题/内容)"
              clearable
              style="width: 220px"
              @keyup.enter="fetchList"
            />
            <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px" @change="fetchList">
              <el-option label="待审核" value="pending" />
              <el-option label="已发布" value="reviewed" />
              <el-option label="已驳回" value="rejected" />
              <el-option label="已下架" value="disabled" />
            </el-select>
            <el-select v-model="filters.category_id" placeholder="分类" clearable style="width: 160px" @change="fetchList">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-date-picker
              v-model="filters.timeRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始"
              end-placeholder="结束"
              style="width: 340px"
              @change="fetchList"
            />
            <el-button type="primary" @click="fetchList">查询</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
          <div>
            <el-button size="small" :disabled="multipleSelection.length===0" @click="batchModerate('approve')">批量通过</el-button>
            <el-button size="small" :disabled="multipleSelection.length===0" @click="batchModerate('disable')">批量下架</el-button>
            <el-button size="small" type="danger" :disabled="multipleSelection.length===0" @click="batchDelete">批量删除</el-button>
          </div>
        </div>
      </template>

      <el-table :data="list" border style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column prop="author_name" label="发布者" width="120" />
        <el-table-column prop="category_name" label="分类" width="120" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.status==='pending'" type="warning">待审核</el-tag>
            <el-tag v-else-if="row.status==='reviewed'" type="success">已发布</el-tag>
            <el-tag v-else-if="row.status==='rejected'" type="danger">已驳回</el-tag>
            <el-tag v-else type="info">已下架</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="180" />
        <el-table-column prop="summary" label="摘要" />
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="moderate(row, 'approve')" :disabled="row.status==='reviewed'">通过</el-button>
            <el-button size="small" type="warning" @click="openReject(row)" :disabled="row.status==='rejected'">驳回</el-button>
            <el-button size="small" @click="moderate(row, 'disable')" :disabled="row.status==='disabled'">下架</el-button>
            <el-button size="small" type="danger" @click="deletePost(row)">删除</el-button>
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
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

    <el-dialog v-model="detailVisible" title="帖子详情" width="60%">
      <div v-if="currentDetail">
        <h3>{{ currentDetail.title }}</h3>
        <p style="color:#999">{{ currentDetail.author_name }} · {{ currentDetail.created_at }} · {{ currentDetail.category_name }}</p>
        <p style="white-space: pre-wrap; line-height: 1.6;">{{ currentDetail.content }}</p>
      </div>
    </el-dialog>

    <el-dialog v-model="rejectVisible" title="驳回原因">
      <el-input type="textarea" v-model="rejectReason" placeholder="请输入驳回原因" />
      <template #footer>
        <el-button @click="rejectVisible=false">取消</el-button>
        <el-button type="primary" @click="submitReject">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import api from '@/utils/api'

const list = ref([])
const categories = ref([])
const pagination = reactive({ page: 1, per_page: 10, total: 0 })
const filters = reactive({ keyword: '', status: '', category_id: '', timeRange: [] })
const multipleSelection = ref([])
const detailVisible = ref(false)
const currentDetail = ref(null)
const rejectVisible = ref(false)
const rejectReason = ref('')
const rejectTarget = ref(null)

onMounted(() => {
  loadCategories()
  fetchList()
})

async function loadCategories() {
  try {
    const res = await api.get('/forum/categories')
    categories.value = res.data.data || res.data || []
  } catch (e) {
    console.error(e)
  }
}

function buildParams(page) {
  const params = {
    page,
    per_page: pagination.per_page
  }
  if (filters.keyword) params.keyword = filters.keyword
  if (filters.status) params.status = filters.status
  if (filters.category_id) params.category_id = filters.category_id
  if (filters.timeRange && filters.timeRange.length === 2) {
    params.start_time = filters.timeRange[0]
    params.end_time = filters.timeRange[1]
  }
  return params
}

async function fetchList(page = 1) {
  try {
    const res = await api.get('/forum/posts', { params: buildParams(page) })
    const data = res.data.data
    list.value = data.items
    pagination.page = data.page
    pagination.per_page = data.per_page
    pagination.total = data.total
  } catch (e) {
    // handled globally
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  filters.category_id = ''
  filters.timeRange = []
  fetchList(1)
}

function changePage(p) {
  fetchList(p)
}

function handleSelectionChange(val) {
  multipleSelection.value = val
}

function viewDetail(row) {
  currentDetail.value = row
  detailVisible.value = true
}

async function moderate(row, action, reason) {
  await api.post(`/forum/posts/${row.id}/moderate`, { action, reason })
  ElMessage.success('操作成功')
  fetchList(pagination.page)
}

function openReject(row) {
  rejectTarget.value = row
  rejectReason.value = ''
  rejectVisible.value = true
}

async function submitReject() {
  if (!rejectTarget.value) return
  await moderate(rejectTarget.value, 'reject', rejectReason.value)
  rejectVisible.value = false
}

function confirmBatch(msg) {
  return ElMessageBox.confirm(msg, '提示', { type: 'warning' })
}

async function batchModerate(action) {
  if (multipleSelection.value.length === 0) return
  await confirmBatch('确认执行批量操作？')
  for (const row of multipleSelection.value) {
    await moderate(row, action)
  }
  multipleSelection.value = []
}

async function deletePost(row) {
  await ElMessageBox.confirm('确认删除该帖子？', '提示', { type: 'warning' })
  await api.delete(`/forum/posts/${row.id}`)
  ElMessage.success('已删除')
  fetchList(pagination.page)
}

async function batchDelete() {
  if (multipleSelection.value.length === 0) return
  await confirmBatch('确认批量删除选中帖子？')
  for (const row of multipleSelection.value) {
    await api.delete(`/forum/posts/${row.id}`)
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
  gap: 12px;
}
.filters {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}
.pager {
  margin-top: 16px;
  text-align: right;
}
</style>

