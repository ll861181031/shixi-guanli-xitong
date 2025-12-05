<template>
  <div class="checkins">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>签到管理</span>
          <el-button
            v-if="isAdmin"
            type="danger"
            size="small"
            :disabled="selectedIds.length === 0"
            @click="confirmBatchDelete"
          >批量删除</el-button>
        </div>
      </template>
      
      <el-table :data="checkins" v-loading="loading" border @selection-change="onSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="student_name" label="学生姓名" />
        <el-table-column prop="student_id_number" label="学号" />
        <el-table-column prop="position_title" label="岗位标题" />
        <el-table-column prop="checkin_date" label="签到日期" />
        <el-table-column prop="checkin_time" label="签到时间" />
        <el-table-column prop="distance" label="距离(米)" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.status === 'normal' ? 'success' : 'danger'">
              {{ row.status === 'normal' ? '正常' : '异常' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchCheckins"
        style="margin-top: 20px"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const loading = ref(false)
const checkins = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const selectedIds = ref([])
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

async function fetchCheckins() {
  loading.value = true
  try {
    const response = await api.get('/checkins', {
      params: { page: page.value, per_page: perPage.value }
    })
    if (response.data.success) {
      checkins.value = response.data.data.items
      total.value = response.data.data.total
    }
  } catch (error) {
    ElMessage.error('获取签到记录失败')
  } finally {
    loading.value = false
  }
}

function onSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
}

async function confirmBatchDelete() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请选择记录')
    return
  }
  try {
    await ElMessageBox.confirm('确认删除选中的签到记录？此操作不可恢复', '提示', { type: 'warning' })
    await api.post('/checkins/batch-delete', { ids: selectedIds.value })
    ElMessage.success('批量删除成功')
    selectedIds.value = []
    fetchCheckins()
  } catch (e) {
    // 已提示
  }
}

onMounted(() => {
  fetchCheckins()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

