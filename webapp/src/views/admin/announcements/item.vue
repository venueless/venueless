<template lang="pug">
.c-announcement(v-if="announcement", :class="[announcement.state, {expired: announcement.expired}]")
	.header
		h2(v-if="!announcement.id") Draft New Announcement
		template(v-else)
			h2 Edit Announcement
			.actions
				bunt-button#btn-progress-state(v-if="announcement.state !== 'archived'", :loading="settingState", @click="progressState") {{ announcement.state === 'draft' ? 'activate' : 'archive' }}
	scrollbars(y)
		bunt-input-outline-container(label="Text", name="text")
			textarea.text(slot-scope="{focus, blur}", @focus="focus", @blur="blur", v-model="announcement.text")
		bunt-input.floating-label(name="show-until", label="Show Until", type="datetime-local", v-model="announcement.show_until")
		.button-group
			bunt-button(:class="{selected: !announcement.show_until}") forever
			bunt-button +10min
			bunt-button +30min
			bunt-button +1h
			bunt-button +25h
		bunt-button#btn-save(:loading="saving", @click="save") {{ !announcement.id ? 'create' : 'save' }}
</template>
<script>
// TODO
// - disable textarea when active?
import api from 'lib/api'

export default {
	props: {
		announcements: Array,
		announcementId: String
	},
	data () {
		return {
			announcement: null,
			saving: false,
			settingState: false
		}
	},
	computed: {
	},
	watch: {
		announcementId: {
			handler () {
				if (this.announcementId === 'new') {
					this.announcement = {
						is_active: false,
						text: '',
						show_until: null
					}
				} else {
					this.announcement = Object.assign({}, this.announcements.find(a => a.id === this.announcementId))
				}
			},
			immediate: true
		}
	},
	methods: {
		async save () {
			this.saving = true
			if (this.announcement.id) {
				const { announcement } = await api.call('announcement.update', this.announcement)
				const existingAnnouncement = this.announcements.find(a => a.id === announcement.id)
				Object.assign(existingAnnouncement, announcement)
			} else {
				const { announcement } = await api.call('announcement.create', this.announcement)
				// TODO not really best practice
				this.announcements.push(announcement)
				this.$router.push({ name: 'admin:announcements:item', params: {announcementId: announcement.id}})
				this.announcement = Object.assign({}, announcement)
			}
			this.saving = false
		},
		async progressState () {
			this.settingState = true
			const { announcement } = await api.call('announcement.update', {
				id: this.announcement.id,
				state: this.announcement.state === 'draft' ? 'active' : 'archived'
			})
			this.announcement = announcement
			const existingAnnouncement = this.announcements.find(a => a.id === announcement.id)
			Object.assign(existingAnnouncement, announcement)
			this.settingState = false
		}
	}
}
</script>
<style lang="stylus">
.c-announcement
	display: flex
	flex-direction: column
	width: 360px
	border-left: border-separator()
	min-height: 0
	.header
		display: flex
		align-items: center
		height: 48px
		box-sizing: border-box
		padding: 8px
		border-bottom: border-separator()
		h2
			font-size: 20px
			font-weight: 500
			margin: 0
		.actions
			display: flex
			flex: auto
			justify-content: flex-end
			#btn-progress-state
				button-style(color: $clr-danger)
				^[0].draft ^[1..-1]
					button-style(color: $clr-success)
	.scroll-content
		padding: 8px
	.bunt-input-outline-container
		margin: 8px 0
	textarea
		font-family: $font-stack
		font-size: 16px
		background-color: transparent
		border: none
		outline: none
		resize: vertical
		min-height: 250px
		padding: 0 8px
	.bunt-input
		input-style(size: compact)
	// TODO decopypaste
	.button-group
		margin: 4px 0 16px 0
		> .bunt-button
			border-radius: 0
			font-size: 12px
			height: 26px
			padding: 0 12px
			min-width: 0
			&.selected
				themed-button-primary()
			&:not(.selected)
				themed-button-secondary()
				border: 2px solid var(--clr-primary)
			&:first-child
				border-radius: 4px 0 0 4px
			&:last-child
				border-radius: 0 4px 4px 0
			&:not(:last-child)
				border-right: none
	#btn-save
		themed-button-primary()
		align-self: flex-start
		padding: 0 32px
</style>
