// Run against the local, served fixture only.
const fs = require('node:fs')
const path = require('node:path')
const { createRequire } = require('node:module')
const {chromium} = createRequire(path.join(process.cwd(), 'package.json'))('playwright-core')
const {auditAgentChat} = require('../scripts/audit-agent-chat.cjs')
const config = require('./fixture/audit.json')

async function sample() {
  const options = process.env.COSMOS_CHROMIUM ? {executablePath: process.env.COSMOS_CHROMIUM} : {}
  const browser = await chromium.launch(options)
  try {
    const context = await browser.newContext({viewport: {width:390, height:900}})
    const page = await context.newPage()
    await page.goto(config.url)
    await page.locator('#draft').fill('Repère · Passerelle nord')
    await page.locator('#computer').focus()
    await page.locator('#computer').blur()
    const results = { restored:await auditAgentChat(page, config.agentChat) }
    const mutations = {
      'send-inside': () => document.querySelector('.entry').append(document.querySelector('#send')),
      'white-canvas': () => { document.querySelector('#chat').style.background = 'beige' },
      'header-without-divider': () => { document.querySelector('.toolbar').style.borderBottom = '1px solid #555' },
      'agent-avatar': () => { document.querySelector('.toolbar').append(document.querySelector('#avatar')) },
      'message-bubble': () => { document.querySelector('#timeline').style.justifyContent = 'flex-start' },
    }
    for (const [key, mutate] of Object.entries(mutations)) {
      await page.reload()
      await page.evaluate(mutate)
      results[key] = await auditAgentChat(page, config.agentChat)
    }
    fs.writeFileSync('.cosmos/review/regressions.json', JSON.stringify(results, null, 2))
  } finally {
    await browser.close()
  }
}
sample().catch(error => { console.error(error); process.exitCode = 1 })
