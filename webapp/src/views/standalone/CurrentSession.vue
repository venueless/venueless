<template lang="pug">
.c-standalone-current-session(v-if="currentSession")
	h2 {{ $t('standalone/CurrentSession:header') }}
	Session(:session="currentSession")
</template>
<script>
import { mapState, mapGetters } from 'vuex'
import { Session } from '@pretalx/schedule'

export default {
	components: {Session},
	props: {
		room: Object
	},
	data () {
		return {
		}
	},
	computed: {
		...mapState(['now']),
		...mapGetters('schedule', ['sessions', 'favs']),
		currentSession () {
			if (!this.sessions) return
			return this.$store.getters['schedule/currentSessionPerRoom']?.[this.room.id]?.session
		},
	},
}
</script>
<style lang="stylus">
.c-standalone-current-session
	display: flex
	flex-direction: column
	align-items: center
	h2
		font-size: 3rem
		margin-bottom: 80px
	.c-linear-schedule-session
		scale: 1.8
		min-width: 400px
		max-width: calc(960px / 1.8 - 24px)
</style>
