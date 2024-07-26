<template lang="pug">
.c-channel-digitalsamba-settings
	bunt-checkbox(v-model="module.config.waiting_room", name="waiting-room", label="Only allow attendees after moderator joined")
	bunt-checkbox(v-model="module.config.skip_join_screen", name="join-screen", label="Skip join screen that allows to test audio and camera")
	bunt-checkbox(v-model="module.config.mute_on_start", name="bbb-mute-on-start", label="Auto-mute users")
	bunt-checkbox(v-model="module.config.disable_cam_on_start", name="bbb-mute-on-start", label="Auto-disable camera")
	sidebar-addons(v-bind="$props")
</template>
<script>
import mixin from './mixin'
import SidebarAddons from './SidebarAddons'

export default {
	components: { SidebarAddons },
	mixins: [mixin],
	computed: {
		module () {
			return this.modules['call.digitalsamba']
		}
	}
}
</script>
<style lang="stylus">
</style>
