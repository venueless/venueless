<script>
import MarkdownIt from 'markdown-it'
import store from 'store'
import { markdownEmoji } from 'lib/emoji'
import { getUserName } from 'lib/profile'

const markdownIt = MarkdownIt('zero', {
	linkify: true // TODO more tlds
})
markdownIt.enable('linkify')
markdownIt.renderer.rules.link_open = function (tokens, idx, options, env, self) {
	tokens[idx].attrPush(['target', '_blank'])
	tokens[idx].attrPush(['rel', 'noopener noreferrer'])
	return self.renderToken(tokens, idx, options)
}

markdownIt.use(markdownEmoji)

const mentionRegex = /(@[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12})/g

export async function contentToPlainText (content) {
	const parts = content.split(mentionRegex)
	let plaintext = ''
	for (const string of parts) {
		if (string.match(mentionRegex)) {
			const userId = string.slice(1)
			if (!store.state.chat.usersLookup[userId]) await store.dispatch('chat/fetchUsers', [userId])
			const user = store.state.chat.usersLookup[string.slice(1)]
			if (user) {
				plaintext += `@${getUserName(user)}`
			}
		} else {
			plaintext += string
		}
	}
	return plaintext
}

const generateHTML = function (input) {
	if (!input) return
	return markdownIt.renderInline(input)
}

export default {
	functional: true,
	props: {
		content: String
	},
	render (createElement, ctx) {
		const parts = ctx.props.content.split(mentionRegex)
		const content = parts.map(string => {
			if (string.match(mentionRegex)) {
				const user = ctx.parent.$store.state.chat.usersLookup[string.slice(1)]
				if (user) {
					return {user}
				}
			}
			return {html: generateHTML(string)}
		})
		return content.map(part => {
			if (part.user) {
				return createElement('span', {
					class: 'mention',
					on: {
						click: (event) => ctx.listeners.clickMention(event, part.user, 'top-start')
					}
				}, getUserName(part.user))
			}
			return createElement('span', {domProps: {innerHTML: part.html}})
		})
	}
}
</script>
