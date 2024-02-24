// scan all emoji in twemoji-emojis/vendor/svg/ and create a map of emoji to their svg
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs/promises'

const files = await fs.readdir(fileURLToPath(new URL('../../node_modules/twemoji-emojis/vendor/svg', import.meta.url)))

const emoji = files.map(file => file.replace('.svg', ''))

console.log(emoji)

await fs.writeFile(fileURLToPath(new URL('emoji.json', import.meta.url)), JSON.stringify(emoji))

