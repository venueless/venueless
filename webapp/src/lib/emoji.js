import EmojiRegex from 'emoji-regex'
import MarkdownIt from 'markdown-it'

import emojiList from 'has-emoji'

const hasEmoji = emojiList.reduce((acc, emoji) => {
	acc[emoji] = true
	return acc
}, {})

const emojiRegex = EmojiRegex()
const splitEmojiRegex = new RegExp(`(${emojiRegex.source})`, 'g')
const startsWithEmojiRegex = new RegExp(`^${emojiRegex.source}`)

export function objectToCssString (object) {
	return Object.entries(object).map(([key, value]) => `${key}:${value}`).join(';')
}

export function startsWithEmoji (string) {
	return startsWithEmojiRegex.test(string)
}

export function nativeToOps (string) {
	return string.split(splitEmojiRegex).map(match => {
		if (emojiRegex.test(match)) {
			// slightly wasteful to test for emoji again
			return { insert: { emoji: match } }
		} else {
			return { insert: match }
		}
	})
}

function twemojiName (codepoints) {
	codepoints = [...codepoints]
	while (codepoints.length) {
		const name = codepoints.join('-')
		if (hasEmoji[name]) return name
		const withoutVariation = codepoints.filter(c => c !== 'fe0f').join('-')
		if (hasEmoji[withoutVariation]) return withoutVariation
		codepoints.pop()
	}
	return '2753'
}

let emojiDataPromise = null
let emojiByNative = null

// Load data once; inject the src to avoid CDN load
export function loadEmojiData () {
	if (!emojiDataPromise) {
		emojiDataPromise = import('@emoji-mart/data/sets/15/twitter.json').then(({ default: data }) => {
			emojiByNative = {}
			for (const emoji of Object.values(data.emojis)) {
				for (const skin of emoji.skins) {
					skin.src = `/emoji/${twemojiName(skin.unified.split('-').map(c => c.replace(/^0+/, '')))}.svg`
					emojiByNative[skin.native] = emoji
					emojiByNative[skin.native.replace(/\uFE0F/g, '')] ??= emoji
				}
			}
			return data
		})
	}
	return emojiDataPromise
}

export async function getEmojiDataFromNative (native) {
	await loadEmojiData()
	return emojiByNative[native] ?? emojiByNative[native.replace(/\uFE0F/g, '')] ?? null
}

export function nativeToStyle (unicodeEmoji) {
	// maps multi-codepoint emoji like 🇻🇦 / \uD83C\uDDFB\uD83C\uDDE6 => 1f1fb-1f1e6.svg
	const codepoints = Array.from(unicodeEmoji).map(c => c.codePointAt(0).toString(16))
	return { 'background-image': `url(/emoji/${twemojiName(codepoints)}.svg)` }
}

export function markdownEmoji (md) {
	function splitTextToken (text, Token) {
		let token
		let lastPos = 0
		const tokens = []

		text.replace(emojiRegex, function (match, offset) {
			// Add new tokens to pending list
			if (offset > lastPos) {
				token = new Token('text', '', 0)
				token.content = text.slice(lastPos, offset)
				tokens.push(token)
			}

			token = new Token('emoji', '', 0)
			token.content = match
			tokens.push(token)
			lastPos = offset + match.length
		})

		if (lastPos < text.length) {
			token = new Token('text', '', 0)
			token.content = text.slice(lastPos)
			tokens.push(token)
		}

		return tokens
	}
	md.core.ruler.push('emoji', function emojiReplace (state) {
		let autolinkLevel = 0

		for (const blockToken of state.tokens) {
			if (blockToken.type !== 'inline') continue
			let tokens = blockToken.children

			// We scan from the end, to keep position when new tags added.
			// Use reversed logic in links start/end match
			for (let i = tokens.length - 1; i >= 0; i--) {
				const token = tokens[i]

				if (token.type === 'link_open' || token.type === 'link_close') {
					if (token.info === 'auto') autolinkLevel -= token.nesting
				}

				if (token.type === 'text' && autolinkLevel === 0 && emojiRegex.test(token.content)) {
					// replace current node
					blockToken.children = tokens = md.utils.arrayReplaceAt(
						tokens, i, splitTextToken(token.content, state.Token)
					)
				}
			}
		}
	})
	md.renderer.rules.emoji = (tokens, idx) => {
		const isFirst = idx === 0
		const needsSpace = tokens[idx + 1] && !tokens[idx + 1].content.startsWith(' ')
		const emoji = tokens[idx].content
		return `<span class="emoji${isFirst && needsSpace ? ' needs-space' : ''}" style="${objectToCssString(nativeToStyle(emoji))}">${emoji}</span>`
	}
}

// global markdown instance to emojify plaintext
const markdownIt = MarkdownIt('zero', {})
markdownIt.use(markdownEmoji)

export function emojifyString (input) {
	if (!input) return
	return markdownIt.renderInline(input)
}

export const emojiPlugin = {
	install (app) {
		app.config.globalProperties.$emojify = emojifyString
	}
}
