<template lang="pug">
.c-poster-exhibition
	bunt-input#input-search(name="search", placeholder="Search/Filter/Sort", icon="search")
	p Search by everything, filter by category, tags, ?, sort by name, likes
	scrollbars.posters(v-if="posters", y)
		.category(v-for="(posters, category) of categorizedPosters")
			h2 {{ category }}
			router-link.poster(v-for="poster of posters", :to="{name: 'poster', params: {posterId: poster.id}}")
				.content
					.tags
						.tag(v-for="tag of poster.tags") {{ tag }}
					h3.title {{ poster.title }}
					.authors {{ poster.authors.authors.map(a => a.name).join(', ') }}
					rich-text-content.abstract(:content="poster.abstract")
					.actions
						bunt-button {{ $t('Exhibition:more:label') }}
				img.poster-screenshot(:src="poster.poster_preview")
	bunt-progress-circular(v-else, size="huge", :page="true")
</template>
<script>
import api from 'lib/api'
import RichTextContent from 'components/RichTextContent'

export default {
	components: { RichTextContent },
	props: {
		room: Object
	},
	data () {
		return {
			posters: null
		}
	},
	computed: {
		categorizedPosters () {
			const categorizedPosters = {}
			for (const poster of this.posters) {
				if (!categorizedPosters[poster.category]) categorizedPosters[poster.category] = []
				categorizedPosters[poster.category].push(poster)
			}
			return categorizedPosters
		}
	},
	async created () {
		this.posters = (await api.call('poster.list', {room: this.room.id}))
	},
}
</script>
<style lang="stylus">
$grid-size = 280px
$logo-height = 130px
$logo-height-medium = 160px
$logo-height-large = 427px

.c-poster-exhibition
	flex: auto
	display: flex
	flex-direction: column
	min-height: 0
	background-color: $clr-grey-50
	#input-search, p
		width: 100%
		max-width: 1160px
		align-self: center
	.posters .scroll-content
		display: flex
		flex-direction: column
		gap: 8px
		padding: 8px
		align-items: center
	.poster
		background-color: $clr-white
		border: border-separator()
		border-radius: 4px
		display: flex
		padding: 8px
		cursor: pointer
		max-height: 360px
		max-width: 1160px
		box-sizing: border-box
		.content
			display: flex
			flex-direction: column
			flex: 1 1 60%
			padding: 0 16px 0 0
		.tags
			display: flex
			.tag
				color: $clr-primary-text-light
				border: 2px solid $clr-primary
				border-radius: 12px
				margin-right: 4px
				padding: 2px 6px
		.title
			margin: 0 0 8px 0
			line-height: 1.4
		.authors
			color: $clr-secondary-text-light
		.abstract
			margin-top: 12px
			color: $clr-primary-text-light
			display: -webkit-box
			-webkit-line-clamp: 7
			-webkit-box-orient: vertical
			overflow: hidden
		.actions
			flex: auto
			display: flex
			justify-content: flex-start
			align-items: flex-end
			.bunt-button
				themed-button-secondary()
		img.poster-screenshot
			object-fit: contain
			max-height: 360px
			min-width: 40%
			flex: 1 1 40%
		&:hover
			border: 1px solid var(--clr-primary)
</style>
