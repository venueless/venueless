<template lang="pug">
.c-stage-settings
	h2 Stream
	bunt-select(v-model="streamSource", name="stream-source", :options="STREAM_SOURCE_OPTIONS", label="Stream source")
	template(v-if="modules['livestream.native']")
		bunt-input(v-model="modules['livestream.native'].config.hls_url", name="url", label="HLS URL")
		upload-url-input(v-model="modules['livestream.native'].config.streamOfflineImage", name="streamOfflineImage", label="Stream offline image")
		bunt-input(v-if="$features.enabled('muxdata')", v-model="modules['livestream.native'].config.mux_env_key", name="muxenvkey", label="MUX data environment key")
		bunt-input(v-model="modules['livestream.native'].config.subtitle_url", name="subtitle_url", label="URL for external subtitles")
		h4 Alternative Streams
		.alternative(v-for="(a, i) in (modules['livestream.native'].config.alternatives || [])")
			bunt-input(v-model="a.label", name="label", label="Label")
			bunt-input(v-model="a.hls_url", name="hls_url", label="HLS URL")
			bunt-icon-button(@click="deleteAlternativeStream(i)") delete-outline
		bunt-button(@click="modules['livestream.native'].config.alternatives = modules['livestream.native'].config.alternatives || []; modules['livestream.native'].config.alternatives.push({label: '', hls_url: ''})") Add alternative stream
	bunt-input(v-else-if="modules['livestream.youtube']", v-model="modules['livestream.youtube'].config.ytid", name="ytid", label="YouTube Video ID", :validation="v$.modules['livestream.youtube'].config.ytid")
	bunt-input(v-else-if="modules['livestream.iframe']", v-model="modules['livestream.iframe'].config.url", name="iframe-player", label="Iframe player url", hint="iframe player should be autoplaying and support resizing to small sizes for background playing")
	sidebar-addons(v-bind="$props")
</template>
<script>
import { useVuelidate } from '@vuelidate/core'
import features from 'features'
import UploadUrlInput from 'components/UploadUrlInput'
import mixin from './mixin'
import SidebarAddons from './SidebarAddons'
import { youtubeid } from 'lib/validators'

const STREAM_SOURCE_OPTIONS = [
	{ id: 'hls', label: 'HLS', module: 'livestream.native' },
	{ id: 'youtube', label: 'YouTube', module: 'livestream.youtube' }
]

if (features.enabled('iframe-player')) {
	STREAM_SOURCE_OPTIONS.push({ id: 'iframe', label: 'Iframe player', module: 'livestream.iframe' })
}

export default {
	components: { UploadUrlInput, SidebarAddons },
	mixins: [mixin],
	setup: () => ({ v$: useVuelidate() }),
	data () {
		return {
			STREAM_SOURCE_OPTIONS,
			b_streamSource: null,
		}
	},
	validations: {
		modules: {
			'livestream.youtube': {
				config: {
					ytid: {
						youtubeid: youtubeid('not a valid YouTube video ID (do not supply the full URL)')
					}
				}
			}
		}
	},
	computed: {
		streamSource: {
			get () {
				return this.b_streamSource
			},
			set (value) {
				this.b_streamSource = value
				STREAM_SOURCE_OPTIONS.map(option => option.module).forEach(module => this.removeModule(module))
				this.addModule(STREAM_SOURCE_OPTIONS.find(option => option.id === value).module)
			},
		}
	},
	created () {
		if (this.modules['livestream.native']) {
			this.b_streamSource = 'hls'
		} else if (this.modules['livestream.youtube']) {
			this.b_streamSource = 'youtube'
		} else if (this.modules['livestream.iframe']) {
			this.b_streamSource = 'iframe'
		}
	},
	methods: {
		deleteAlternativeStream (index) {
			this.modules['livestream.native'].config.alternatives.splice(index, 1)
			if (this.modules['livestream.native'].config.alternatives.length === 0) {
				this.modules['livestream.native'].config.alternatives = undefined
			}
		}
	}
}
</script>
<style lang="stylus">
</style>
