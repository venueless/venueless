<template lang="pug">
.c-channel-digitalsamba-settings
	bunt-select(v-model="module.config.size", name="size", :options="SAMBA_SIZE_OPTIONS", label="Room size")
	bunt-select(v-model="module.config.tiles", name="tiles", :options="SAMBA_TILE_OPTIONS", label="Tile options")
	bunt-checkbox(v-model="module.config.waiting_room", name="waiting-room", label="Only allow attendees after moderator joined")
	bunt-checkbox(v-model="module.config.skip_join_screen", name="join-screen", label="Skip join screen that allows to test audio and camera")
	bunt-checkbox(v-model="module.config.mute_on_start", name="samba-mute-on-start", label="Auto-mute users")
	bunt-checkbox(v-model="module.config.disable_cam_on_start", name="samba-mute-on-start", label="Auto-disable camera")
	sidebar-addons(v-bind="$props")
	bunt-input(v-if="roomId", v-model="dsRoomId", name="room-id", label="Backend room ID", disabled="true")
</template>
<script>
import mixin from './mixin'

const SAMBA_SIZE_OPTIONS = [
	{ id: 'small', label: 'Small (max. 100 people, max. 100 broadcasters)' },
	{ id: 'large', label: 'Large (max. 2000 people, max. 15 broadcasters)' }
]
const SAMBA_TILE_OPTIONS = [
	{ id: 'all', label: 'Show all broadcaster tiles' },
	{ id: 'cam_mic', label: 'Only show tiles with active camera or microphone' },
	{ id: 'cam', label: 'Only show tiles with active camera' },
]
import SidebarAddons from './SidebarAddons'

export default {
	components: { SidebarAddons },
	mixins: [mixin],
	data () {
		return {
			dsRoomId: null,
			SAMBA_SIZE_OPTIONS,
			SAMBA_TILE_OPTIONS,
		}
	},
	computed: {
		module () {
			const m = this.modules['call.digitalsamba']
			if (!m.config.size) {
				m.config.size = 'small'
			}
			if (!m.config.tiles) {
				m.config.tiles = 'all'
			}
			return m
		}
	},
	async mounted () {
		if (this.roomId) {
			this.dsRoomId = (await api.call('digitalsamba.room_id', { room: this.roomId })).room_id || 'not yet assigned'
		}
	}
}
</script>
<style lang="stylus">
</style>
