<template lang="pug">
.c-admin-config(v-scrollbar.y="")
	.header
		h2 Configuration
	bunt-tabs.tabs-default
		bunt-tab(id="main", header="Main")
			main-config()
		bunt-tab(id="theme", header="Theme")
			theme-config()
		bunt-tab(id="rooms", header="Rooms")
			p Rooms
</template>
<script>
import ThemeConfig from 'components/config/ThemeConfig'
import MainConfig from 'components/config/MainConfig'

export default {
	name: 'AdminConfig',
	components: { ThemeConfig, MainConfig },
}
</script>
<style lang="stylus">
.c-admin-config
	h2
		margin: 16px

	.bunt-tabs-body
		padding: 16px
</style>
