<template lang="pug">
.c-announcement(v-if="announcement")
	.header
		h2(v-if="!announcement.id") New Announcement
		template(v-else)
			h2 Edit Announcement
			.actions
				bunt-button#btn-toggle-is-active(:class="{'is-active': announcement.is_active}", :loading="togglingActive", @click="toggleIsActive") {{ !announcement.is_active ? 'activate' : 'deactivate' }}
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
		bunt-button#btn-save(:loading="saving", @click="saveActiveAnnouncement") {{ !announcement.id ? 'create' : 'save' }}
</template>
<script>
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
			togglingActive: false
		}
	},
	computed: {},
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
	async created () {
	},
	async mounted () {
		await this.$nextTick()
	},
	methods: {
		async saveActiveAnnouncement () {
			this.saving = true
			if (this.activeAnnouncement.id) {
				const { announcement } = await api.call('announcement.update', this.activeAnnouncement)
				const existingAnnouncement = this.announcements.find(a => a.id === announcement.id)
				Object.assign(existingAnnouncement, announcement)
			} else {
				const { announcement } = await api.call('announcement.create', this.activeAnnouncement)
				this.announcements.push(announcement)
				this.activeAnnouncement = Object.assign({}, announcement)
			}
			this.saving = false
		},
		async toggleIsActive () {
			this.togglingActive = true
			const { announcement } = await api.call('announcement.update', {
				id: this.activeAnnouncement.id,
				is_active: !this.activeAnnouncement.is_active
			})
			this.activeAnnouncement = announcement
			const existingAnnouncement = this.announcements.find(a => a.id === announcement.id)
			Object.assign(existingAnnouncement, announcement)
			this.togglingActive = false
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
			#btn-toggle-is-active
				button-style(color: $clr-success)
				&.is-active
					button-style(color: $clr-danger)
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
