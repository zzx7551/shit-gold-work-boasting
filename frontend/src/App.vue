<script setup>
import { computed, reactive, ref } from 'vue'

const SITE_TITLE = '一坨屎都能包装成金子的找工作包装网站'

const modes = [
  { value: 'resume', label: '简历包装' },
  { value: 'interview', label: '面试话术' }
]

const mode = ref('resume')
const interviewInput = ref('我啥也不会')
const interviewOutput = ref('')
const loading = ref(false)
const error = ref('')
const exportingPdf = ref(false)

const resume = reactive({
  avatar: '',
  name: '张三',
  title: '产品运营 / 项目协调',
  phone: '138-0000-0000',
  email: 'demo@example.com',
  location: '上海',
  summary:
    '具备较强的信息整理、跨部门沟通和执行推进能力，能够围绕业务目标拆解任务并推动结果落地。',
  skills: '需求沟通 / 进度跟踪 / 数据整理 / 文档沉淀 / 跨部门协作',
  experience: [
    {
      id: 1,
      time: '2024.03 - 至今',
      organization: '某某公司',
      role: '项目协调 / 运营支持',
      description:
        '负责日常项目进度跟进，协调相关同事按节点提交材料；整理过程数据和表格，输出阶段性复盘文档。'
    }
  ],
  projects: [
    {
      id: 1,
      time: '2024.05 - 2024.08',
      name: '部门流程优化项目',
      role: '项目协助',
      description:
        '协助完成部门流程优化项目，梳理关键节点、明确责任分工，并推动信息同步机制落地。'
    }
  ],
  education: '某某大学 / 本科 / 2020-2024',
  selfEvaluation:
    '做事认真稳定，沟通反馈及时，能够在不确定任务中主动补位，持续提升团队协作效率。'
})

const canTransform = computed(() => interviewInput.value.trim().length > 0 && !loading.value)

let experienceId = 2
let projectId = 2

async function transformText() {
  if (!canTransform.value) return
  loading.value = true
  error.value = ''
  interviewOutput.value = ''

  try {
    const response = await fetch('/api/transform/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: interviewInput.value, mode: 'interview' })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error || '生成失败')
    interviewOutput.value = data.result
  } catch (err) {
    error.value = err.message || '后端暂时没有响应'
  } finally {
    loading.value = false
  }
}

function handleEnter(event) {
  if (!event.shiftKey) {
    event.preventDefault()
    transformText()
  }
}

function uploadAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    resume.avatar = String(reader.result || '')
  }
  reader.readAsDataURL(file)
}

function addExperience() {
  resume.experience.push({
    id: experienceId++,
    time: '',
    organization: '',
    role: '',
    description: ''
  })
}

function removeExperience(id) {
  if (resume.experience.length <= 1) return
  const index = resume.experience.findIndex((item) => item.id === id)
  if (index !== -1) resume.experience.splice(index, 1)
}

function addProject() {
  resume.projects.push({
    id: projectId++,
    time: '',
    name: '',
    role: '',
    description: ''
  })
}

function removeProject(id) {
  if (resume.projects.length <= 1) return
  const index = resume.projects.findIndex((item) => item.id === id)
  if (index !== -1) resume.projects.splice(index, 1)
}

async function exportPdf() {
  exportingPdf.value = true
  try {
    const response = await fetch('/api/resume/export-pdf/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume })
    })
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.error || 'PDF 导出失败')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${resume.name || 'resume'}-简历.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (err) {
    alert(err.message || 'PDF 导出失败')
  } finally {
    exportingPdf.value = false
  }
}
</script>

