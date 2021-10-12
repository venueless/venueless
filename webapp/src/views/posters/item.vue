<template lang="pug">
.v-poster(v-scrollbar.y="")
	h2 {{ poster.category }}
	.tags
		.tag(v-for="tag of poster.tags") {{ tag }}
	h1.title {{ poster.title }}
	p.authors {{ poster.authors.join(', ') }}
	a.poster(:href="poster.poster_url", target="_blank", title="click me to open poster pdf")
		img(:src="poster.poster_preview")
	.presenters
		h3 Presenters
		.presenter(v-for="user in poster.presenters")
			avatar(:user="user", :size="36")
			span.display-name {{ user ? user.profile.display_name : '' }}
	.actions
		bunt-button(tooltip="opens room linked via schedule") goto session
		bunt-button(tooltip="opens text chat") discuss
		.likes(v-tooltip="'imagine clicking does something'")
			.mdi.mdi-heart-outline
			.count {{ poster.likes }}
	p.abstract {{ poster.abstract }}
	.downloads(v-if="poster.files.length > 0")
		h2 {{ $t("Exhibitor:downloads-headline:text") }}
		a.download(v-for="file in poster.files", :href="file.url", target="_blank")
			.mdi.mdi-file-pdf-outline(v-if="file.url.toLowerCase().endsWith('pdf')")
			.filename {{ file.display_text }}

</template>
<script>
import posters from 'posters'
import Avatar from 'components/Avatar'

export default {
	components: { Avatar},
	props: {
		posterId: String
	},
	data () {
		return {
		}
	},
	computed: {
		poster () {
			return posters.find(poster => poster.id === this.posterId)
		}
	},
	created () {},
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
	flex-direction: column
	.poster
		img
			max-height: 560px
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
		align-items: center
		gap: 8px
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
</style>
