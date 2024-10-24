<template lang="pug">
.c-themeconfig
	.ui-page-header
		h1 Theme Config
	scrollbars(y)
		bunt-progress-circular(v-if="!error && !config", size="huge")
		.error(v-if="error") We could not fetch the current configuration.
		template(v-if="config")
			.ui-form-body
				color-picker(v-model="config.theme.colors.primary", name="colors_primary", label="Primary color", :validation="v$.config.theme.colors.primary")
				color-picker(v-model="config.theme.colors.sidebar", name="colors_sidebar", label="Sidebar color", :validation="v$.config.theme.colors.sidebar")
				color-picker(v-model="config.theme.colors.bbb_background", name="colors_bbb_background", label="BBB background color", :validation="v$.config.theme.colors.bbb_background")
				upload-url-input(v-model="config.theme.logo.url", name="logo_url", label="Logo", :validation="v$.config.theme.logo.url")
				bunt-checkbox(v-model="config.theme.logo.fitToWidth", name="logo_fit", label="Fit logo to width")
				upload-url-input(v-model="config.theme.streamOfflineImage", name="streamoffline_url", label="Stream offline image", :validation="v$.config.theme.streamOfflineImage")
				upload-url-input(v-model="config.theme.webappIcon", name="webapp_icon_url", label="Web app icon (PNG, square)", :validation="v$.config.theme.webappIcon")
				bunt-select#select-identicon-style(v-model="config.theme.identicons.style", name="identicon-style", label="Identicon style", :options="identiconStyles")
			.text-overwrites
				.header
					div Original
					div Custom translation
				tr.overwrite(v-for="(val, key) in strings")
					.source
						.key {{ key }}
						.value {{ val }}
					bunt-input(v-model="config.theme.textOverwrites[key]", :name="key")
	.ui-form-actions
		bunt-button.btn-save(:loading="saving", :errorMessage="error", @click="save") Save
		.errors {{ validationErrors.join(', ') }}
</template>
<script>
import { useVuelidate } from '@vuelidate/core'
import api from 'lib/api'
import { DEFAULT_COLORS, DEFAULT_LOGO, DEFAULT_IDENTICONS } from 'theme'
import i18n from 'i18n'
import ColorPicker from 'components/ColorPicker'
import UploadUrlInput from 'components/UploadUrlInput'
import ValidationErrorsMixin from 'components/mixins/validation-errors'
import { required, color, url } from 'lib/validators'
import { renderers as identiconRenderers } from 'lib/identicons'

export default {
	components: { ColorPicker, UploadUrlInput },
	mixins: [ValidationErrorsMixin],
	setup: () => ({ v$: useVuelidate() }),
	data () {
		return {
			// We do not use the global config object since we cannot rely on it being up to date (theme is only updated
			// during application load).
			config: null,

			saving: false,
			error: null
		}
	},
	computed: {
		strings () {
			// access i18n dict via undocumented api
			return i18n.store.data[this.config.locale].translation
		},
		identiconStyles () {
			return Object.entries(identiconRenderers).map(([id, renderer]) => ({
				id,
				label: renderer.definition.label
			}))
		}
	},
	validations: {
		config: {
			theme: {
				colors: {
					primary: {
						required: required('primary color is required'),
						color: color('color must be in 3 or 6 digit hex format')
					},
					sidebar: {
						required: required('sidebar color is required'),
						color: color('color must be in 3 or 6 digit hex format')
					},
					bbb_background: {
						required: required('BBB background color is required'),
						color: color('color must be in 3 or 6 digit hex format')
					},
				},
				logo: {
					url: {
						url: url('must be a valid url')
					}
				},
				streamOfflineImage: {
					url: url('must be a valid url')
				},
				webappIcon: {
					url: url('must be a valid url')
				},
			},
		}
	},
	async created () {
		// TODO: Force reloading if world.updated is received from the server
		try {
			this.config = await api.call('world.config.get')

			// Enforce some defaults
			this.config.theme = { logo: {}, colors: {}, streamOfflineImage: null, textOverwrites: {}, ...this.config.theme }
			this.config.theme.colors = { ...DEFAULT_COLORS, ...this.config.theme.colors }
			this.config.theme.logo = { ...DEFAULT_LOGO, ...this.config.theme.logo }
			this.config.theme.identicons = { ...DEFAULT_IDENTICONS, ...this.config.theme.identicons }
		} catch (error) {
			this.error = error
			console.log(error)
		}
	},
	methods: {
		async save () {
			this.v$.$touch()
			if (this.v$.$invalid) return

			// Cleanup empty strings in text overwrites
			for (const key of Object.keys(this.config.theme.textOverwrites)) {
				if (!this.config.theme.textOverwrites[key]) {
					delete this.config.theme.textOverwrites[key]
				}
			}

			this.saving = true
			await api.call('world.config.patch', { theme: this.config.theme })
			this.saving = false
			// TODO error handling

			location.reload() // Theme config is only activated after reload
		},
	}
}
</script>
<style lang="stylus">
.c-themeconfig
	flex: auto
	display: flex
	flex-direction: column
	.text-overwrites
		display: flex
		flex-direction: column
		> *
			display: flex
			align-items: center
			height: 52px
			> *
				width: 50%
		.header
			text-align: left
			border-bottom: border-separator()
			padding: 10px
			font-weight: 600
			font-size: 18px
			position: sticky
			top: 0
			background-color: $clr-white
			z-index: 1
		.overwrite
			&:hover
				background-color: $clr-grey-100
			.source
				display: flex
				flex-direction: column
				justify-content: space-around
				padding-left: 8px
				.key
					color: $clr-secondary-text-light
					font-size: 12px
					font-style: italic
			.bunt-input
				input-style(size: compact)
				padding-top: 0
				margin-right: 8px
</style>
