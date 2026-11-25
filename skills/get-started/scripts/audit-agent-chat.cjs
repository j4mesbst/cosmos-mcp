// Measure the agreed controls before browser screenshots. The server matches these selectors
// to the approved reference decisions and validates the measured rules for that screenshot.
async function auditAgentChat(page, roles) {
  return page.evaluate(roles => {
    const find = key => document.querySelector(roles[key])
    const elements = Object.fromEntries(Object.keys(roles).map(key => [key, find(key)]))
    const {canvas, back, agent, avatar, computer, messages, composer, add, send} = elements
    if ([canvas, back, agent, avatar, computer, messages, composer, add, send].some(element => !element)) {
      return {roles, measurements: null}
    }
    const rect = element => {
      const {left, top, width, height, right, bottom} = element.getBoundingClientRect()
      return {left, top, width, height, right, bottom}
    }
    const radius = element => parseFloat(getComputedStyle(element).borderTopLeftRadius)
    const box = Object.fromEntries(Object.entries(elements).map(([key, value]) => [key, rect(value)]))
    const firstBubble = messages.firstElementChild
    return {roles, measurements: {
      box, color: getComputedStyle(canvas).backgroundColor,
      divider: parseFloat(getComputedStyle(back.parentElement).borderBottomWidth),
      agentContainsAvatar: agent.contains(avatar),
      composerContainsSend: composer.contains(send), sendEnabled: !send.matches(':disabled'),
      composerContainsAdd: composer.contains(add),
      composerRadius: radius(composer), addRadius: radius(add),
      bubble: firstBubble ? {...rect(firstBubble), radius: radius(firstBubble)} : null,
      viewportHeight: innerHeight,
    }}
  }, roles)
}
module.exports = { auditAgentChat }
