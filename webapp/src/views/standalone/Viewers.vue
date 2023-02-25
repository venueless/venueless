<template lang="pug">
.c-standalone-viewers
	h1 VIEWERS
	p {{ members }}
</template>
<script>
import { mapState, mapGetters } from 'vuex'
export default {
	components: {},
	props: {
		room: Object
	},
	data () {
		return {
		}
	},
	computed: {
		...mapState('chat', ['members']),
	},
}
</script>
<style lang="stylus">
</style>
