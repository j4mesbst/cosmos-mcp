// Build reference controls from the pinned new-york-v4 registry classes.
const fs = require('node:fs')
const path = require('node:path')
const source = fs.readFileSync(path.join(__dirname, '../references/components/button.tsx'), 'utf8')
const base = source.match(/buttonVariants = cva\(\s*"([^"]+)"/)[1]
const properties = ['backgroundColor', 'color', 'height', 'borderRadius', 'borderTopWidth',
  'borderTopColor', 'paddingLeft', 'paddingRight', 'fontSize', 'fontWeight', 'boxShadow', 'opacity']
function choices(name) {
  const block = source.split(name + ': {')[1].split('},')[0]
  return Object.fromEntries([...block.matchAll(/["']?([\w-]+)["']?:\s*"([^"]+)"/g)].map(m => [m[1], m[2]]))
}
const variants = choices('variant'), sizes = choices('size')

async function inspectButtons(page, selector) {
  return page.locator(selector).evaluateAll((nodes, {base, variants, sizes, properties}) => {
    return nodes.filter(el => el.getClientRects().length && getComputedStyle(el).visibility === 'visible').map(el => {
      const {variant, size, slot} = el.dataset
      if (slot !== 'button' || !variants[variant] || !sizes[size]) throw Error('Expected a shadcn Button: ' + el.textContent)
      const ref = document.createElement(el.tagName)
      ref.innerHTML = el.innerHTML
      ref.className = [base, variants[variant], sizes[size]].join(' ')
      ref.toggleAttribute('disabled', el.matches(':disabled'))
      ref.style.position = 'absolute'
      ref.style.visibility = 'hidden'
      document.body.append(ref)
      try {
        const actual = getComputedStyle(el), expected = getComputedStyle(ref)
        const differences = properties.filter(key => actual[key] !== expected[key])
        if (!['inline-flex', 'flex'].includes(actual.display) || actual.borderRadius === '0px') differences.push('missing utility styles')
        return {label: el.getAttribute('aria-label') || el.textContent.trim(), variant, size, differences}
      } finally { ref.remove() }
    })
  }, {base, variants, sizes, properties})
}
module.exports = {inspectButtons}
