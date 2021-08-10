<template lang="pug">
.c-reactions-bar(:class="{expanded}")
	.actions(@click="expand")
		bunt-icon-button(v-for="reaction of availableReactions", @click.stop="react(reaction.id)")
			.emoji(:style="reaction.style")
</template>
<script>
import { availableReactions } from 'lib/emoji'

export default {
	props: {
		expanded: Boolean
	},
	data () {
		return {
			availableReactions
		}
	},
	methods: {
		expand () {
			if (this.expanded) return
			this.$emit('expand')
		},
		react (id) {
			this.$store.dispatch('addReaction', id)
			// TODO display immediately and add own cooldown
		}
	}
}
</script>
<style lang="stylus">
.c-reactions-bar
	position: relative
	width: 64px
	height: 56px
	.actions
		position: absolute
		bottom: 5px
		left: 0
		display: flex
		pointer-events: all
		background-color: $clr-white
		border: border-separator()
		border-radius: 24px
		padding: 4px
		transition: transform .3s ease
	.bunt-icon-button
		icon-button-style()
		&:not(:first-child)
			margin-left: 8px
	.emoji
		height: 28px
		width: @height
		display: inline-block
		background-image: url("~emoji-datasource-twitter/img/twitter/sheets-256/64.png")
		background-size: 5700% 5700%
		image-rendering: -webkit-optimize-contrast
	&:not(.expanded)
		.actions:hover
			cursor: pointer
			background-color: $clr-grey-100
		.bunt-icon-button
			pointer-events: none
	&.expanded
		.actions
			transform: translateX(calc(64px - 100% - 16px))
</style>
