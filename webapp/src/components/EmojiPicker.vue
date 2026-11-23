<template lang="pug">
.c-emoji-picker
</template>
<script>
import i18next from 'i18next'
import { colors } from 'theme'
import { loadEmojiData } from 'lib/emoji'

// Inject translations to prevent CDN fetch
const PICKER_LOCALES = {
	de: () => import('@emoji-mart/data/i18n/de.json'),
	pt_BR: () => import('@emoji-mart/data/i18n/pt.json'),
}

export default {
	emits: ['selected'],
	async mounted () {
		const [{ Picker }, data, i18n] = await Promise.all([
			import('emoji-mart'),
			loadEmojiData(),
			PICKER_LOCALES[i18next.language]?.().then(module => module.default)
		])
		if (!this.$el.isConnected) return
		const picker = new Picker({
			data,
			i18n,
			set: 'twitter',
			theme: 'light',
			getSpritesheetURL: () => '',
			onEmojiSelect: emoji => this.$emit('selected', emoji)
		})
		picker.style.setProperty('--rgb-accent', colors.primary.rgb().array().join(', '))
		picker.injectStyles('.emoji-mart-emoji img { width: 1em; height: 1em; }')
		this.$el.appendChild(picker)
	}
}
</script>
<style lang="stylus">
.c-emoji-picker
	min-width: 352px
	min-height: 435px
	em-emoji-picker
		--font-family: $font-stack
		--border-radius: 2px
		--shadow: 0 2px 5px 0 rgba(0, 0, 0, .16), 0 2px 10px 0 rgba(0, 0, 0, .12)
</style>
