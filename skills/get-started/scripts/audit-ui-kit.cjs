async function auditUIKit(page, { heroui, logoSlugs }) {
  return page.evaluate(async ({ heroui, logoSlugs }) => {
    const visible = element => {
      if (!element.checkVisibility({ opacityProperty:true, visibilityProperty:true }) || element.closest('[aria-hidden=true], [inert]')) return false
      const bounds = element.getBoundingClientRect()
      for (let item = element; item && item !== document.body; item = item.parentElement) {
        const style = getComputedStyle(item)
        if (parseFloat(style.width) <= 1 && parseFloat(style.height) <= 1 &&
            (style.clip !== 'auto' || style.clipPath !== 'none')) return false
      }
      return bounds.width > 0 && bounds.height > 0
    }
    const interactive = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [role=switch], [role=checkbox], [role=radio], [role=tab], [role=combobox], [role=slider], [role=link]'
    const recognized = /^(button|link|close-button|switch|switch-control|input|text-field|text-area|checkbox|radio|select|slider|toggle-button|tabs|accordion-trigger|modal-close-trigger|popover-trigger|dropdown-trigger|list-box-item)(-|$)/
    const controls = heroui ? [...document.querySelectorAll(interactive)].filter(visible).map(element => {
      const slots = []
      for (let item = element; item && item !== document.body; item = item.parentElement) {
        if (item.dataset.slot) slots.push(item.dataset.slot)
        if (slots.some(slot => recognized.test(slot))) break
      }
      return { status: slots.some(slot => recognized.test(slot)) ? 'heroui' : 'unverified',
        slot: slots.find(slot => recognized.test(slot)) || '', label: element.getAttribute('aria-label') || element.textContent.trim() }
    }) : []
    const logos = await Promise.all(logoSlugs.map(async slug => {
      const element = [...document.querySelectorAll('img[data-cosmos-logo]')].find(item =>
        item.dataset.cosmosLogo === slug && visible(item) && item.naturalWidth > 0)
      if (!element) return { slug, status:'missing' }
      const url = new URL(element.currentSrc)
      if (url.origin !== location.origin || url.pathname !== `/cosmos-logos/${slug}.svg`) return { slug, status:'unexpected-url' }
      const response = await fetch(url)
      if (!response.ok) return { slug, status:'fetch-failed' }
      const hash = await crypto.subtle.digest('SHA-256', await response.arrayBuffer())
      const sha256 = Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2,'0')).join('')
      return { slug, status:'loaded', sha256 }
    }))
    return { controls, logos, slots: [...new Set(Array.from(document.querySelectorAll('[data-slot]')).filter(visible)
      .map(element => element.dataset.slot))] }
  }, { heroui, logoSlugs })
}
module.exports = {auditUIKit}
