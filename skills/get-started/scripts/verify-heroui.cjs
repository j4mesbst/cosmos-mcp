const fs = require('node:fs')
const path = require('node:path')
const assert = require('node:assert/strict')
const { createRequire } = require('node:module')

function verify() {
  const { parse } = createRequire(path.resolve('package.json'))('@babel/parser')
  const { files, entry } = JSON.parse(fs.readFileSync(0, 'utf8'))
  assert(files[entry], 'Register the JSX entry file.')
  const native = new Set(['a', 'button', 'input', 'select', 'textarea', 'details', 'dialog', 'summary'])
  const interactiveRoles = new Set(['button', 'switch', 'checkbox', 'radio', 'tab', 'combobox', 'slider', 'link'])
  const used = new Set()
  for (const [file, code] of Object.entries(files)) {
    const tree = parse(code, { sourceType: 'unambiguous', plugins: ['jsx', 'typescript'] })
    const bindings = new Map()
    for (const statement of tree.program.body) {
      if (statement.type !== 'ImportDeclaration') continue
      const source = statement.source.value
      assert(!/^(@nextui-org\/|@radix-ui\/|@headlessui\/|@mui\/|antd$|react-aria-components$)/.test(source),
        `${file} imports a competing UI implementation`)
      if (source === '@heroui/react') {
        for (const spec of statement.specifiers) {
          if (spec.type === 'ImportSpecifier') bindings.set(spec.local.name, spec.imported.name)
        }
      }
      if (source.startsWith('.') && file !== 'vite.config.js') {
        const wanted = path.posix.normalize(path.posix.join(path.posix.dirname(file), source))
        if (!/\.(css|json|svg|png|webp|jpg|jpeg)$/.test(wanted)) {
          assert(['', '.tsx', '.jsx', '.ts', '.js', '.mjs', '/index.tsx', '/index.jsx', '/index.ts', '/index.js']
            .some(ext => Object.hasOwn(files, wanted + ext)), `Register imported source ${wanted}`)
        }
      }
    }
    const scan = node => {
      if (!node || typeof node !== 'object') return
      if (node.type === 'JSXOpeningElement') {
        let root = node.name
        while (root.type === 'JSXMemberExpression') root = root.object
        const name = root.name
        assert(!native.has(name), `Use HeroUI for <${name}> in ${file}`)
        if (bindings.has(name)) used.add(bindings.get(name))
        for (const attr of node.attributes) {
          if (attr.type !== 'JSXAttribute') continue
          const key = attr.name.name
          assert(key !== 'data-slot', `Do not write library data-slot markers in ${file}`)
          if (/^[a-z]/.test(name || '')) {
            assert(!(key === 'role' && interactiveRoles.has(attr.value?.value)),
              `Use a HeroUI component for ${attr.value?.value} in ${file}`)
          }
        }
      }
      for (const child of Object.values(node)) {
        if (Array.isArray(child)) child.forEach(scan)
        else if (child && typeof child === 'object') scan(child)
      }
    }
    scan(tree.program)
  }
  assert(used.has('Button') || used.has('Link'), 'Render an imported HeroUI Button or Link.')
  process.stdout.write(JSON.stringify([...used].sort()))
}

try { verify() } catch (error) {
  process.stderr.write(error.message)
  process.exitCode = 1
}
