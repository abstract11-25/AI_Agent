<template>
  <div class="app-container">
    <!-- 页面标题和用户信息 -->
    <div class="header-section glass">
      <div class="header-title">
        <h1>智能体评估工作台</h1>
        <p>配置评估参数、实时观察执行状态并查看多维度特征指标</p>
      </div>
      <el-dropdown @command="handleCommand" class="user-info">
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

    <!-- 主内容区 -->
    <el-row :gutter="24" style="margin-top: 20px;">
      <!-- 左侧：评估配置 -->
      <el-col :span="8">
        <el-card class="panel-card config-card glass">
          <template #header>
            <div class="config-header">
              <div class="config-title">
                <h2>评估配置</h2>
                <p>填写模型信息与评估参数即可开始测试</p>
              </div>
            </div>
          </template>

          <el-scrollbar max-height="calc(100vh - 220px)">
          <el-form :model="form" label-width="110px">
            <el-collapse v-model="activeConfigSections" class="config-collapse">
              <el-collapse-item title="基础配置" name="basic">
                <el-form-item label="服务商" required>
                  <el-select v-model="form.provider" placeholder="请选择服务商">
                    <el-option
                      v-for="item in providerOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>
            <el-form-item label="API密钥" required>
              <el-input
                v-model="form.apiKey"
                type="password"
                    :placeholder="apiKeyPlaceholder"
                clearable
              />
            </el-form-item>
                <el-form-item label="模型名称">
                  <el-input
                    v-model="form.model"
                    placeholder="例如：gpt-4o-mini / glm-4.5-flash"
                    clearable
                  />
                </el-form-item>
                <el-form-item label="Base URL">
                  <el-input
                    v-model="form.baseUrl"
                    placeholder="请输入接口地址"
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
              </el-collapse-item>

              <el-collapse-item title="高级配置" name="advanced">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item label="温度">
                      <el-input-number
                        v-model="form.temperature"
                        :step="0.1"
                        :min="0"
                        :max="2"
                        :precision="2"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="Max Tokens">
                      <el-input-number
                        v-model="form.maxTokens"
                        :min="1"
                        :max="4096"
                        :step="64"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="请求超时(s)">
                      <el-input-number
                        v-model="form.timeout"
                        :min="5"
                        :max="300"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="重试次数">
                      <el-input-number
                        v-model="form.maxRetries"
                        :min="0"
                        :max="5"
                        controls-position="right"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="额外请求头">
                  <el-input
                    v-model="form.extraHeaders"
                    type="textarea"
                    placeholder='示例：{"Authorization":"Bearer xxx"}'
                    autosize
                  />
                  <div class="text-help">可选，JSON 对象格式，会与默认请求头合并。</div>
                </el-form-item>

                <el-form-item label="额外请求体">
                  <el-input
                    v-model="form.extraBody"
                    type="textarea"
                    placeholder='示例：{"stream":false}'
                    autosize
                  />
                  <div class="text-help">可选，JSON 对象格式，会合并进请求 body。</div>
                </el-form-item>
              </el-collapse-item>

              <el-collapse-item title="特征评估配置" name="feature">
                <el-form-item label="启用特征评估">
                  <el-switch v-model="form.featureMetricsEnabled" />
                </el-form-item>
                <template v-if="form.featureMetricsEnabled">
                  <el-row :gutter="12">
                    <el-col :span="12">
                      <el-form-item label="真实正例总数">
                        <el-input-number
                          v-model="form.groundTruthTotal"
                          :min="0"
                          :controls="false"
                          placeholder="默认按用例数量"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="场景类型总数">
                        <el-input-number
                          v-model="form.totalSceneTypes"
                          :min="0"
                          :controls="false"
                          placeholder="例如：5"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="单主体基准耗时(s)">
                        <el-input-number
                          v-model="form.baselineSingleTaskTime"
                          :min="0"
                          :precision="3"
                          :controls="false"
                          placeholder="协同基准耗时"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                    <el-col :span="12">
                      <el-form-item label="基准适配成本">
                        <el-input-number
                          v-model="form.baselineAdaptationCost"
                          :min="0"
                          :precision="2"
                          :controls="false"
                          placeholder="例如：1.0"
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-col>
                  </el-row>
                  <el-form-item label="评估特性">
                    <el-checkbox-group v-model="form.selectedFeatures">
                      <el-checkbox
                        v-for="item in featureOptions"
                        :key="item.value"
                        :label="item.value"
                      >
                        {{ item.label }}
                      </el-checkbox>
                    </el-checkbox-group>
                    <div class="text-help">未选中的特性不会计算，对应的结果面板也会隐藏。</div>
                  </el-form-item>
                </template>
              </el-collapse-item>
            </el-collapse>

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
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- 右侧：评估结果（不变，新增对“取消”状态的处理） -->
      <el-col :span="16">
        <el-card v-if="agentInfo" class="panel-card glass">
          <template #header>当前智能体</template>
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="服务商">
              {{ providerLabel(agentInfo?.provider) }}
            </el-descriptions-item>
            <el-descriptions-item label="模型名称">
              {{ agentInfo?.model || '未指定' }}
            </el-descriptions-item>
            <el-descriptions-item label="Base URL">
              {{ agentInfo?.base_url || '未指定' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="panel-card glass">
          <el-tabs v-model="activeTab" class="result-tabs">
          <el-tab-pane label="执行状态" name="progress">
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
            <el-empty v-else description="暂无执行任务，请开始评估" />

            <el-card v-if="isEvaluating && realtimeResults.length > 0" class="history-card subtle-card">
              <template #header>实时回答记录</template>
              <div class="history-list">
                <div
                  v-for="(item, index) in realtimeResults"
                  :key="item.input + index"
                  class="history-item"
                >
                  <div class="history-title">
                    <el-tag :type="item.type === 'functional' ? 'success' : 'warning'" size="small">
                      {{ item.type === 'functional' ? '功能' : '安全' }}
                    </el-tag>
                    <span class="history-category">{{ item.category || '未分类' }}</span>
                  </div>
                  <div class="history-body">
                    <div class="history-label">测试输入：</div>
                    <div class="history-content">{{ item.input }}</div>
                  </div>
                  <div class="history-body">
                    <div class="history-label">智能体回答：</div>
                    <div class="history-content response">{{ item.actual || '无响应' }}</div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-tab-pane>

          <el-tab-pane label="评估结果" name="results">
            <template v-if="evaluationSummary || evaluationResults.length">
              <el-card v-if="evaluationSummary">
          <template #header>评估结果概览</template>
          <el-row :gutter="20">
            <el-col :span="6" v-if="evaluationSummary.functional">
              <div class="stat-card">
                <div class="stat-label">功能评估准确率</div>
                <div class="stat-value">{{ (evaluationSummary.functional.accuracy * 100).toFixed(1) }}%</div>
                      <div class="stat-subvalue">
                  通过 {{ evaluationSummary.functional.count }} 项
                </div>
              </div>
            </el-col>
            <el-col :span="6" v-if="evaluationSummary.safety">
              <div class="stat-card">
                <div class="stat-label">安全评估通过率</div>
                <div class="stat-value">{{ (evaluationSummary.safety.safety_rate * 100).toFixed(1) }}%</div>
                      <div class="stat-subvalue">
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
                      <div class="stat-subvalue">
                        平均单次：{{ evaluationSummary.average_case_time ? `${formatNumber(evaluationSummary.average_case_time)}s` : 'N/A' }}
                      </div>
              </div>
            </el-col>
          </el-row>
        </el-card>

              <el-card v-if="evaluationResults.length > 0" style="margin-top: 20px;">
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
            </template>
            <el-empty v-else description="暂无评估结果，请先完成评估任务" />
          </el-tab-pane>

          <el-tab-pane
            label="特征指标"
            name="features"
            :disabled="!basicFeatureMetrics && !(generalizationMetrics && (hasValues(generalizationMetrics?.adaptivity) || hasValues(generalizationMetrics?.robustness) || hasValues(generalizationMetrics?.portability) || hasValues(generalizationMetrics?.collaboration)))"
          >
            <template v-if="basicFeatureMetrics || (generalizationMetrics && (hasValues(generalizationMetrics?.adaptivity) || hasValues(generalizationMetrics?.robustness) || hasValues(generalizationMetrics?.portability) || hasValues(generalizationMetrics?.collaboration)))">
              <el-card v-if="basicFeatureMetrics" class="subtle-card">
                <template #header>基础特征指标</template>
                <el-descriptions :column="3" size="small" border>
                  <el-descriptions-item label="准确率">
                    {{ formatPercent(basicFeatureMetrics?.accuracy ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="召回率">
                    {{ formatPercent(basicFeatureMetrics?.recall ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="F1 值">
                    {{ formatPercent(basicFeatureMetrics?.f1_score ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="任务完成率">
                    {{ formatPercent(basicFeatureMetrics?.task_completion_rate ?? null) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="平均响应耗时">
                    {{ basicFeatureMetrics?.average_response_time !== null && basicFeatureMetrics?.average_response_time !== undefined ? `${formatNumber(basicFeatureMetrics?.average_response_time)}s` : 'N/A' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="通过/总用例">
                    {{ basicFeatureMetrics?.passed_cases ?? 0 }} / {{ basicFeatureMetrics?.total_cases ?? 0 }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <el-card
                v-if="generalizationMetrics && (hasValues(generalizationMetrics?.adaptivity) || hasValues(generalizationMetrics?.robustness) || hasValues(generalizationMetrics?.portability) || hasValues(generalizationMetrics?.collaboration))"
                style="margin-top: 20px;"
                class="subtle-card"
              >
                <template #header>通用化指标</template>
                <div class="metric-section" v-if="hasValues(generalizationMetrics?.adaptivity)">
                  <h4>适应性</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="训练场景完成率">
                      {{ formatPercent(generalizationMetrics?.adaptivity?.train_completion_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="非训练场景完成率">
                      {{ formatPercent(generalizationMetrics?.adaptivity?.non_train_completion_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="跨场景完成率偏差">
                      {{ generalizationMetrics?.adaptivity?.cross_scene_completion_deviation !== null && generalizationMetrics?.adaptivity?.cross_scene_completion_deviation !== undefined ? formatNumber(generalizationMetrics?.adaptivity?.cross_scene_completion_deviation, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="场景覆盖度">
                      {{ formatPercent(generalizationMetrics?.adaptivity?.scene_coverage ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="未知场景适配耗时">
                      {{ generalizationMetrics?.adaptivity?.unknown_scene_adaptation_time ? `${formatNumber(generalizationMetrics?.adaptivity?.unknown_scene_adaptation_time)}s` : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="覆盖场景类型">
                      <template v-if="generalizationMetrics?.adaptivity?.covered_scene_types?.length">
                        <el-tag
                          v-for="scene in generalizationMetrics?.adaptivity?.covered_scene_types"
                          :key="scene"
                          size="small"
                          style="margin-right: 4px; margin-bottom: 4px;"
                        >
                          {{ scene }}
                        </el-tag>
                      </template>
                      <span v-else>N/A</span>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="metric-section" v-if="hasValues(generalizationMetrics?.robustness)">
                  <h4>鲁棒性</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="异常输入错误率">
                      {{ formatPercent(generalizationMetrics?.robustness?.abnormal_input_error_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="高并发稳定性">
                      {{ generalizationMetrics?.robustness?.high_concurrency_stability !== null && generalizationMetrics?.robustness?.high_concurrency_stability !== undefined ? formatNumber(generalizationMetrics?.robustness?.high_concurrency_stability, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="环境波动容错率">
                      {{ formatPercent(generalizationMetrics?.robustness?.environment_fault_tolerance ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="异常输入样本数">
                      {{ generalizationMetrics?.robustness?.abnormal_case_count ?? 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="高并发样本数">
                      {{ generalizationMetrics?.robustness?.high_concurrency_case_count ?? 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="环境波动样本数">
                      {{ generalizationMetrics?.robustness?.environment_unstable_case_count ?? 0 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="metric-section" v-if="hasValues(generalizationMetrics?.portability)">
                  <h4>可移植性</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="跨环境部署成功率">
                      {{ formatPercent(generalizationMetrics?.portability?.cross_environment_success_rate ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="兼容性问题数">
                      {{ generalizationMetrics?.portability?.compatibility_issue_count ?? 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="适配成本系数">
                      {{ generalizationMetrics?.portability?.adaptation_cost_ratio !== null && generalizationMetrics?.portability?.adaptation_cost_ratio !== undefined ? formatNumber(generalizationMetrics?.portability?.adaptation_cost_ratio, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="兼容性清单覆盖率">
                      {{ formatPercent(generalizationMetrics?.portability?.compatibility_coverage ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="部署尝试次数">
                      {{ generalizationMetrics?.portability?.deployment_attempts ?? 0 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="metric-section" v-if="hasValues(generalizationMetrics?.collaboration)">
                  <h4>协作效率</h4>
                  <el-descriptions :column="2" size="small" border>
                    <el-descriptions-item label="信息交互准确率">
                      {{ formatPercent(generalizationMetrics?.collaboration?.information_accuracy ?? null) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="协同耗时差值">
                      {{ generalizationMetrics?.collaboration?.collaboration_time_delta !== null && generalizationMetrics?.collaboration?.collaboration_time_delta !== undefined ? `${formatNumber(generalizationMetrics?.collaboration?.collaboration_time_delta)}s` : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="协同贡献度">
                      {{ generalizationMetrics?.collaboration?.collaboration_contribution !== null && generalizationMetrics?.collaboration?.collaboration_contribution !== undefined ? formatNumber(generalizationMetrics?.collaboration?.collaboration_contribution, 4) : 'N/A' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="协作样本数">
                      {{ generalizationMetrics?.collaboration?.collaboration_case_count ?? 0 }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-card>
            </template>
            <el-empty v-else description="未启用或暂无特征评估结果" />
          </el-tab-pane>
        </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, ArrowDown } from '@element-plus/icons-vue'
import request from '../utils/request'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

// 1. 类型定义（新增任务ID和取消状态的适配）
interface FormData {
  provider: string
  apiKey: string
  model: string
  baseUrl: string
  temperature: number
  maxTokens: number
  timeout: number
  maxRetries: number
  extraHeaders: string
  extraBody: string
  featureMetricsEnabled: boolean
  selectedFeatures: string[]
  groundTruthTotal: number | null
  totalSceneTypes: number | null
  baselineSingleTaskTime: number | null
  baselineAdaptationCost: number | null
  testCaseSource: 'default' | 'custom'
  evaluationTypes: ('functional' | 'safety')[]
  customTestCases: Array<{
    type: 'functional' | 'safety'
    input: string
    expected: string
    category: string
  }> | null
}

interface ProviderOption {
  value: string
  label: string
  baseUrl?: string
  model?: string
  placeholder?: string
}

interface EvaluationResult {
  type: 'functional' | 'safety'
  category: string
  input: string
  expected: string
  actual: string
  passed: boolean
  duration?: number
  metadata?: Record<string, any>
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
  average_case_time?: number | null
  feature_metrics?: FeatureMetrics
}

interface FeatureMetrics {
  basic?: {
    accuracy?: number | null
    recall?: number | null
    f1_score?: number | null
    task_completion_rate?: number | null
    average_response_time?: number | null
    total_cases?: number
    passed_cases?: number
    total_duration?: number | null
  }
  generalization?: {
    adaptivity?: AdaptivityMetrics
    robustness?: RobustnessMetrics
    portability?: PortabilityMetrics
    collaboration?: CollaborationMetrics
  }
}

interface AdaptivityMetrics {
  train_completion_rate?: number | null
  non_train_completion_rate?: number | null
  cross_scene_completion_deviation?: number | null
  scene_coverage?: number | null
  covered_scene_types?: string[]
  unknown_scene_adaptation_time?: number | null
  scene_distribution?: Record<string, number>
}

interface RobustnessMetrics {
  abnormal_input_error_rate?: number | null
  high_concurrency_stability?: number | null
  environment_fault_tolerance?: number | null
  abnormal_case_count?: number
  high_concurrency_case_count?: number
  environment_unstable_case_count?: number
}

interface PortabilityMetrics {
  cross_environment_success_rate?: number | null
  compatibility_issue_count?: number | null
  adaptation_cost_ratio?: number | null
  compatibility_coverage?: number | null
  deployment_attempts?: number
}

interface CollaborationMetrics {
  information_accuracy?: number | null
  collaboration_time_delta?: number | null
  collaboration_contribution?: number | null
  collaboration_case_count?: number
}

// 2. 状态管理（新增任务ID存储）
const featureOptions = [
  { value: 'basic', label: '基础指标' },
  { value: 'adaptivity', label: '适应性' },
  { value: 'robustness', label: '鲁棒性' },
  { value: 'portability', label: '可移植性' },
  { value: 'collaboration', label: '协作效率' }
]
const defaultFeatures = featureOptions.map(option => option.value)
const providerOptions: ProviderOption[] = [
  {
    value: 'zhipu',
    label: '智谱 GLM',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
    model: 'glm-4.5-flash',
    placeholder: '请输入智谱 AI API Key'
  },
  {
    value: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1/chat/completions',
    model: 'gpt-4o-mini',
    placeholder: '请输入 OpenAI API Key'
  },
  {
    value: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1/chat/completions',
    model: 'deepseek-chat',
    placeholder: '请输入 DeepSeek API Key'
  },
  {
    value: 'moonshot',
    label: 'Moonshot',
    baseUrl: 'https://api.moonshot.cn/v1/chat/completions',
    model: 'moonshot-v1-8k',
    placeholder: '请输入 Moonshot API Key'
  },
  {
    value: 'qwen',
    label: '通义千问 (DashScope)',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
    model: 'qwen-plus',
    placeholder: '请输入 DashScope API Key'
  },
  {
    value: 'baichuan',
    label: '百川',
    baseUrl: 'https://api.baichuan-ai.com/v1/chat/completions',
    model: 'Baichuan2-Turbo',
    placeholder: '请输入百川 API Key'
  },
  {
    value: 'custom',
    label: '自定义兼容接口',
    baseUrl: '',
    model: '',
    placeholder: '请输入 API Key（若需要）'
  }
]

const form: FormData = reactive({
  provider: 'zhipu',
  apiKey: '',
  model: 'glm-4.5-flash',
  baseUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
  temperature: 0.3,
  maxTokens: 512,
  timeout: 60,
  maxRetries: 2,
  extraHeaders: '',
  extraBody: '',
  featureMetricsEnabled: true,
  selectedFeatures: [...defaultFeatures],
  groundTruthTotal: null,
  totalSceneTypes: null,
  baselineSingleTaskTime: null,
  baselineAdaptationCost: null,
  testCaseSource: 'default',
  evaluationTypes: ['functional', 'safety'],
  customTestCases: null
})

const providerPresetMap = providerOptions.reduce<Record<string, ProviderOption>>((acc, option) => {
  acc[option.value] = option
  return acc
}, {})

const providerLabel = (value?: string) => {
  if (!value) return '-'
  return providerPresetMap[value]?.label ?? value
}

const currentProviderOption = computed<ProviderOption | undefined>(() =>
  providerOptions.find(option => option.value === form.provider)
)

const apiKeyPlaceholder = computed(() => {
  const option = currentProviderOption.value
  if (!option) return '请输入 API Key'
  return option.placeholder || `请输入 ${option.label} API Key`
})

watch(
  () => form.provider,
  (newProvider) => {
    const newPreset = providerPresetMap[newProvider]
    if (newPreset) {
      form.baseUrl = newPreset.baseUrl ?? ''
      form.model = newPreset.model ?? ''
    }
  },
  { immediate: true }
)

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
interface AgentRuntimeInfo {
  provider?: string
  model?: string
  base_url?: string
}
const agentInfo = ref<AgentRuntimeInfo | null>(null)
const activeTab = ref<'progress' | 'results'>('progress')
const activeConfigSections = ref<string[]>(['basic'])

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

const realtimeResults = computed(() => evaluationResults.value.slice().reverse())

const featureMetrics = computed(() => evaluationSummary.value?.feature_metrics ?? null)
const basicFeatureMetrics = computed(() => featureMetrics.value?.basic ?? null)
const generalizationMetrics = computed(() => featureMetrics.value?.generalization ?? null)

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined) return 'N/A'
  return `${value.toFixed(2)}%`
}

const formatNumber = (value?: number | null, digits = 3) => {
  if (value === null || value === undefined) return 'N/A'
  return value.toFixed(digits)
}

const hasValues = (group?: Record<string, any> | null): boolean => {
  if (!group) return false
  return Object.values(group).some((value) => {
    if (value === null || value === undefined) return false
    if (Array.isArray(value)) return value.length > 0
    if (typeof value === 'object') return Object.keys(value as Record<string, any>).length > 0
    return true
  })
}

watch(
  () => form.featureMetricsEnabled,
  (enabled) => {
    if (enabled && form.selectedFeatures.length === 0) {
      form.selectedFeatures = [...defaultFeatures]
    }
  }
)

// 5. 开始评估（修改：记录任务ID）
const startEvaluation = async () => {
  isEvaluating.value = true
  progress.value = 0
  evaluationResults.value = []
  evaluationSummary.value = null
  taskId.value = ''  // 重置任务ID
  agentInfo.value = null
  activeTab.value = 'progress'

  const parseOptionalObject = (source: string, label: string) => {
    if (!source || !source.trim()) return undefined
    try {
      const parsed = JSON.parse(source)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed
      }
      throw new Error('需要是 JSON 对象')
    } catch (error: any) {
      ElMessage.error(`${label} 格式错误：${error?.message || error}`)
      throw error
    }
  }

  let extraHeaders: Record<string, any> | undefined
  let extraBody: Record<string, any> | undefined

  try {
    extraHeaders = parseOptionalObject(form.extraHeaders, '额外请求头')
    extraBody = parseOptionalObject(form.extraBody, '额外请求体')
  } catch {
    isEvaluating.value = false
    return
  }

  const agentPayload: Record<string, any> = {
    provider: form.provider,
      api_key: form.apiKey,
    model: form.model || undefined,
    base_url: form.baseUrl || undefined,
    temperature: form.temperature,
    max_tokens: form.maxTokens,
    timeout: form.timeout,
    max_retries: form.maxRetries
  }

  if (!agentPayload.model) {
    delete agentPayload.model
  }
  if (!agentPayload.base_url) {
    delete agentPayload.base_url
  }
  if (extraHeaders) {
    agentPayload.extra_headers = extraHeaders
  }
  if (extraBody) {
    agentPayload.extra_body = extraBody
  }

  const payload: Record<string, any> = {
    agent: agentPayload,
      test_case_source: form.testCaseSource,
      evaluation_types: form.evaluationTypes
  }

  if (form.testCaseSource === 'custom' && form.customTestCases) {
    payload.custom_test_cases = form.customTestCases
  }

  if (form.featureMetricsEnabled) {
    const featureConfigPayload: Record<string, any> = {
      enabled: true,
      ground_truth_total: form.groundTruthTotal ?? undefined,
      total_scene_types: form.totalSceneTypes ?? undefined,
      baseline_single_task_time: form.baselineSingleTaskTime ?? undefined,
      baseline_adaptation_cost: form.baselineAdaptationCost ?? undefined,
      features: form.selectedFeatures.length ? form.selectedFeatures : undefined
    }
    Object.keys(featureConfigPayload).forEach((key) => {
      if (featureConfigPayload[key] === undefined || featureConfigPayload[key] === null) {
        delete featureConfigPayload[key]
      }
    })
    if (Object.keys(featureConfigPayload).length > 0) {
      payload.feature_config = featureConfigPayload
    }
  }

  try {
    // 调用后端启动评估接口
    const response = await request.post('/api/evaluate', payload)
    taskId.value = response.data.task_id  // 保存任务ID
    agentInfo.value = {
      provider: agentPayload.provider,
      model: agentPayload.model,
      base_url: agentPayload.base_url
    }

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
        if (taskStatus.agent) {
          agentInfo.value = taskStatus.agent
        }

        // 处理所有可能的状态：完成、失败、取消
        if (taskStatus.status === 'completed') {
          clearInterval(pollInterval!)
          evaluationSummary.value = taskStatus.summary
          isEvaluating.value = false
          ElMessage.success('评估完成！')
          activeTab.value = 'results'
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
    agentInfo.value = null
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
  padding: 24px;
  min-height: 100vh;
  background: radial-gradient(circle at top, rgba(64, 158, 255, 0.08), transparent 55%), #f4f6fb;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  margin-bottom: 24px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(64, 158, 255, 0.18);
  backdrop-filter: blur(12px);
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.2), rgba(255, 255, 255, 0.82));
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.header-title h1 {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #1f2d3d;
}

.header-title p {
  margin: 6px 0 0;
  color: #5c6c83;
  font-size: 14px;
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
  padding: 10px 18px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: #1f2d3d;
  font-weight: 500;
  box-shadow: 0 8px 20px rgba(30, 73, 128, 0.16);
  transition: all 0.25s;
}

.user-dropdown:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(30, 73, 128, 0.22);
}

.panel-card {
  border-radius: 18px;
  border: none;
  box-shadow: 0 20px 50px rgba(15, 38, 67, 0.12);
  overflow: hidden;
}

.panel-card :deep(.el-card__header) {
  background: rgba(64, 158, 255, 0.06);
  border-bottom: 1px solid rgba(64, 158, 255, 0.15);
}

.config-card {
  position: sticky;
  top: 24px;
}

.config-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2d3d;
}

.config-header p {
  margin: 6px 0 0;
  color: #7a8aa0;
  font-size: 13px;
}

.progress-container {
  padding: 18px 0;
}

.progress-text {
  margin: 10px 0;
  color: #5c6c83;
  font-size: 14px;
}

.progress-info {
  margin-top: 15px;
}

.subtle-card {
  border-radius: 16px;
  border: 1px solid rgba(64, 158, 255, 0.12);
  box-shadow: 0 12px 30px rgba(64, 158, 255, 0.12);
  background: rgba(255, 255, 255, 0.9);
}

.progress-detail {
  margin-top: 15px;
  padding: 16px;
  background-color: rgba(64, 158, 255, 0.08);
  border-radius: 12px;
  border-left: 4px solid #409EFF;
}

.detail-item {
  margin-bottom: 12px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 600;
  color: #1f2d3d;
  display: inline-block;
  min-width: 100px;
  margin-right: 10px;
}

.detail-content {
  color: #5c6c83;
  word-break: break-word;
}

.response-content {
  color: #4e5c70;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px;
  border-radius: 12px;
  margin-top: 6px;
  max-height: 200px;
  overflow-y: auto;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(64, 158, 255, 0.12);
}

.stat-card {
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.12), rgba(255, 255, 255, 0.9));
  border-radius: 16px;
  padding: 18px;
  text-align: center;
  box-shadow: 0 12px 28px rgba(64, 158, 255, 0.1);
}

.stat-label {
  color: #5c6c83;
  font-size: 14px;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1890ff;
}

.stat-subvalue {
  color: #909399;
  font-size: 12px;
  margin-top: 6px;
}

.result-tabs {
  padding: 12px 4px 4px;
}

.result-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.result-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  padding: 0 22px;
  height: 42px;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.result-tabs :deep(.el-tabs__item.is-active) {
  font-weight: 600;
  color: #1890ff;
}

.result-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 999px;
}

.result-tabs :deep(.el-tab-pane) {
  padding-bottom: 8px;
}

.history-card {
  margin-top: 20px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 16px;
  padding: 14px 18px;
  border-left: 4px solid #409EFF;
  box-shadow: 0 8px 24px rgba(64, 158, 255, 0.1);
}

.history-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.history-category {
  color: #5c6c83;
  font-size: 13px;
}

.history-body {
  display: flex;
  margin-bottom: 8px;
}

.history-body:last-child {
  margin-bottom: 0;
}

.history-label {
  flex: 0 0 80px;
  color: #303133;
  font-weight: 600;
  font-size: 13px;
}

.history-content {
  flex: 1;
  color: #5c6c83;
  font-size: 13px;
  word-break: break-word;
  white-space: pre-wrap;
}

.history-content.response {
  background-color: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  padding: 8px 12px;
  line-height: 1.6;
  box-shadow: inset 0 0 0 1px rgba(233, 240, 255, 0.9);
}

.metric-section {
  margin-bottom: 20px;
}

.metric-section:last-child {
  margin-bottom: 0;
}

.metric-section h4 {
  margin-bottom: 10px;
  color: #1f2d3d;
  font-size: 15px;
  font-weight: 600;
}

.text-help {
  color: #7a8aa0;
  font-size: 12px;
  margin-top: 5px;
}

@media screen and (max-width: 1400px) {
  .config-card {
    position: static;
  }
}
</style>