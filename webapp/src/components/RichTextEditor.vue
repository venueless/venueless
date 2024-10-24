<template lang="pug">
bunt-input-outline-container.c-rich-text-editor(ref="outline", :label="label")
	.toolbar(ref="toolbar")
		.buttongroup
			bunt-icon-button.ql-bold(v-tooltip="$t('RichTextEditor:bold:tooltip')") format-bold
			bunt-icon-button.ql-italic(v-tooltip="$t('RichTextEditor:italic:tooltip')") format-italic
			bunt-icon-button.ql-underline(v-tooltip="$t('RichTextEditor:underline:tooltip')") format-underline
			bunt-icon-button.ql-strike(v-tooltip="$t('RichTextEditor:strike:tooltip')") format-strikethrough-variant
		.buttongroup
			bunt-icon-button.ql-header(v-tooltip="$t('RichTextEditor:h1:tooltip')", value="1") format-header-1
			bunt-icon-button.ql-header(v-tooltip="$t('RichTextEditor:h2:tooltip')", value="2") format-header-2
			bunt-icon-button.ql-header(v-tooltip="$t('RichTextEditor:h3:tooltip')", value="3") format-header-3
			bunt-icon-button.ql-header(v-tooltip="$t('RichTextEditor:h4:tooltip')", value="4") format-header-4
			bunt-icon-button.ql-blockquote(v-tooltip="$t('RichTextEditor:blockquote:tooltip')") format-quote-open
			bunt-icon-button.ql-code-block(v-tooltip="$t('RichTextEditor:code:tooltip')") code-tags
		.buttongroup
			bunt-icon-button.ql-list(v-tooltip="$t('RichTextEditor:list-ordered:tooltip')", value="ordered") format-list-numbered
			bunt-icon-button.ql-list(v-tooltip="$t('RichTextEditor:list-bullet:tooltip')", value="bullet") format-list-bulleted
		.buttongroup
			bunt-icon-button.ql-align(v-tooltip="$t('RichTextEditor:align-left:tooltip')", value="") format-align-left
			bunt-icon-button.ql-align(v-tooltip="$t('RichTextEditor:align-center:tooltip')", value="center") format-align-center
			bunt-icon-button.ql-align(v-tooltip="$t('RichTextEditor:align-right:tooltip')", value="right") format-align-right
			bunt-icon-button.ql-full-width(v-tooltip="$t('RichTextEditor:full-width:tooltip')") arrow-expand-horizontal
		.buttongroup
			bunt-icon-button.ql-link(v-tooltip="$t('RichTextEditor:link:tooltip')") link-variant
			bunt-icon-button.ql-image(v-tooltip="$t('RichTextEditor:image:tooltip')") image
			bunt-icon-button.ql-video(v-tooltip="$t('RichTextEditor:video:tooltip')") filmstrip-box
		.buttongroup
			bunt-icon-button.ql-clean(v-tooltip="$t('RichTextEditor:clean:tooltip')") format-clear
	.editor.rich-text-content(ref="editor")
	.uploading(v-if="uploading")
		bunt-progress-circular(size="huge")

</template>
<script>
/* global ENV_DEVELOPMENT */
import { markRaw } from 'vue'
import Quill from 'quill'
import BuntTheme from 'lib/quill/BuntTheme'
import VideoResponsive from 'lib/quill/VideoResponsive'
import fullWidthFormat from 'lib/quill/fullWidthFormat'
import Emitter from 'quill/core/emitter'
import api from 'lib/api'

const Delta = Quill.import('delta')

