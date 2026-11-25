// Evaluate product-specific decisions on the visible page before interaction.
async function inspectDesign(page, spec) {
  const results = []
  for (const key of ['composition', 'copy', 'token']) {
    const probe = spec?.[key]
    if (!probe?.selector) throw Error('Specify designProbes.' + key + '.selector')
    const element = page.locator(probe.selector).first()
    await element.waitFor({state:'visible', timeout:5000})
    const result = await element.evaluate((el, {key, probe}) => {
      const clean = text => text.replace(/\s+/g, ' ').trim()
      if (key !== 'token') {
        if (!probe.text?.trim()) throw Error('Specify expected visible text for ' + key)
        return {actual:clean(el.innerText), expected:clean(probe.text)}
      }
      if (!/^--cosmos-[a-z-]+$/.test(probe.token) ||
          !['color','background-color','border-left-color','border-top-color'].includes(probe.property)) {
        throw Error('Choose a generated color token and a rendered CSS color property.')
      }
      const computed = getComputedStyle(el)
      const value = computed.getPropertyValue(probe.token).trim()
      if (!value) throw Error('Generated token missing: ' + probe.token)
      const sample = document.createElement('span')
      sample.style.color = value
      el.parentNode.append(sample)
      try { return {actual:computed.getPropertyValue(probe.property), expected:getComputedStyle(sample).color} }
      finally { sample.remove() }
    }, {key, probe})
    if (result.actual !== result.expected) throw Error(key + ': ' + JSON.stringify(result))
    results.push({key, ...probe, ...result})
  }
  return results
}
module.exports = {inspectDesign}
