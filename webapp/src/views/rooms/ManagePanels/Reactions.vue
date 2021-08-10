<template lang="pug">
.c-manage-panel-reactions
	svg(viewBox="0 -1.05 120 1.05", preserveAspectRatio="none").sparklines
		path(v-for="(line, id) of sparklines", :class="[id.replace('+', 'plus-')]", :d="line.path")
	.reactions
		.reaction(v-for="reaction of availableReactions", :class="[reaction.id.replace('+', 'plus-')]")
			.emoji(:style="reaction.style")
			.count {{ rollingReactionsLastMinute[reaction.id] || 0 }}
</template>
<script>
import { mapState } from 'vuex'
import { availableReactions } from 'lib/emoji'
import moment from 'moment'

export default {
	components: {},
	props: {
		showReactionBar: Boolean
	},
	data () {
		return {
			availableReactions,
			reactionsHistory: [],
			now: moment()
		}
	},
	computed: {
		...mapState(['reactions']),
		rollingReactionsLastMinute () {
			const reactions = {}
			for (let i = this.reactionsHistory.length - 1; i >= 0; i--) {
				const item = this.reactionsHistory[i]
				if (this.now.diff(item.timestamp, 'seconds') > 60) break
				for (const [reaction, count] of Object.entries(item.reactions)) {
					if (reactions[reaction] === undefined) reactions[reaction] = 0
					reactions[reaction] += count
				}
			}
			return reactions
		},
		sparklines () {
			const lines = {}
			for (const {id} of availableReactions) {
				lines[id] = {
					data: [],
					path: 'M 120 0'
				}
			}
			for (let i = this.reactionsHistory.length - 1; i >= 0; i--) {
				const item = this.reactionsHistory[i]
				if (this.now.diff(item.timestamp, 'minutes') > 60) break
				for (const {id} of availableReactions) {
					lines[id].data.push(item.reactions[id] || 0)
				}
			}
			let maxCount = 0
			for (const line of Object.values(lines)) {
				maxCount = Math.max(maxCount, ...line.data)
			}
			for (const line of Object.values(lines)) {
				for (let i = 0; i < line.data.length; i++) {
					line.path += `L ${120 - i} ${-1 * line.data[i] / maxCount}`
				}
			}
			return lines
		}
	},
	watch: {
		reactions () {
			if (!this.reactions) return
			const now = moment()
			const last = this.reactionsHistory[this.reactionsHistory.length - 1]
			if (!last || now.diff(last.timestamp, 'seconds') > 30) {
				this.reactionsHistory.push({
					timestamp: now,
					reactions: this.reactions
				})
			} else {
				for (const [reaction, count] of Object.entries(this.reactions)) {
					if (last.reactions[reaction] === undefined) last.reactions[reaction] = 0
					last.reactions[reaction] += count
				}
			}
		}
	},
	created () {
		this.nowInterval = setInterval(() => {
			this.now = moment()
			// fill history with empty data
			const last = this.reactionsHistory[this.reactionsHistory.length - 1]
			if (!last || this.now.diff(last.timestamp, 'seconds') > 30) {
				this.reactionsHistory.push({
					timestamp: this.now,
					reactions: {}
				})
			}
		}, 1000)
	},
	beforeDestroy () {
		clearInterval(this.nowInterval)
	},
	methods: {
	}
}
</script>
<style lang="stylus">
.c-manage-panel-reactions
	display: flex
	flex-direction: column
	.sparklines
		height: 60px
		path
			fill: none
			stroke: black
			vector-effect: non-scaling-stroke
			stroke-width: 2px
			&.clap
				stroke: $clr-green
			&.heart
				stroke: $clr-pink
			&.plus-1
				stroke: $clr-deep-orange
			&.rolling_on_the_floor_laughing
				stroke: $clr-blue
			&.open_mouth
				stroke: $clr-purple
	.reactions
		display: flex
	.reaction
		flex: auto
		display: flex
		flex-direction: column
		align-items: center
		padding: 8px 0
		&.clap
			border-top: 4px solid $clr-green
		&.heart
			border-top: 4px solid $clr-pink
		&.plus-1
			border-top: 4px solid $clr-deep-orange
		&.rolling_on_the_floor_laughing
			border-top: 4px solid $clr-blue
		&.open_mouth
			border-top: 4px solid $clr-purple
	.emoji
		height: 36px
		width: @height
		display: inline-block
		background-image: url("~emoji-datasource-twitter/img/twitter/sheets-256/64.png")
		background-size: 5700% 5700%
		image-rendering: -webkit-optimize-contrast
		margin-bottom: 8px
</style>
