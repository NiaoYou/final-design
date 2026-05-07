/**
 * take_screenshots.js  (V3 — 完整交互版)
 * =============================================
 * 系统页面路由（frontend/src/router/index.ts）：
 *   /        → HomeView      (首页 KPI，自动加载)
 *   /import  → ImportView    (数据导入)
 *   /result  → ResultDashboardView
 *               ├─ PCA 校正前后对比（自动加载）
 *               ├─ 差异分析    → 需点击「运行分析」按钮
 *               ├─ 通路富集    → 需点击「运行富集分析」按钮（KEGG API ≈30s）
 *               └─ MetaKG 图  → 自动加载，力导向需等收敛
 *
 * 运行：node thesis/scripts/take_screenshots.js
 * 前置：backend :8000 + frontend :5173 均已启动
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = 'http://localhost:5173';
const OUT_DIR = path.resolve(__dirname, '../figures/screenshots');
fs.mkdirSync(OUT_DIR, { recursive: true });

const VIEWPORT = { width: 1600, height: 1000 };

// ── 辅助函数 ───────────────────────────────────────────────────────────────

async function idle(page, timeout = 10000) {
  await page.waitForLoadState('networkidle', { timeout }).catch(() => {});
}

async function shot(page, filename, msg = '') {
  const outPath = path.join(OUT_DIR, filename);
  await page.screenshot({ path: outPath });
  const kb = (fs.statSync(outPath).size / 1024).toFixed(0);
  const flag = kb < 30 ? ' ⚠️ 可能为空白' : ' ✅';
  console.log(`  [saved] ${filename}  ${kb} KB${flag}${msg ? '  ' + msg : ''}`);
  return Number(kb);
}

// 等待某文字的按钮出现并点击，返回是否成功
async function clickButton(page, text, timeout = 8000) {
  try {
    const btn = page.locator(`button:has-text("${text}")`).first();
    await btn.waitFor({ state: 'visible', timeout });
    await btn.click();
    return true;
  } catch {
    // 备用：el-button
    try {
      const btn = page.locator(`.el-button:has-text("${text}")`).first();
      await btn.waitFor({ state: 'visible', timeout: 3000 });
      await btn.click();
      return true;
    } catch {
      console.log(`    ⚠️ 未找到按钮: "${text}"`);
      return false;
    }
  }
}

// 等待某元素出现（超时则静默），用于等待图表渲染
async function waitFor(page, selector, timeout = 30000) {
  await page.waitForSelector(selector, { timeout }).catch(() => {});
}

// 滚动到某元素位置
async function scrollTo(page, selector, offset = -80) {
  const el = await page.$(selector).catch(() => null);
  if (el) {
    const box = await el.boundingBox();
    if (box) {
      await page.evaluate((y) => window.scrollTo({ top: y, behavior: 'instant' }), box.y + offset);
      await page.waitForTimeout(300);
    }
  }
}

// 等待文字「消失」（即加载中状态结束）
async function waitForTextGone(page, text, timeout = 60000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const visible = await page.locator(`text="${text}"`).isVisible().catch(() => false);
    if (!visible) return true;
    await page.waitForTimeout(500);
  }
  return false;
}

// ── 主流程 ─────────────────────────────────────────────────────────────────

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  // ==========================================================================
  // 图 4-7  首页 KPI 概览  /
  // ==========================================================================
  console.log('\n[图 4-7] 首页 KPI...');
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  await idle(page);
  // 等待 KPI 卡片数值填入（el-card 或含数字的 span 出现）
  await waitFor(page, '.kpi-row, .el-statistic, [class*="kpi"]', 6000);
  await page.waitForTimeout(2000);
  await shot(page, 'fig_4_7_dashboard.png');

  // ==========================================================================
  // 图 4-8  数据导入页  /import
  // ==========================================================================
  console.log('\n[图 4-8] 数据导入页...');
  await page.goto(`${BASE}/import`, { waitUntil: 'domcontentloaded' });
  await idle(page);
  await page.waitForTimeout(1500);
  await shot(page, 'fig_4_8_import_mapping.png');

  // ==========================================================================
  // 进入 /result 页，后续多张截图都在这里
  // ==========================================================================
  console.log('\n[/result] 加载结果展示页...');
  await page.goto(`${BASE}/result`, { waitUntil: 'domcontentloaded' });
  await idle(page, 15000);
  await page.waitForTimeout(3000);

  // ==========================================================================
  // 图 4-9  PCA 校正前后对比（自动加载）
  // ==========================================================================
  console.log('\n[图 4-9] PCA 对比...');
  // 滚到 PCA 区域 —— section 里有 .pca-image-panel 或图片
  await scrollTo(page, 'section:has(img), .pca-image-panel, img[src*="pca"]', -120);
  await page.waitForTimeout(2000);
  // 等图片真正渲染出来
  await waitFor(page, 'img', 8000);
  await page.waitForTimeout(1500);
  await shot(page, 'fig_4_9_pca_compare.png');

  // ==========================================================================
  // 图 4-10  差异代谢物火山图（需点击「运行分析」）
  // ==========================================================================
  console.log('\n[图 4-10] 差异分析...');
  // 找到差异分析区块
  await scrollTo(page, 'section:has(.volcano), section:has-text("差异代谢物分析")', -80);
  await page.waitForTimeout(800);

  // 确保下拉框已加载（组别选项）
  await waitFor(page, '.volcano .el-select, .volcano select', 8000);
  await page.waitForTimeout(500);

  // 点击「运行分析」
  const clickedVolcano = await clickButton(page, '运行分析');
  if (clickedVolcano) {
    console.log('    → 已点击「运行分析」，等待结果...');
    // 等火山图 canvas 或散点出现
    await waitFor(page, '.volcano__chart canvas, .volcano canvas', 20000);
    await page.waitForTimeout(2000);
  }
  await scrollTo(page, 'section:has(.volcano)', -80);
  await page.waitForTimeout(500);
  await shot(page, 'fig_4_10_volcano_table.png');

  // ==========================================================================
  // 图 4-11  KEGG 通路富集气泡图（需点击「运行富集分析」，KEGG API 约 30s）
  // ==========================================================================
  console.log('\n[图 4-11] 通路富集（KEGG，首次约需 30s）...');
  await scrollTo(page, 'section:has(.pe), section:has-text("通路富集分析")', -80);
  await page.waitForTimeout(800);

  await waitFor(page, '.pe .el-select, .pe select', 8000);
  await page.waitForTimeout(500);

  const clickedEnrich = await clickButton(page, '运行富集分析');
  if (clickedEnrich) {
    console.log('    → 已点击「运行富集分析」，等待 KEGG API（最多 60s）...');
    // 等气泡图 canvas 出现，最多等 60 秒
    await waitFor(page, '.pe__chart canvas', 65000);
    await page.waitForTimeout(2000);
  }
  await scrollTo(page, 'section:has(.pe)', -80);
  await page.waitForTimeout(500);
  await shot(page, 'fig_4_11_kegg_bubble.png');

  // ==========================================================================
  // 图 4-12  MetaKG 力导向全图（自动加载，等力导向收敛）
  // ==========================================================================
  console.log('\n[图 4-12] MetaKG 力导向图...');
  await scrollTo(page, 'section:has-text("MetaKG"), .metakg, [class*="metakg"]', -80);
  await page.waitForTimeout(500);
  // MetaKG 是 onMounted 自动加载，等 canvas 出现后再等力导向收敛
  await waitFor(page, '[class*="metakg"] canvas, .metakg canvas', 15000);
  await page.waitForTimeout(6000);  // 力导向收敛
  await shot(page, 'fig_4_12_metakg_force.png');

  // ==========================================================================
  // 图 3-8  MetaKG Benchmark 子图（同一 MetaKG 区域，确保在 Benchmark 数据集下）
  // ==========================================================================
  console.log('\n[图 3-8] MetaKG Benchmark 子图...');
  // 确认当前是 benchmark 数据集（页面初始默认就是）；再等几秒让布局稳定
  await page.waitForTimeout(3000);
  await shot(page, 'fig_3_8_metakg_subgraph.png');

  await browser.close();

  // ── 汇总验证 ────────────────────────────────────────────────────────────
  console.log('\n══ 截图尺寸验证 ══');
  const files = [
    'fig_4_7_dashboard.png',
    'fig_4_8_import_mapping.png',
    'fig_4_9_pca_compare.png',
    'fig_4_10_volcano_table.png',
    'fig_4_11_kegg_bubble.png',
    'fig_4_12_metakg_force.png',
    'fig_3_8_metakg_subgraph.png',
  ];
  let allOk = true;
  for (const f of files) {
    const p = path.join(OUT_DIR, f);
    if (fs.existsSync(p)) {
      const kb = Math.round(fs.statSync(p).size / 1024);
      const ok = kb >= 30;
      if (!ok) allOk = false;
      console.log(`  ${ok ? '✅' : '⚠️ '} ${f}: ${kb} KB`);
    } else {
      allOk = false;
      console.log(`  ❌ ${f}: 未生成`);
    }
  }
  console.log(allOk ? '\n✅ 全部截图正常' : '\n⚠️ 部分截图可能为空白，建议检查');
  console.log('保存路径：', OUT_DIR);
})();
