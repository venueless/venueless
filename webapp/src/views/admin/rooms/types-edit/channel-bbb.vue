<template lang="pug">
.c-channel-bbb-settings
	bunt-checkbox(v-model="module.config.record", name="record", label="Allow recording (needs to be set before first join)")
	bunt-checkbox(v-model="module.config.hide_presentation", name="hide-presentation", label="Hide presentation when users join")
	bunt-checkbox(v-model="module.config.waiting_room", name="waiting-room", label="Put new users in waiting room first (needs to be set before first join)")
	bunt-checkbox(v-model="module.config.auto_microphone", name="auto-microphone", label="Auto-join users with microphone on (skip dialog asking how to join)")
	bunt-checkbox(v-model="module.config.auto_camera", name="auto-camera", label="Auto-join users with camera on")
	bunt-checkbox(v-model="module.config.bbb_mute_on_start", name="bbb-mute-on-start", label="Auto-mute users")
	bunt-checkbox(v-model="module.config.bbb_disable_cam", name="bbb-disable-cam", label="Disable camera for non-moderators")
	bunt-checkbox(v-model="module.config.bbb_disable_chat", name="bbb-disable-chat", label="Disable public chat for non-moderators")
	bunt-input(v-model="module.config.voice_bridge", name="voice-bridge", label="Voice Bridge ID")
	bunt-input(v-model="module.config.prefer_server", name="prefer-server", label="Prefer Server with ID")
	upload-url-input(v-model="module.config.presentation", name="presentation", label="Initial presentation")
	sidebar-addons(v-bind="$props")
</template>
<script>
import UploadUrlInput from 'components/UploadUrlInput'
import mixin from './mixin'
import SidebarAddons from './SidebarAddons'

export default {
	components: { UploadUrlInput, SidebarAddons },
	mixins: [mixin],
	computed: {
		module () {
			return this.modules['call.bigbluebutton']
		}
	}
}
</script>
<style lang="stylus">
</style>