<template>
  <main class="app-shell">
    <header class="top-nav no-print">
      <nav class="module-nav" aria-label="功能模块">
        <button
          v-for="item in modes"
          :key="item.value"
          :class="{ active: mode === item.value }"
          type="button"
          @click="mode = item.value"
        >
          {{ item.label }}
        </button>
      </nav>
      <span class="nav-link">{{ SITE_TITLE }}</span>
    </header>

    <section v-if="mode === 'interview'" class="search-stage">
      <h1>{{ SITE_TITLE }}</h1>
      <p class="tagline">输入朴素表达，生成更适合面试场景的高阶说法</p>

      <div class="search-box">
        <textarea
          v-model="interviewInput"
          rows="1"
          :disabled="loading"
          placeholder="输入你的大白话，比如：我啥也不会"
          @keydown.enter="handleEnter"
        />
        <button type="button" :disabled="!canTransform" @click="transformText">
          <span v-if="loading" class="button-spinner" aria-hidden="true"></span>
          {{ loading ? '生成中' : '包装一下' }}
        </button>
      </div>

      <section class="result-panel" aria-live="polite">
        <div class="result-head">
          <strong>包装后的内容</strong>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <div v-else-if="loading" class="loading-panel">
          <div class="loader-ring" aria-hidden="true"></div>
          <div>
            <strong>正在生成包装句子<span class="loading-dots"></span></strong>
            <p>正在把原话整理成更适合面试的表达，请稍等。</p>
          </div>
        </div>
        <p v-else-if="interviewOutput" class="result-text">{{ interviewOutput }}</p>
        <p v-else class="empty-text">
          示例：我啥也不会 → 我的学习能力非常强，心态开放，执行稳定，具备高成长潜力。
        </p>
      </section>
    </section>

    <section v-else class="resume-workspace">
      <div class="resume-editor no-print">
        <div class="section-title">
          <h1>简历包装</h1>
          <p>按固定框架填内容，右侧实时生成简历预览。</p>
        </div>

        <label class="upload-field">
          <span>头像 / 证件照</span>
          <input type="file" accept="image/*" @change="uploadAvatar" />
        </label>

        <div class="form-grid">
          <label>
            <span>姓名</span>
            <input v-model="resume.name" />
          </label>
          <label>
            <span>求职方向</span>
            <input v-model="resume.title" />
          </label>
          <label>
            <span>电话</span>
            <input v-model="resume.phone" />
          </label>
          <label>
            <span>邮箱</span>
            <input v-model="resume.email" />
          </label>
          <label>
            <span>城市</span>
            <input v-model="resume.location" />
          </label>
        </div>

        <label>
          <span>个人优势</span>
          <textarea v-model="resume.summary" rows="4" />
        </label>
        <label>
          <span>核心技能</span>
          <textarea v-model="resume.skills" rows="3" />
        </label>
        <div class="repeatable-group">
          <div class="repeatable-head">
            <span>工作 / 实习经历</span>
            <button type="button" @click="addExperience">添加</button>
          </div>
          <div
            v-for="(item, index) in resume.experience"
            :key="item.id"
            class="repeatable-card"
          >
            <div class="repeatable-card-head">
              <strong>经历 {{ index + 1 }}</strong>
              <button
                type="button"
                :disabled="resume.experience.length <= 1"
                @click="removeExperience(item.id)"
              >
                删除
              </button>
            </div>
            <div class="form-grid">
              <label>
                <span>时间</span>
                <input v-model="item.time" placeholder="例如：2024.03 - 至今" />
              </label>
              <label>
                <span>公司 / 组织</span>
                <input v-model="item.organization" placeholder="例如：某某公司" />
              </label>
              <label>
                <span>岗位 / 角色</span>
                <input v-model="item.role" placeholder="例如：运营助理" />
              </label>
            </div>
            <label>
              <span>经历描述</span>
              <textarea v-model="item.description" rows="4" />
            </label>
          </div>
        </div>

        <div class="repeatable-group">
          <div class="repeatable-head">
            <span>项目经历</span>
            <button type="button" @click="addProject">添加</button>
          </div>
          <div v-for="(item, index) in resume.projects" :key="item.id" class="repeatable-card">
            <div class="repeatable-card-head">
              <strong>项目 {{ index + 1 }}</strong>
              <button
                type="button"
                :disabled="resume.projects.length <= 1"
                @click="removeProject(item.id)"
              >
                删除
              </button>
            </div>
            <div class="form-grid">
              <label>
                <span>时间</span>
                <input v-model="item.time" placeholder="例如：2024.05 - 2024.08" />
              </label>
              <label>
                <span>项目名称</span>
                <input v-model="item.name" placeholder="例如：流程优化项目" />
              </label>
              <label>
                <span>项目角色</span>
                <input v-model="item.role" placeholder="例如：项目协助" />
              </label>
            </div>
            <label>
              <span>项目描述</span>
              <textarea v-model="item.description" rows="4" />
            </label>
          </div>
        </div>
        <label>
          <span>教育经历</span>
          <textarea v-model="resume.education" rows="2" />
        </label>
        <label>
          <span>自我评价</span>
          <textarea v-model="resume.selfEvaluation" rows="3" />
        </label>

        <button class="pdf-button" type="button" :disabled="exportingPdf" @click="exportPdf">
          {{ exportingPdf ? '正在导出...' : '导出 PDF' }}
        </button>
      </div>

      <article class="resume-preview">
        <header class="resume-header">
          <div>
            <h2>{{ resume.name || '姓名' }}</h2>
            <p>{{ resume.title || '求职方向' }}</p>
            <ul>
              <li>{{ resume.phone || '电话' }}</li>
              <li>{{ resume.email || '邮箱' }}</li>
              <li>{{ resume.location || '城市' }}</li>
            </ul>
          </div>
          <div class="avatar-box">
            <img v-if="resume.avatar" :src="resume.avatar" alt="头像" />
            <span v-else>照片</span>
          </div>
        </header>

        <section>
          <h3>个人优势</h3>
          <p>{{ resume.summary }}</p>
        </section>
        <section>
          <h3>核心技能</h3>
          <p>{{ resume.skills }}</p>
        </section>
        <section>
          <h3>工作 / 实习经历</h3>
          <div v-for="item in resume.experience" :key="item.id" class="resume-entry">
            <div class="resume-entry-head">
              <strong>{{ item.organization || '公司 / 组织' }}</strong>
              <span>{{ item.time || '时间' }}</span>
            </div>
            <em>{{ item.role || '岗位 / 角色' }}</em>
            <p>{{ item.description || '经历描述' }}</p>
          </div>
        </section>
        <section>
          <h3>项目经历</h3>
          <div v-for="item in resume.projects" :key="item.id" class="resume-entry">
            <div class="resume-entry-head">
              <strong>{{ item.name || '项目名称' }}</strong>
              <span>{{ item.time || '时间' }}</span>
            </div>
            <em>{{ item.role || '项目角色' }}</em>
            <p>{{ item.description || '项目描述' }}</p>
          </div>
        </section>
        <section>
          <h3>教育经历</h3>
          <p>{{ resume.education }}</p>
        </section>
        <section>
          <h3>自我评价</h3>
          <p>{{ resume.selfEvaluation }}</p>
        </section>
      </article>
    </section>
  </main>
</template>
