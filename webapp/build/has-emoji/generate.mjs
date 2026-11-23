// ⁂ Lists the twemoji SVGs shipped by @twemoji/svg, so lib/emoji.js knows which files exist under /emoji/.
// ⁂ Run `node build/has-emoji/generate.mjs` in webapp/ after upgrading @twemoji/svg, and commit emoji.json.
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs/promises'

const files = await fs.readdir(fileURLToPath(new URL('../../node_modules/@twemoji/svg', import.meta.url)))

const emoji = files.filter(file => file.endsWith('.svg')).map(file => file.replace('.svg', '')).sort()

console.log(`${emoji.length} emoji`)

await fs.writeFile(fileURLToPath(new URL('emoji.json', import.meta.url)), JSON.stringify(emoji))

