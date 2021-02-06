<template lang="pug">
.c-channel(:class="{'has-call': hasCall}")
	.ui-page-header
		h2 {{ otherUsers.map(user => user.profile.display_name).join(', ') }}
		bunt-icon-button(@click="startCall", tooltip="start video call", tooltipPlacement="left") phone_outline
	.main
		.channel-call(v-if="hasCall")
			.channel-call-placeholder
		chat(:mode="hasCall ? 'compact' : 'standalone'", :module="{channel_id: channelId}", :showUserlist="false")
</template>
<script>
import { mapState } from 'vuex'
import Chat from 'components/Chat'

export default {
	components: { Chat },
	props: {
		channelId: String
	},
	computed: {
		...mapState(['user']),
		...mapState('chat', ['joinedChannels', 'call']),
		hasCall () {
			return this.call.channel === this.channelId
		},
		channel () {
			return this.joinedChannels?.find(channel => channel.id === this.channelId)
		},
		otherUsers () {
			return this.channel?.members.filter(member => member.id !== this.user.id)
		}
	},
	methods: {
		startCall () {
			const channel = this.channel
			this.$store.dispatch('chat/startCall', {channel})
		}
	}
}
</script>
<style lang="stylus">
.c-channel
	flex: auto
	display: flex
	flex-direction: column
	background-color: $clr-white
	min-height: 0
	.ui-page-header
		padding: 8px 16px
		justify-content: space-between
		h2
			margin: 0
		.bunt-icon-button
			icon-button-style(style: clear)
	.main
		flex: auto
		display: flex
		min-height: 0
		.channel-call
			display: flex
			flex-direction: column
			min-height: 0
			flex: auto
	&.has-call .c-chat
		flex: 380px 0 0

</style>
