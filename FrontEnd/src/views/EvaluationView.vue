<template>
  <div class="app-container">
    <!-- 页面标题和用户信息 -->
    <div class="header-section">
      <el-page-header content="智能体评估系统" />
      <div class="user-info">
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-icon><User /></el-icon>
            <span>{{ userStore.user?.username || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled>
                <span style="color: #909399;">{{ userStore.user?.email }}</span>
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主内容区 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：评估配置 -->
      <el-col :span="8">
        <el-card>
          <template #header>评估配置</template>

          <el-form :model="form" label-width="100px">
            <!-- 原有表单内容不变 -->
            <el-form-item label="API密钥" required>
              <el-input
                v-model="form.apiKey"
                type="password"
                placeholder="请输入智谱AI API密钥"
                clearable
              />
            </el-form-item>

            <el-form-item label="测试用例来源">
              <el-radio-group v-model="form.testCaseSource">
                <el-radio label="default">默认测试集</el-radio>
                <el-radio label="custom">自定义测试集</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item
              label="自定义测试集"
              v-if="form.testCaseSource === 'custom'"
            >
              <el-upload
                accept=".json"
                :auto-upload="false"
                :on-change="handleTestCasesUpload"
                :show-file-list="true"
              >
                <el-button type="primary">选择JSON文件</el-button>
              </el-upload>
              <div class="text-help">格式：[{"type":"functional","input":"问题","expected":"答案","category":"分类"}]</div>
            </el-form-item>

            <el-form-item label="评估类型">
              <el-checkbox-group v-model="form.evaluationTypes">
                <el-checkbox label="functional">功能评估</el-checkbox>
                <el-checkbox label="safety">安全评估</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item>
              <!-- 新增：取消按钮，与开始按钮并排 -->
              <el-button
                type="primary"
                @click="startEvaluation"
                :loading="isEvaluating"
                :disabled="!form.apiKey || form.evaluationTypes.length === 0 || isEvaluating"
              >
                开始评估
              </el-button>
              <el-button
                type="warning"
                @click="cancelEvaluation"
                :disabled="!isEvaluating"
                style="margin-left: 10px;"
              >
                取消评估
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：评估结果（不变，新增对“取消”状态的处理） -->
      <el-col :span="16">
        <!-- 评估进度 -->
        <el-card v-if="isEvaluating">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>评估进度</span>
              <span style="font-size: 18px; font-weight: bold; color: #409EFF;">
                {{ progress }}%
              </span>
            </div>
          </template>
          <div class="progress-container">
            <el-progress
              :percentage="progress"
              :status="progress < 100 ? 'progress' : 'success'"
              :format="() => `${progress}%`"
            />
            <div class="progress-info">
              <div class="progress-text">
                <strong>当前进度：</strong>
                <span v-if="totalCases > 0">
                  第 {{ currentIndex }} / {{ totalCases }} 个测试用例
                </span>
                <span v-else>准备中...</span>
              </div>
              <div class="progress-text" style="margin-top: 8px;">
                <strong>当前测试用例：</strong>{{ currentTestCase }}
              </div>
              <div v-if="currentInput" class="progress-detail">
                <div class="detail-item">
                  <span class="detail-label">测试输入：</span>
                  <span class="detail-content">{{ currentInput }}</span>
                </div>
                <div class="detail-item" v-if="currentResponse">
                  <span class="detail-label">智能体回答：</span>
                  <div class="response-content">
                    {{ currentResponse }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 评估结果概览 -->
        <el-card v-if="evaluationSummary && !isEvaluating">
          <template #header>评估结果概览</template>
          <el-row :gutter="20">
            <el-col :span="6" v-if="evaluationSummary.functional">
              <div class="stat-card">
                <div class="stat-label">功能评估准确率</div>
                <div class="stat-value">{{ (evaluationSummary.functional.accuracy * 100).toFixed(1) }}%</div>
                <div style="color: #909399; font-size: 12px; margin-top: 5px;">
                  通过 {{ evaluationSummary.functional.count }} 项
                </div>
              </div>
            </el-col>
            <el-col :span="6" v-if="evaluationSummary.safety">
              <div class="stat-card">
                <div class="stat-label">安全评估通过率</div>
                <div class="stat-value">{{ (evaluationSummary.safety.safety_rate * 100).toFixed(1) }}%</div>
                <div style="color: #909399; font-size: 12px; margin-top: 5px;">
                  通过 {{ evaluationSummary.safety.count }} 项
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总体得分</div>
                <div class="stat-value">{{ (evaluationSummary.summary.overall_score * 100).toFixed(1) }}%</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总耗时</div>
                <div class="stat-value">{{ evaluationSummary.total_time }}s</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 详细评估结果 -->
        <el-card v-if="evaluationResults.length > 0 && !isEvaluating" style="margin-top: 20px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>详细评估结果</span>
              <el-radio-group v-model="resultFilter" size="small">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="functional">功能评估</el-radio-button>
                <el-radio-button label="safety">安全评估</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <el-table :data="filteredResults" stripe style="width: 100%">
            <el-table-column prop="type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.type === 'functional' ? 'success' : 'warning'">
                  {{ row.type === 'functional' ? '功能' : '安全' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120" />
            <el-table-column prop="input" label="输入" min-width="200" show-overflow-tooltip />
            <el-table-column prop="expected" label="期望结果" min-width="150" show-overflow-tooltip />
            <el-table-column prop="actual" label="实际结果" min-width="200" show-overflow-tooltip />
            <el-table-column prop="passed" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.passed ? 'success' : 'danger'">
                  {{ row.passed ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-empty
          description="暂无评估结果，请点击开始评估"
          v-if="evaluationResults.length === 0 && !isEvaluating"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, ArrowDown } from '@element-plus/icons-vue'
import request from '../utils/request'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

// 1. 类型定义（新增任务ID和取消状态的适配）
interface FormData {
  apiKey: string
  testCaseSource: 'default' | 'custom'
  evaluationTypes: ('functional' | 'safety')[]
  customTestCases: Array<{
    type: 'functional' | 'safety'
    input: string
    expected: string
    category: string
  }> | null
}

interface EvaluationResult {
  type: 'functional' | 'safety'
  category: string
  input: string
  expected: string
  actual: string
  passed: boolean
}

interface EvaluationSummary {
  total_time: number
  functional?: {
    accuracy: number
    count: number
  }
  safety?: {
    safety_rate: number
    count: number
  }
  summary: {
    overall_score: number
  }
}

// 2. 状态管理（新增任务ID存储）
const form: FormData = reactive({
  apiKey: '',
  testCaseSource: 'default',
  evaluationTypes: ['functional', 'safety'],
  customTestCases: null
})

const isEvaluating = ref(false)
const progress = ref(0)
const currentTestCase = ref('')
const currentInput = ref('')
const currentResponse = ref('')
const currentIndex = ref(0)
const totalCases = ref(0)
const evaluationResults = ref<EvaluationResult[]>([])
const evaluationSummary = ref<EvaluationSummary | null>(null)
const resultFilter = ref('')
let pollInterval: NodeJS.Timeout | null = null
const taskId = ref('')  // 新增：存储当前任务ID

// 3. 处理自定义测试用例上传（不变）
const handleTestCasesUpload = (file: any) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const content = JSON.parse((e.target as FileReader).result as string)
      form.customTestCases = content
      ElMessage.success(`已加载 ${content.length} 条测试用例`)
    } catch (error) {
      ElMessage.error('JSON格式错误，请检查文件')
      console.error(error)
    }
  }
  reader.readAsText(file.raw)
}

// 4. 筛选结果（不变）
const filteredResults = computed(() => {
  if (!resultFilter.value) return evaluationResults.value
  return evaluationResults.value.filter(item => item.type === resultFilter.value)
})

// 5. 开始评估（修改：记录任务ID）
const startEvaluation = async () => {
  isEvaluating.value = true
  progress.value = 0
  evaluationResults.value = []
  evaluationSummary.value = null
  taskId.value = ''  // 重置任务ID

  try {
    // 调用后端启动评估接口
    const response = await request.post('/api/evaluate', {
      api_key: form.apiKey,
      test_case_source: form.testCaseSource,
      custom_test_cases: form.customTestCases,
      evaluation_types: form.evaluationTypes
    })
    taskId.value = response.data.task_id  // 保存任务ID

    // 轮询获取评估进度（新增：处理"取消"状态）
    pollInterval = setInterval(async () => {
      if (!taskId.value) {
        clearInterval(pollInterval!)
        return
      }

      try {
        const statusResponse = await request.get(`/api/evaluation/${taskId.value}`)
        const taskStatus = statusResponse.data

        // 更新进度和结果
        progress.value = taskStatus.progress
        currentTestCase.value = taskStatus.current_case || ''
        currentInput.value = taskStatus.current_input || ''
        currentResponse.value = taskStatus.current_response || ''
        currentIndex.value = taskStatus.current_index || 0
        totalCases.value = taskStatus.total_cases || 0
        evaluationResults.value = taskStatus.results || []

        // 处理所有可能的状态：完成、失败、取消
        if (taskStatus.status === 'completed') {
          clearInterval(pollInterval!)
          evaluationSummary.value = taskStatus.summary
          isEvaluating.value = false
          ElMessage.success('评估完成！')
        } else if (taskStatus.status === 'failed') {
          clearInterval(pollInterval!)
          ElMessage.error(`评估失败：${taskStatus.error}`)
          isEvaluating.value = false
        } else if (taskStatus.status === 'cancelled') {  // 新增：处理取消状态
          clearInterval(pollInterval!)
          ElMessage.info('评估已取消')
          isEvaluating.value = false
        }
      } catch (error: any) {
        clearInterval(pollInterval!)
        ElMessage.error('获取评估状态失败：' + error.message)
        isEvaluating.value = false
      }
    }, 1000)  // 每秒查询一次

  } catch (error: any) {
    ElMessage.error('启动评估失败：' + (error.response?.data?.detail || error.message))
    isEvaluating.value = false
  }
}

// 新增：取消评估的方法
const cancelEvaluation = async () => {
  if (!taskId.value || !isEvaluating.value) return

  try {
    // 调用后端取消接口
    await request.post(`/api/cancel/${taskId.value}`)
    // 清除轮询并更新状态
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
    isEvaluating.value = false
    currentTestCase.value = '评估已取消'
    ElMessage.success('评估已成功取消')
  } catch (error: any) {
    ElMessage.error('取消评估失败：' + (error.response?.data?.detail || error.message))
  }
}

// 处理用户下拉菜单命令
const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}

// 组件挂载时获取用户信息
onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.user) {
    await userStore.fetchUserInfo()
  }
})
</script>

<style scoped>
.app-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.progress-container {
  padding: 20px 0;
}

.progress-text {
  margin: 10px 0;
  color: #606266;
  font-size: 14px;
}

.progress-info {
  margin-top: 15px;
}

.progress-detail {
  margin-top: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  border-left: 3px solid #409EFF;
}

.detail-item {
  margin-bottom: 12px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: bold;
  color: #303133;
  display: inline-block;
  min-width: 100px;
  margin-right: 10px;
}

.detail-content {
  color: #606266;
  word-break: break-word;
}

.response-content {
  color: #606266;
  background-color: #ffffff;
  padding: 10px;
  border-radius: 4px;
  margin-top: 5px;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
}

.stat-card {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  text-align: center;
}

.stat-label {
  color: #606266;
  font-size: 14px;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #1890ff;
}

.text-help {
  color: #606266;
  font-size: 12px;
  margin-top: 5px;
}
</style>