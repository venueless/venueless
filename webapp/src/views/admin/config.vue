<template lang="pug">
.c-admin-config(v-scrollbar.y="")
	.header
		h2 Configuration
	bunt-tabs.tabs-default
		bunt-tab(id="theme", header="Theme")
			theme-config()
		bunt-tab(id="rooms", header="Rooms")
			p Rooms
</template>
<script>
import ThemeConfig from 'components/config/ThemeConfig'

export default {
	name: 'AdminConfig',
	components: { ThemeConfig },
}
</script>
<style lang="stylus">
.c-admin-config
	h2
		margin: 16px

	.bunt-tabs-body
		padding: 16px
</style>
