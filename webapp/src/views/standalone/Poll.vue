<template lang="pug">
.c-standalone-poll(v-if="pinnedPoll", :style="{'--total-votes': totalVotes}")
	.poll
		.question
			| {{ pinnedPoll.content }}
		.option(v-for="option of pinnedPoll.options", :class="{'most-votes': optionsWithMostVotes.includes(option.id)}")
			.content {{ option.content }}
			.votes(:style="{'--votes': pinnedPoll.results[option.id]}") {{ totalVotes ? (pinnedPoll.results[option.id] / totalVotes * 100).toFixed() : 0 }}%
	.vote(v-if="linkCache")
		h1 Vote here now:
		.svg(v-html="linkCache.qrcode")
		.url {{ linkCache.shortUrl }}
</template>
<script>
import { mapGetters } from 'vuex'
import QRCode from 'qrcode'
import api from 'lib/api'
let linkCache

export default {
	props: {
		room: Object,
		config: Object
	},
	data () {
		return {
			linkCache
		}
	},
	computed: {
		...mapGetters('poll', ['pinnedPoll']),
		// TODO copypasta
		totalVotes () {
			if (!this.pinnedPoll.results) return 0
			return Object.values(this.pinnedPoll.results).reduce((acc, result) => acc + result, 0)
		},
		optionsWithMostVotes () {
			const sortedResults = Object.entries(this.pinnedPoll.results).slice().sort((a, b) => b[1] - a[1])
			const mostVotes = sortedResults[0][1]
			const optionsWithMostVotes = []
			for (const result of sortedResults) {
				if (result[1] !== mostVotes) break
				optionsWithMostVotes.push(result[0])
			}
			return optionsWithMostVotes
		}
	},
	watch: {
		'config.pinned_poll_show_qr': {
			immediate: true,
			handler: 'createQRCode'
		}
	},
	methods: {
		async createQRCode () {
			if (!this.config?.pinned_poll_show_qr || linkCache?.room === this.room) {
				this.linkCache = null
				return
			}
			const { url } = await api.call('room.invite.anonymous.link', { room: this.room.id })
			linkCache = {
				room: this.room,
				url,
				shortUrl: url.replace(/^https?:\/\//, ''),
				qrcode: await QRCode.toString(url, { type: 'svg', margin: 0 })
			}
			this.linkCache = linkCache
		}
	}
}
</script>
<style lang="stylus">
.c-standalone-poll
	display: flex
	align-items: center
	gap: 64px
	.poll
		min-width: 500px
	.question
		font-size: 36px
		font-weight: 500
		margin-bottom: 32px
	.option
		font-size: 18px
		margin-bottom: 16px
		.votes
			display: flex
			padding: 8px 0
			align-items: center
			&::before
				content: ''
				display: block
				height: 20px
				background-color: $clr-grey-300
				width: calc(var(--votes) / var(--total-votes) * 100%)
				min-width: 4px
				margin-right: 4px
				border-radius: 8px
		&.most-votes
			.votes::before
				background-color: var(--clr-standalone-bg)
				.themed-bg &
					background-color: var(--clr-standalone-fg)
	> .vote
		display: flex
		flex-direction: column
		align-items: center
		h1
			margin: 0
		.svg
			margin: 16px 0
			width: 300px
			svg
				// hide white background
				:first-child
					display: none
		.url
			font-size: 48px

		.themed-bg &
			svg
				path
						stroke: var(--clr-standalone-fg)
</style>