export default {
	props: {
		modelValue: [Delta, Object],
		label: String
	},
	emits: ['update:modelValue'],
	data () {
		return {
			quill: null,
			uploading: false,
		}
	},
	computed: {},
	mounted () {
		Quill.register('themes/bunt', BuntTheme, false)
		Quill.register(VideoResponsive)
		Quill.register(fullWidthFormat)
		this.quill = markRaw(new Quill(this.$refs.editor, {
			debug: ENV_DEVELOPMENT ? 'info' : 'warn',
			theme: 'bunt',
			modules: {
				toolbar: {
					container: this.$refs.toolbar,
					handlers: {
						image: () => {
							const fileInput = document.createElement('input')
							fileInput.setAttribute('type', 'file')
							fileInput.setAttribute('accept', 'image/png, image/gif, image/jpeg, image/bmp, image/x-icon')
							fileInput.addEventListener('change', () => {
								if (fileInput.files != null && fileInput.files[0] != null) {
									const file = fileInput.files[0]

									this.uploading = true
									api.uploadFilePromise(file, file.name).then(data => {
										if (data.error) {
											alert(`Upload error: ${data.error}`) // Proper user-friendly messages
											this.$emit('update:modelValue', '')
										} else {
											const range = this.quill.getSelection(true)
											this.quill.updateContents(new Delta()
												.retain(range.index)
												.delete(range.length)
												.insert({ image: data.url }), Emitter.sources.USER)
											this.quill.setSelection(range.index + 1, Emitter.sources.SILENT)
										}
										this.uploading = false
									}).catch(error => {
										// TODO: better error handling
										console.log(error)
										alert(`error: ${error}`)
										this.uploading = false
									})
								}
							})
							fileInput.click()
						},
					}
				}
			},
			bounds: this.$refs.editor,
		}))
		if (this.modelValue && this.modelValue.ops.length > 0) {
			this.quill.setContents(this.modelValue)
		}
		this.quill.on('selection-change', this.onSelectionchange)
		this.quill.on('text-change', this.onTextchange)
	},
	unmounted () {
		this.quill.off('selection-change', this.onSelectionchange)
		this.quill.off('text-change', this.onTextchange)
	},
	methods: {
		onTextchange () {
			this.$emit('update:modelValue', this.quill.getContents())
		},
		onSelectionchange (range, oldRange) {
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
	position: relative

	.uploading
		position: absolute
		left: 0
		top: 0
		width: 100%
		height: 100%
		background: rgba(255, 255, 255, 0.7)
		display: flex
		align-items: center
		justify-content: center

	.toolbar
		border-bottom: 1px solid #ccc
		display: flex
		flex-direction: row
		flex-wrap: wrap
		padding: 4px
		.buttongroup
			margin-right: 16px
		.bunt-icon-button
			border-radius: 8px
			margin-right: 2px
			.bunt-icon
				color: rgba(0, 0, 0, 0.5)
		.ql-active
			background: #f0f0f0
		.ql-active .bunt-icon
			color: var(--clr-primary)
	.ql-editor
		min-height: 46px
	.ql-hidden
		display: none
	.ql-tooltip  /* based on https://github.com/quilljs/quill/blob/develop/assets/snow/tooltip.styl */
		z-index: 1000
		position: absolute
		background-color: #fff
		border: 1px solid #ccc
		box-shadow: 0px 0px 5px #ddd
		padding: 5px 12px
		white-space: nowrap

		&::before
			content: "Visit URL:"
			line-height: 26px
			margin-right: 8px

		input[type=text]
			display: none
			border: 1px solid #ccc
			font-size: 13px
			height: 26px
			margin: 0px
			padding: 3px 5px
			width: 170px

		a.ql-preview
			display: inline-block
			max-width: 200px
			overflow-x: hidden
			text-overflow: ellipsis
			vertical-align: top

		a.ql-action::after
			border-right: 1px solid #ccc
			content: 'Edit'
			margin-left: 16px
			padding-right: 8px

		a.ql-remove::before
			content: 'Remove'
			margin-left: 8px

		a
			line-height: 26px

	.ql-tooltip.ql-editing
		a.ql-preview, a.ql-remove
			display: none

		input[type=text]
			display: inline-block

		a.ql-action::after
			border-right: 0px
			content: 'Save'
			padding-right: 0px

	.ql-tooltip[data-mode=link]::before
		content: "Enter link:"
</style>
