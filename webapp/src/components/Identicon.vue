<template lang="pug">
img.c-identicon(:src="url")
</template>
<script>
import { renderUrl } from 'lib/identicons'

export default {
	props: {
		user: Object
	},
	computed: {
		url () {
			return renderUrl(this.user)
		}
	}
}
</script>
<style lang="stylus">
.c-identicon
	user-select: none
</style>
