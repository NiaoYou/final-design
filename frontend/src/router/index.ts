import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
          meta: { title: '首页' },
        },
        {
          path: 'import',
          name: 'import',
          component: () => import('@/views/ImportView.vue'),
          meta: { title: '数据导入' },
        },
        {
          path: 'task',
          name: 'task',
          component: () => import('@/views/TaskConfigView.vue'),
          meta: { title: '参数配置' },
        },
        {
          path: 'result',
          name: 'result',
          component: () => import('@/views/ResultDashboardView.vue'),
          meta: { title: '结果展示' },
        },
        {
          path: 'history',
          name: 'history',
          component: () => import('@/views/HistoryView.vue'),
          meta: { title: '历史任务' },
        },
      ],
    },
    // 独立截图专用页面（无 Layout，全屏）
    {
      path: '/screenshot/metakg',
      name: 'screenshot-metakg',
      component: () => import('@/views/MetaKGScreenshotView.vue'),
      meta: { title: 'MetaKG 截图' },
    },
    {
      path: '/screenshot/volcano',
      name: 'screenshot-volcano',
      component: () => import('@/views/VolcanoScreenshotView.vue'),
      meta: { title: '火山图截图' },
    },
    {
      path: '/screenshot/enrichment',
      name: 'screenshot-enrichment',
      component: () => import('@/views/EnrichmentScreenshotView.vue'),
      meta: { title: 'KEGG 富集截图' },
    },
  ],
})

router.afterEach((to) => {
  const base = (to.meta.title as string) || ''
  document.title = base ? `${base} · 代谢组学数据处理平台` : '代谢组学数据处理平台'
})

export default router
