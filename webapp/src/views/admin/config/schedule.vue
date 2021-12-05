<template lang="pug">
.c-scheduleconfig
	.ui-page-header
	scrollbars(y)
		bunt-progress-circular(size="huge", v-if="!error && !config")
		.error(v-if="error") We could not fetch the current configuration.
		.ui-form-body(v-if="config")
			bunt-select(name="source", label="Schedule source", v-model="source", :options="sourceOptions", :disabled="source === 'conftool'")
			template(v-if="source === 'pretalx'")
				p To use pretalx for your event, enter the domain of the pretalx server you use and the short form name of your event. We'll then pull in the schedule automatically and keep it updated. You must be using pretalx version 2 or later.
				bunt-input(name="domain", label="pretalx domain", v-model="config.pretalx.domain", placeholder="e.g. https://pretalx.com", :validation="$v.config.pretalx.domain")
				bunt-input(name="event", label="pretalx event slug", v-model="config.pretalx.event", placeholder="e.g. democon")
			template(v-else-if="source === 'url'")
				p To automatically load the schedule from an external system, enter an URL here. Note that the URL must be a JSON file compliant with the pretalx schedule widget API version 2.
				bunt-input(name="url", label="JSON URL", v-model="config.pretalx.url", placeholder="e.g. https://website.com/event.json", :validation="$v.config.pretalx.url")
			template(v-else-if="source === 'file'")
				p If you don't use pretalx, you can upload your schedule as a Microsoft Excel file (XLSX) with a specific setup.
				p
					a(href="/schedule_ex_en.xlsx", target="_blank") Download English sample file
					| {{ " / " }}
					a(href="/schedule_ex_de.xlsx", target="_blank") Download German sample file
				upload-url-input(name="schedule-file", v-model="config.pretalx.url", label="Schedule file", :validation="$v.config.pretalx.url")
			template(v-else-if="source === 'conftool'")
				p conftool is controlled by the main conftool settings.
	.ui-form-actions
		bunt-button.btn-save(@click="save", :loading="saving", :error-message="error") Save
		.errors {{ validationErrors.join(', ') }}
</template>
<script>
import api from 'lib/api'
import { required, url } from 'lib/validators'
import UploadUrlInput from 'components/UploadUrlInput'
import ValidationErrorsMixin from 'components/mixins/validation-errors'

export default {
	components: { UploadUrlInput },
	mixins: [ValidationErrorsMixin],
	data () {
		return {
			showUpload: false, // HACK we need an extra flag to show an empty file upload, since url and file use the same config field
			config: null,
			saving: false,
			error: null
		}
	},
	computed: {
		sourceOptions () {
			const sourceOptions = [
				{id: null, label: 'No Schedule'},
				{id: 'pretalx', label: 'Pretalx'},
				{id: 'file', label: 'File Upload'},
				{id: 'url', label: 'External URL'},
			]
			if (this.$features.enabled('conftool') && this.config.pretalx.conftool) {
				sourceOptions.push({id: 'conftool', label: 'Conftool'})
			}
			return sourceOptions
		},
		source: {
			get () {
				if (this.config.pretalx.domain !== undefined) return 'pretalx'
				if (this.config.pretalx.conftool) return 'conftool'
				if (this.showUpload) return 'file'
				if (this.config.pretalx.url !== undefined) {
					if (this.config.pretalx.url.includes('/pub/')) { // this *looks* like our storage
						return 'file'
					}
					return 'url'
				}
				return null
			},
			set (value) {
				// setting pretalx.conftool isn't done via frontend so we don't handle it here
				this.showUpload = false
				switch (value) {
					case 'pretalx':
						this.config.pretalx = {
							domain: '',
							event: ''
						}
						break
					case 'file':
						this.showUpload = true
						this.config.pretalx = {
							url: ''
						}
						break
					case 'url':
						this.config.pretalx = {
							url: ''
						}
						break
					case null:
						this.config.pretalx = {}
						break
				}
			}
		}
	},
	validations () {
		if (this.source === 'pretalx') {
			return {
				config: {
					pretalx: {
						domain: {
							required: required('domain is required'),
							url: url('domain must be a valid URL')
						},
						event: {
							required: required('event slug is required')
						}
					}
				}
			}
		}
		if (this.source === 'url' || this.source === 'file') {
			return {
				config: {
					pretalx: {
						url: {
							required: required('URL is required'),
							url: url('URL must be a valid URL')
						}
					}
				}
			}
		}
		return {}
	},
	async created () {
		// TODO: Force reloading if world.updated is received from the server
		try {
			this.config = await api.call('world.config.get')
		} catch (error) {
			this.error = error
			console.log(error)
		}
	},
	async mounted () {
		await this.$nextTick()
	},
	methods: {
		async save () {
			this.$v.$touch()
			if (this.$v.$invalid) return
			this.saving = true
			await api.call('world.config.patch', {pretalx: this.config.pretalx})
			// TODO error handling
			this.saving = false
		}
	}
}
</script>
<style lang="stylus">
.c-scheduleconfig
	flex: auto
	display: flex
	flex-direction: column
	.scroll-content
		flex: auto // take up more space for select dropdown to position correctly
</style>
