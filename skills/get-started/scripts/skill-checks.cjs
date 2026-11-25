function measureVisualCheck({selector, property, operator, value}) {
  const element = document.querySelector(selector)
  const style = element && getComputedStyle(element)
  const actual = style ? style.getPropertyValue(property).trim() : ''
  const visible = Boolean(element?.checkVisibility() && element.getClientRects().length)
  let pass = visible && actual === value
  if (operator === 'min-px') {
    pass = visible && actual.endsWith('px') && parseFloat(actual) >= Number(value)
  }
  return {selector, property, operator, value, actual, pass}
}

async function checkedValue(page, step) {
  const element = step.selector ? page.locator(step.selector).first() : null
  switch (step.action) {
    case 'urlIncludes': return page.url().includes(step.value)
    case 'visible': return element.isVisible()
    case 'value': return (await element.count()) > 0 && (await element.inputValue()) === step.value
    case 'text': return (await element.count()) > 0 && (await element.innerText()).includes(step.value)
    default: return null
  }
}

module.exports = {measureVisualCheck, checkedValue}
