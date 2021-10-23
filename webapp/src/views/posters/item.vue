<template lang="pug">
.v-poster
	template(v-if="poster")
		//- .ui-page-header
		//- 	bunt-icon-button(@click="$router.push({name: 'admin:rooms:index'})") arrow_left
		//- 	h1.title {{ poster.title }}
		.info-sidebar
			scrollbars(y)
				.info
					h2.category {{ poster.category }}
					.tags
						.tag(v-for="tag of poster.tags") {{ tag }}
					h1.title {{ poster.title }}
					.authors {{ poster.authors.authors.map(a => a.name).join(', ') }}
					.presenters
						h3 Presenters
						.presenter(v-for="user in poster.presenters")
							avatar(:user="user", :size="36")
							span.display-name {{ user ? user.profile.display_name : '' }}
					rich-text-content.abstract(:content="poster.abstract")
					.downloads(v-if="poster.links.length > 0")
						h3 {{ $t("Exhibitor:downloads-headline:text") }}
						a.download(v-for="file in poster.links", :href="file.url", target="_blank")
							.mdi.mdi-file-pdf-outline(v-if="file.url.toLowerCase().endsWith('pdf')")
							.filename {{ file.display_text }}
		.poster
			//- .poster-content
				h1.title {{ poster.title }}
				.authors {{ poster.authors.authors.map(a => a.name).join(', ') }}
				rich-text-content.abstract(:content="poster.abstract")
			iframe(:src="poster.poster_url + '#navpanes=0&view=Fit'")
				//- a.poster(:href="poster.poster_url", target="_blank", title="click me to open poster pdf")
				//- 	img(:src="poster.poster_preview")
		.chat-sidebar
			.actions
				bunt-button(tooltip="opens room linked via schedule") go to session
				.likes(v-tooltip="'imagine clicking does something'")
					.mdi.mdi-heart-outline
					.count {{ poster.likes }}
			h3 Discuss
			chat(mode="compact", :module="{channel_id: poster.channel}")
	bunt-progress-circular(v-else, size="huge", :page="true")
</template>
<script>
import api from 'lib/api'
import Avatar from 'components/Avatar'
import Chat from 'components/Chat'
import RichTextContent from 'components/RichTextContent'

export default {
	components: { Avatar, Chat, RichTextContent },
	props: {
		posterId: String
	},
	data () {
		return {
			poster: null
		}
	},
	computed: {
	},
	async created () {
		this.poster = await api.call('poster.get', {poster: this.posterId})
	},
	mounted () {
		this.$nextTick(() => {
		})
	},
	methods: {}
}
</script>
<style lang="stylus">
.v-poster
	display: flex
	// flex-direction: column
	min-height: 0
	flex: auto
	.info-sidebar
		display: flex
		flex-direction: column
		min-height: 0
		width: 380px
		flex: none
		border-right: border-separator()
		.info
			display: flex
			flex-direction: column
			padding: 8px
		.category
			font-size: 20px
		.title
			font-size: 18px
		.authors
			color: $clr-secondary-text-light
	.content
		flex: auto
		display: flex
		min-height: 0
		> .c-scrollbars
			align-items: center
			.scroll-content
				max-width: 920px

	.poster
		display: flex
		flex-direction: column
		flex: auto
		.poster-content
			padding: 0 16px 16px
		iframe
			width: 100%
			flex: auto
			height: 600px
			border: 0
			outline: none
	.tags
		display: flex
		.tag
			color: $clr-primary-text-light
			border: 2px solid $clr-primary
			border-radius: 12px
			margin-right: 4px
			padding: 2px 6px
	.presenters
		display: flex
		flex-direction: column
		.presenter
			display: flex
			align-items: center
	.actions
		display: flex
		gap: 8px
		margin: 8px
	.likes
		display: flex
		align-items: center
		font-size: 18px
		cursor: pointer
		.mdi
			font-size: 32px
			color: $clr-pink
	.downloads
		.download
			display: flex
	.chat-sidebar
		display: flex
		flex-direction: column
		min-height: 0
		width: 380px
		flex: none
		border-left: border-separator()
		h3
			margin: 0
			padding: 8px
			border-bottom: border-separator()
</style>
