<template>
  <div class="users">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>用户管理</span>
          <div class="header-right">
            <el-select v-model="roleFilter" size="small" @change="fetchUsers">
              <el-option label="学生" value="student" />
              <el-option label="教师" value="teacher" />
              <el-option label="管理员" value="admin" />
              <el-option label="全部" value="all" />
            </el-select>
            <el-button
              v-if="isAdmin"
              type="primary"
              size="small"
              style="margin-left: 10px"
              @click="openCreateDialog"
            >
              新增用户
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="users" v-loading="loading" border>
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="real_name" label="真实姓名" />
        <el-table-column prop="student_id" label="学号" />
        <el-table-column prop="role" label="角色">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'teacher' ? 'warning' : 'success'">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="permissions" label="权限" width="260">
          <template #default="{ row }">
            <template v-if="row.permissions?.length">
              <el-tag
                v-for="item in row.permissions"
                :key="item"
                size="small"
                type="info"
                style="margin: 2px"
              >
                {{ formatPermission(item) }}
              </el-tag>
            </template>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="credit_score" label="信用分" width="90" />
        <el-table-column prop="created_at" label="创建时间" />
      </el-table>
      
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchUsers"
        style="margin-top: 20px"
      />

      <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px">
        <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="真实姓名" prop="real_name">
            <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
          </el-form-item>
          <el-form-item label="角色" prop="role">
            <el-select v-model="form.role" @change="handleRoleChange">
              <el-option label="学生" value="student" />
              <el-option label="教师" value="teacher" />
              <el-option label="管理员" value="admin" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="form.role === 'student'" label="学号" prop="student_id">
            <el-input v-model="form.student_id" placeholder="请输入学号" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.phone" placeholder="可选：请输入手机号" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="可选：请输入邮箱" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="默认密码" />
          </el-form-item>
          <el-form-item v-if="form.role === 'teacher'" label="权限" prop="permissions">
            <el-select
              v-model="form.permissions"
              multiple
              placeholder="请选择可访问模块"
            >
              <el-option
                v-for="item in permissionOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="submitLoading" @click="submitUser">确定</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const loading = ref(false)
const submitLoading = ref(false)
const users = ref([])
const page = ref(1)
const perPage = ref(10)
const total = ref(0)
const roleFilter = ref('student')
const dialogVisible = ref(false)
const dialogTitle = ref('新增用户')
const formRef = ref(null)

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

const permissionOptions = [
  { label: '岗位管理', value: 'positions' },
  { label: '申请管理', value: 'applications' },
  { label: '签到管理', value: 'checkins' },
  { label: '周报管理', value: 'reports' },
  { label: '数据统计', value: 'statistics' },
  { label: '用户管理', value: 'users' }
]

const permissionLabels = permissionOptions.reduce((acc, cur) => {
  acc[cur.value] = cur.label
  return acc
}, {})

const form = reactive({
  username: '',
  real_name: '',
  role: 'student',
  student_id: '',
  phone: '',
  email: '',
  password: '',
  permissions: []
})

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  student_id: [
    {
      validator: (rule, value, callback) => {
        if (form.role === 'student' && !value) {
          callback(new Error('学生需要填写学号'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function getRoleText(role) {
  const map = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return map[role] || role
}

function formatPermission(value) {
  return permissionLabels[value] || value
}

function resetForm() {
  form.username = ''
  form.real_name = ''
  form.role = 'student'
  form.student_id = ''
  form.phone = ''
  form.email = ''
  form.password = ''
  form.permissions = []
  formRef.value?.clearValidate()
}

function openCreateDialog() {
  resetForm()
  dialogVisible.value = true
}

function handleRoleChange() {
  if (form.role !== 'student') {
    form.student_id = ''
  }
  if (form.role !== 'teacher') {
    form.permissions = []
  }
  formRef.value?.validateField('student_id')
}

async function fetchUsers() {
  loading.value = true
  try {
    const response = await api.get('/users', {
      params: { page: page.value, per_page: perPage.value, role: roleFilter.value }
    })
    if (response.data.success) {
      users.value = response.data.data.items
      total.value = response.data.data.total
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function submitUser() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      const payload = {
        username: form.username,
        real_name: form.real_name,
        role: form.role,
        phone: form.phone || undefined,
        email: form.email || undefined,
        password: form.password
      }
      if (form.role === 'student') {
        payload.student_id = form.student_id
      }
      if (form.role === 'teacher') {
        payload.permissions = form.permissions
      }
      await api.post('/users', payload)
      ElMessage.success('新增用户成功')
      dialogVisible.value = false
      fetchUsers()
    } catch (error) {
      ElMessage.error(error.response?.data?.message || '新增用户失败')
    } finally {
      submitLoading.value = false
    }
  })
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-right {
  display: flex;
  align-items: center;
}
</style>

