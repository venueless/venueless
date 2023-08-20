<template lang="pug">
Poll(:poll="pinnedPoll")
</template>
<script>
import { mapGetters } from 'vuex'
import Poll from 'components/Poll'

export default {
	components: { Poll },
	props: {
		room: Object
	},
	data () {
		return {
		}
	},
	computed: {
		...mapGetters('poll', ['pinnedPoll']),
	},
	async created () {},
	async mounted () {
		await this.$nextTick()
	},
	methods: {}
}
</script>
<style lang="stylus">
</style>
