<template lang="pug">
.c-announcement-notification.ui-notification
	.details {{ announcement.text }}
</template>
<script>
export default {
	props: {
		announcement: Object
	},
	data () {
		return {
		}
	},
	computed: {},
	async created () {},
	async mounted () {
		await this.$nextTick()
	},
	methods: {}
}
</script>
<style lang="stylus">
</style>
