<template lang="pug">
bunt-input-outline-container.c-rich-text-editor(ref="outline")
	.toolbar(ref="toolbar")
		.buttongroup
			bunt-icon-button.ql-bold(v-tooltip="$t('RichTextEditor:bold:tooltip')") format-bold
			bunt-icon-button.ql-italic(v-tooltip="$t('RichTextEditor:italic:tooltip')") format-italic
			bunt-icon-button.ql-underline(v-tooltip="$t('RichTextEditor:underline:tooltip')") format-underline
			bunt-icon-button.ql-strike(v-tooltip="$t('RichTextEditor:strike:tooltip')") format-strikethrough-variant
		.buttongroup
			bunt-icon-button.ql-header(value="1", v-tooltip="$t('RichTextEditor:h1:tooltip')") format-header-1
			bunt-icon-button.ql-header(value="2", v-tooltip="$t('RichTextEditor:h2:tooltip')") format-header-2
			bunt-icon-button.ql-header(value="3", v-tooltip="$t('RichTextEditor:h3:tooltip')") format-header-3
			bunt-icon-button.ql-header(value="4", v-tooltip="$t('RichTextEditor:h4:tooltip')") format-header-4
			bunt-icon-button.ql-blockquote(v-tooltip="$t('RichTextEditor:blockquote:tooltip')") format-quote-open
			bunt-icon-button.ql-code-block(v-tooltip="$t('RichTextEditor:code:tooltip')") code-tags
		.buttongroup
			bunt-icon-button.ql-list(value="ordered", v-tooltip="$t('RichTextEditor:list-ordered:tooltip')") format-list-numbered
			bunt-icon-button.ql-list(value="bullet", v-tooltip="$t('RichTextEditor:list-bullet:tooltip')") format-list-bulleted
		.buttongroup
			bunt-icon-button.ql-align(value="", v-tooltip="$t('RichTextEditor:align-left:tooltip')") format-align-left
			bunt-icon-button.ql-align(value="center", v-tooltip="$t('RichTextEditor:align-center:tooltip')") format-align-center
			bunt-icon-button.ql-align(value="right", v-tooltip="$t('RichTextEditor:align-right:tooltip')") format-align-right
		.buttongroup
			bunt-icon-button.ql-link(v-tooltip="$t('RichTextEditor:link:tooltip')") link-variant
			bunt-icon-button.ql-image(v-tooltip="$t('RichTextEditor:image:tooltip')") image
		.buttongroup
			bunt-icon-button.ql-clean(v-tooltip="$t('RichTextEditor:clean:tooltip')") format-clear
	.editor.rich-text-content(ref="editor")

</template>
<script>
/* global ENV_DEVELOPMENT */
import Quill from 'quill'
import 'quill/dist/quill.core.css'

const Delta = Quill.import('delta')

export default {
	props: {
		value: Array,
	},
	data () {
		return {
			quill: null,
		}
	},
	computed: {},
	mounted () {
		this.quill = new Quill(this.$refs.editor, {
			debug: ENV_DEVELOPMENT ? 'info' : 'warn',
			modules: {
				toolbar: this.$refs.toolbar,
			},
		})
		if (this.value) {
			this.quill.setContents(this.value)
		}
		this.quill.on('selection-change', this.onSelectionchange)
		this.quill.on('text-change', this.onTextchange)
	},
	destroyed () {
		this.quill.off('selection-change', this.onSelectionchange)
		this.quill.off('text-change', this.onTextchange)
	},
	methods: {
		onTextchange (delta, oldContents, source) {
			this.$emit('input', this.quill.getContents())
		},
		onSelectionchange (range, oldRange, source) {
			if (range === null && oldRange !== null) {
				this.$refs.outline.blur()
			} else if (range !== null && oldRange === null) {
				this.$refs.outline.focus()
			}
		},
	},
}
</script>
<style lang="stylus">
.c-rich-text-editor
	padding-top: 0

	.toolbar
		border-bottom: 1px solid #ccc
		display: flex
		flex-direction: row
		flex-wrap: wrap
		.buttongroup
			margin-right: 16px
		.bunt-icon-button .bunt-icon
			color: rgba(0, 0, 0, 0.5)
		.ql-active .bunt-icon
			color: var(--clr-primary)
</style>
