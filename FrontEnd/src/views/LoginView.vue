<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>智能体评估系统</h2>
          <p>请登录或注册账号</p>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-width="80px"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名或邮箱"
                clearable
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="handleLogin"
                style="width: 100%"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <!-- 注册要求提示 -->
          <el-alert
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 20px;"
          >
            <template #title>
              <div style="font-size: 13px;">
                <div><strong>注册要求：</strong></div>
                <div>• 用户名：至少3个字符，必须唯一</div>
                <div>• 邮箱：必须是有效的邮箱格式（如：user@example.com）</div>
                <div>• 密码：至少6个字符，建议使用字母+数字组合</div>
              </div>
            </template>
          </el-alert>

          <!-- 错误提示（如果有） -->
          <el-alert
            v-if="registerError"
            type="error"
            :closable="true"
            show-icon
            @close="registerError = ''"
            style="margin-bottom: 20px;"
          >
            <template #title>
              <div style="font-size: 13px;">
                <div><strong>{{ registerError }}</strong></div>
                <div v-if="registerErrorDetail" style="margin-top: 5px; color: #909399;">
                  {{ registerErrorDetail }}
                </div>
              </div>
            </template>
          </el-alert>

          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-width="80px"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名（至少3个字符）"
                clearable
                @input="clearRegisterError"
              />
              <div class="form-tip">用户名将用于登录，请确保唯一性</div>
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入邮箱（如：user@example.com）"
                clearable
                @input="clearRegisterError"
              />
              <div class="form-tip">用于登录和找回密码，请使用真实邮箱</div>
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码（至少6位）"
                show-password
                @input="clearRegisterError"
              />
              <div class="form-tip">建议使用字母、数字组合，提高安全性</div>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
                @input="clearRegisterError"
                @keyup.enter="handleRegister"
              />
              <div class="form-tip">请确保与上方密码完全一致</div>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="handleRegister"
                style="width: 100%"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const registerError = ref('')
const registerErrorDetail = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 登录表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度至少3位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 处理标签页切换
const handleTabChange = () => {
  loginFormRef.value?.clearValidate()
  registerFormRef.value?.clearValidate()
  clearRegisterError()
}

// 清除注册错误提示
const clearRegisterError = () => {
  registerError.value = ''
  registerErrorDetail.value = ''
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      const success = await userStore.login(loginForm.username, loginForm.password)
      loading.value = false
      if (success) {
        router.push('/')
      }
    }
  })
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  // 清除之前的错误提示
  clearRegisterError()

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      const result = await userStore.register(
        registerForm.username,
        registerForm.email,
        registerForm.password
      )
      loading.value = false
      
      if (result.success) {
        // 注册成功后切换到登录标签页
        activeTab.value = 'login'
        loginForm.username = registerForm.username
        registerFormRef.value.resetFields()
        clearRegisterError()
      } else {
        // 显示详细的错误信息
        registerError.value = result.message || '注册失败'
        registerErrorDetail.value = result.detail || ''
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 450px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.card-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>

