<template lang="pug">
.c-change-avatar(v-if="modelValue")
	.inputs
		bunt-button.btn-randomize(@click="changeIdenticon") {{ $t('profile/ChangeAvatar:button-randomize:label') }}
		span {{ $t('profile/ChangeAvatar:or') }}
		upload-button.btn-upload(accept="image/png, image/jpg, .png, .jpg, .jpeg", @change="fileSelected") {{ $t('profile/ChangeAvatar:button-upload:label') }}
	.image-wrapper
		.file-error(v-if="fileError")
			.mdi.mdi-alert-octagon
			.message {{ fileError }}
		cropper(v-else-if="avatarImage", ref="cropper", class="cropper", :stencilComponent="$options.components.CircleStencil", :src="avatarImage", :stencilProps="{aspectRatio: '1/1'}", :sizeRestrictionsAlgorithm="pixelsRestrictions")
		identicon(v-else, :user="identiconUser", @click="changeIdenticon")
</template>
<script>
import { v4 as uuid } from 'uuid'
import { Cropper, CircleStencil } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import api from 'lib/api'
import Identicon from 'components/Identicon'
import UploadButton from 'components/UploadButton'

const MAX_AVATAR_SIZE = 128

export default {
	// eslint-disable-next-line vue/no-unused-components
	components: { Cropper, CircleStencil, Identicon, UploadButton },
	props: {
		modelValue: Object,
		profile: Object
	},
	emits: ['update:modelValue', 'blockSave'],
	data () {
		return {
			identicon: null,
			avatarImage: null,
			fileError: null,
			changedImage: false
		}
	},
	computed: {
		identiconUser () {
			return {
				profile: {
					...this.profile,
					avatar: {
						identicon: this.identicon
					}
				}
			}
		}
	},
	created () {
		if (!this.modelValue) {
			this.$emit('update:modelValue', {})
			this.identicon = uuid()
		} else if (this.modelValue.url) {
			this.avatarImage = this.modelValue.url
		} else if (this.modelValue.identicon) {
			this.identicon = this.modelValue.identicon
		}
	},
	methods: {
		changeIdenticon () {
			this.fileError = null
			this.avatarImage = null
			this.identicon = uuid()
			this.$emit('blockSave', false)
		},
		fileSelected (event) {
			// TODO block reupload while running?
			this.fileError = null
			this.avatarImage = null
			this.$emit('blockSave', false)
			if (!event.target.files.length === 1) return
			const avatarFile = event.target.files[0]
			const reader = new FileReader()
			reader.readAsDataURL(avatarFile)
			event.target.modelValue = ''
			reader.onload = event => {
				if (event.target.readyState !== FileReader.DONE) return
				const img = new Image()
				img.onload = () => {
					if (img.width < 128 || img.height < 128) {
						this.fileError = this.$t('profile/ChangeAvatar:error:image-too-small')
						this.$emit('blockSave', true)
					} else {
						this.changedImage = true
						this.avatarImage = event.target.result
					}
				}
				img.src = event.target.result
			}
		},
		pixelsRestrictions ({ minWidth, minHeight, maxWidth, maxHeight }) {
			return {
				minWidth: Math.max(128, minWidth),
				minHeight: Math.max(128, minHeight),
				maxWidth,
				maxHeight,
			}
		},
		update () {
			return new Promise((resolve) => {
				const { canvas } = this.$refs.cropper?.getResult() || {}
				if (!canvas) {
					this.$emit('update:modelValue', { identicon: this.identicon })
					return resolve()
				}
				if (!this.changedImage) return resolve()

				canvas.toBlob(blob => {
					const request = api.uploadFile(blob, 'avatar.png', null, MAX_AVATAR_SIZE, MAX_AVATAR_SIZE)
					request.addEventListener('load', () => {
						const response = JSON.parse(request.responseText)
						this.$emit('update:modelValue', { url: response.url })
						resolve()
					})
				}, 'image/png') // TODO use original mimetype
			})
		},
	}
}
</script>
<style lang="stylus">
.c-change-avatar
	display: flex
	flex-direction: column
	align-items: center
	.c-identicon
		cursor: pointer
		height: 128px
		width: 128px
	.inputs
		display: flex
		justify-content: center
		align-items: center
		margin-bottom: 16px
		> span
			margin: 0 28px 0 16px
	.btn-randomize
		themed-button-secondary()
	.btn-upload .bunt-button
		themed-button-primary()
	.image-wrapper
		flex: auto
		display: flex
		flex-direction: column
		align-items: center
		justify-content: center
		height: calc(80vh - 230px) // HACK approx. shrinking to avoid top down constraints
		max-height: 320px
		min-height: 160px
		+below('m')
			height: calc(95vh - 230px)
	.file-error
		width: 320px
		height: 320px
		display: flex
		flex-direction: column
		color: $clr-danger
		align-items: center
		justify-content: center
		.mdi
			font-size: 64px
	.cropper
		width: 320px
		height: 320px
		background-color: $clr-grey-900
</style>
