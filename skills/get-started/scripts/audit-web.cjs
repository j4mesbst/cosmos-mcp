/* Run from your web project: node /absolute/path/audit-web.cjs .cosmos/audit.json */
const assert = require('node:assert/strict')
const { createHash } = require('node:crypto')
const fs = require('node:fs')
const path = require('node:path')
const { createRequire } = require('node:module')

const fromProject = createRequire(path.join(process.cwd(), 'package.json'))
const { chromium } = fromProject('playwright-core')
const { AxeBuilder } = fromProject('@axe-core/playwright')
const {measureVisualCheck, checkedValue} = require('./skill-checks.cjs')
const config = JSON.parse(fs.readFileSync(process.argv[2] === '-' ? 0 : process.argv[2], 'utf8'))
const url = new URL(config.url)
assert(['http:', 'https:'].includes(url.protocol) && ['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname), 'Start a local dev or preview server.')
assert(Array.isArray(config.steps) && config.steps.length && config.steps.some(step => ['visible', 'value', 'text', 'urlIncludes'].includes(step.action)),
  'Provide at least one executable assertion of the primary flow in steps.')
const output = '.cosmos/review'
fs.mkdirSync(output, { recursive: true })

async function run() {
  const options = process.env.COSMOS_CHROMIUM ? { executablePath: process.env.COSMOS_CHROMIUM } : {}
  const browser = await chromium.launch(options)
  const viewports = []
  const screenshots = {}
  try {
    for (const width of [390, 768, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' })
      const page = await context.newPage()
      page.setDefaultTimeout(5000)
      const errors = []
      page.on('pageerror', error => errors.push(error.message))
      page.on('console', event => { if (event.type() === 'error') errors.push(event.text()) })
      await page.goto(url.href)
      const buttons = config.shadcnButtons
        ? await require('./check-buttons.cjs').inspectButtons(page, config.shadcnButtons)
        : undefined
      if (buttons) assert(buttons.length && buttons.every(b => b.differences.length === 0), JSON.stringify(buttons))
      const designProbes = await require("./render-decisions.cjs").inspectDesign(page, config.designProbes)
      const referenceTargets = []
      for (const selector of config.referenceTargets || []) {
        const target = page.locator(selector).first()
        if (!await target.isVisible()) continue
        const bounds = await target.boundingBox()
        if (bounds && bounds.x < width && bounds.y < 900 &&
            bounds.x + bounds.width > 0 && bounds.y + bounds.height > 0) referenceTargets.push(selector)
      }
      const agentChat = config.agentChat
        ? await require('./audit-agent-chat.cjs').auditAgentChat(page, config.agentChat)
        : undefined
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
      const skillVisuals = []
      for (const rule of config.skillVisuals || []) {
        skillVisuals.push({skill:rule.skill, ...await page.evaluate(measureVisualCheck, rule)})
      }
      let draftCapture
      if (agentChat && config.agentChatDraft && width === 390) {
        const field = page.locator(config.agentChatDraft.selector)
        await field.fill(config.agentChatDraft.text)
        await field.blur()
        const draftFile = `${output}/agent-draft-390.png`
        await page.screenshot({ path: draftFile })
        screenshots[draftFile] = createHash('sha256').update(fs.readFileSync(draftFile)).digest('hex')
        draftCapture = {
          screenshot: draftFile,
          agentChat: await require('./audit-agent-chat.cjs').auditAgentChat(page, config.agentChat),
        }
        await page.reload()
      }
      let uiKit = config.uiKit ? await require('./audit-ui-kit.cjs').auditUIKit(page, config.uiKit) : undefined
      const file = `${output}/render-${width}.png`
      await page.screenshot({ path: file, fullPage: false })
      screenshots[file] = createHash('sha256').update(fs.readFileSync(file)).digest('hex')
      await page.keyboard.press('Tab')
      const keyboard = await page.locator(':focus-visible').evaluateAll(elements => elements.some(element => {
        const style = getComputedStyle(element)
        return (style.outlineStyle !== 'none' && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== 'none'
      }))
      const reducedMotion = await page.evaluate(() => {
        const moving = document.getAnimations().some(animation => animation.playState === 'running')
        return matchMedia('(prefers-reduced-motion: reduce)').matches && !moving
      })
      let primaryFlow = true
      const observations = new Map()
      let pressedKey = false
      let keyboardTransition = false
      try {
        for (const step of config.steps) {
          const element = step.selector ? page.locator(step.selector).first() : null
          switch (step.action) {
            case 'fill': pressedKey = false; await element.fill(step.value); break
            case 'press':
              pressedKey = config.requireKeyboardTransition &&
                ['Enter', 'Space', 'Escape', 'Tab', 'ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight'].includes(step.value)
              observations.clear()
              if (pressedKey) {
                for (const assertion of config.steps) {
                  try { observations.set(assertion, await checkedValue(page, assertion)) }
                  catch { observations.set(assertion, null) }
                }
              }
              await element.press(step.value)
              break
            case 'click': pressedKey = false; await element.click(); break
            case 'visible': await element.waitFor({ state: 'visible' }); break
            case 'value': assert.equal(await element.inputValue(), step.value); break
            case 'text': assert((await element.innerText()).includes(step.value)); break
            case 'capture-ui': {
              assert(uiKit, 'Enable uiKit before capturing interactive states.')
              const state = await require('./audit-ui-kit.cjs').auditUIKit(page, config.uiKit)
              uiKit.controls.push(...state.controls)
              uiKit.slots = [...new Set([...uiKit.slots, ...state.slots])]
              break
            }
            case 'urlIncludes': assert(page.url().includes(step.value)); break
            default: throw Error('Unknown audit step ' + step.action)
          }
          if (pressedKey && ['visible', 'text', 'urlIncludes', 'value'].includes(step.action) &&
              observations.get(step) === false && await checkedValue(page, step) === true) {
            keyboardTransition = true
          }
        }
      } catch (error) {
        primaryFlow = false
        console.error(width, error.message)
      }
      const row = { width, screenshot: file, buttons, designProbes, referenceTargets, agentChat, uiKit, skillVisuals, keyboardTransition, overflow,
        axeViolations: axe.violations.length, keyboard, reducedMotion, primaryFlow, errors: errors.length,
        violations: axe.violations.map(item => item.id) }
      viewports.push(row)
      if (draftCapture) viewports.push({ ...row, ...draftCapture })
      await context.close()
    }
  } finally {
    await browser.close()
  }
  const report = { schema: 'cosmos-browser-1', viewports, screenshots }
  fs.writeFileSync(`${output}/browser-report.json`, JSON.stringify(report, null, 2) + '\n')
  console.log(JSON.stringify(report))
  if (viewports.some(r => r.overflow || r.axeViolations || !r.keyboard || !r.reducedMotion || !r.primaryFlow || r.errors || r.skillVisuals.some(check => !check.pass) ||
    (config.requireKeyboardTransition && !r.keyboardTransition))) {
    process.exitCode = 1
  }
}

run().catch(error => { console.error(error); process.exitCode = 1 })
