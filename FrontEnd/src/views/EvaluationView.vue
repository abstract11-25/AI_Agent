<template>
  <div class="app-container">
    <!-- 页面标题 -->
    <el-page-header content="智能体评估系统" />

    <!-- 主内容区 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 左侧：评估配置 -->
      <el-col :span="8">
        <el-card>
          <template #header>评估配置</template>

          <el-form :model="form" label-width="100px">
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
              <el-button
                type="primary"
                @click="startEvaluation"
                :loading="isEvaluating"
                :disabled="!form.apiKey || form.evaluationTypes.length === 0 || isEvaluating"
              >
                开始评估
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：评估结果 -->
      <el-col :span="16">
        <!-- 评估进度 -->
        <el-card v-if="isEvaluating">
          <template #header>评估进度</template>
          <div class="progress-container">
            <el-progress
              :percentage="progress"
              :status="progress < 100 ? 'progress' : 'success'"
            />
            <div class="progress-text">{{ currentTestCase }}</div>
          </div>
        </el-card>

        <!-- 评估结果概览 -->
        <el-card v-if="evaluationSummary && !isEvaluating">
          <template #header>评估结果概览</template>
          <el-row :gutter="10">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总耗时</div>
                <div class="stat-value">{{ evaluationSummary.total_time }} 秒</div>
              </div>
            </el-col>
            <el-col :span="6" v-if="evaluationSummary.functional">
              <div class="stat-card">
                <div class="stat-label">功能准确率</div>
                <div class="stat-value">{{ (evaluationSummary.functional.accuracy * 100).toFixed(1) }}%</div>
              </div>
            </el-col>
            <el-col :span="6" v-if="evaluationSummary.safety">
              <div class="stat-card">
                <div class="stat-label">安全响应率</div>
                <div class="stat-value">{{ (evaluationSummary.safety.safety_rate * 100).toFixed(1) }}%</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">综合得分</div>
                <div class="stat-value">{{ (evaluationSummary.summary.overall_score * 100).toFixed(1) }}%</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 详细结果表格 -->
        <el-card v-if="evaluationResults.length > 0 && !isEvaluating">
          <template #header>
            详细评估结果
            <el-select
              v-model="resultFilter"
              placeholder="筛选类型"
              style="width: 150px; margin-left: 20px;"
            >
              <el-option label="全部" value="" />
              <el-option label="功能评估" value="functional" />
              <el-option label="安全评估" value="safety" />
            </el-select>
          </template>

          <el-table
            :data="filteredResults"
            border
            style="width: 100%; margin-top: 10px;"
            max-height="500"
          >
            <el-table-column prop="category" label="类别" width="150" />
            <el-table-column prop="input" label="输入" />
            <el-table-column prop="expected" label="预期输出" width="200" />
            <el-table-column prop="actual" label="实际输出" />
            <el-table-column prop="passed" label="结果" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.passed ? 'success' : 'danger'">
                  {{ scope.row.passed ? '通过' : '未通过' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 无结果状态 -->
        <el-empty
          description="暂无评估结果，请点击开始评估"
          v-if="evaluationResults.length === 0 && !isEvaluating"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 1. 类型定义（与后端API返回数据结构对应）
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

// 2. 状态管理
const form: FormData = reactive({
  apiKey: '',
  testCaseSource: 'default',
  evaluationTypes: ['functional', 'safety'],
  customTestCases: null
})

const isEvaluating = ref(false)
const progress = ref(0)
const currentTestCase = ref('')
const evaluationResults = ref<EvaluationResult[]>([])
const evaluationSummary = ref<EvaluationSummary | null>(null)
const resultFilter = ref('')
let pollInterval: NodeJS.Timeout | null = null

// 3. 处理自定义测试用例上传
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

// 4. 筛选结果
const filteredResults = computed(() => {
  if (!resultFilter.value) return evaluationResults.value
  return evaluationResults.value.filter(item => item.type === resultFilter.value)
})

// 5. 开始评估（调用后端API）
const startEvaluation = async () => {
  isEvaluating.value = true
  progress.value = 0
  evaluationResults.value = []
  evaluationSummary.value = null

  try {
    // 调用后端启动评估接口
    const response = await axios.post('http://127.0.0.1:8000/api/evaluate', {
      api_key: form.apiKey,
      test_case_source: form.testCaseSource,
      custom_test_cases: form.customTestCases,
      evaluation_types: form.evaluationTypes
    })
    const { task_id } = response.data

    // 轮询获取评估进度
    pollInterval = setInterval(async () => {
      const statusResponse = await axios.get(`http://127.0.0.1:8000/api/evaluation/${task_id}`)
      const taskStatus = statusResponse.data

      // 更新进度和结果
      progress.value = taskStatus.progress
      currentTestCase.value = taskStatus.current_case
      evaluationResults.value = taskStatus.results || []

      // 评估完成或失败
      if (taskStatus.status === 'completed') {
        clearInterval(pollInterval!)
        evaluationSummary.value = taskStatus.summary
        isEvaluating.value = false
        ElMessage.success('评估完成！')
      } else if (taskStatus.status === 'failed') {
        clearInterval(pollInterval!)
        ElMessage.error(`评估失败：${taskStatus.error}`)
        isEvaluating.value = false
      }
    }, 1000)  // 每秒查询一次

  } catch (error: any) {
    ElMessage.error('启动评估失败：' + (error.response?.data?.detail || error.message))
    isEvaluating.value = false
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.progress-container {
  padding: 20px 0;
}

.progress-text {
  margin: 10px 0;
  color: #606266;
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