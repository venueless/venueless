<template lang="pug">
.c-admin-announcements
	.ui-page-header
		h1 Announcements
		.actions
			bunt-button#btn-create(@click="newAnnouncement") Create a new announcement
	.page-content(v-if="announcements")
		.announcements-list
			.header
				.active active
				.text text
				.show-until show until
			.tbody
				.announcement.table-row(v-for="announcement of announcements", :class="{selected: activeAnnouncement && announcement.id === activeAnnouncement.id}", @click="activeAnnouncement = Object.assign({}, announcement)")
					.active.mdi(:class="{'is-active': announcement.is_active, 'mdi-check-bold': announcement.is_active, 'mdi-close-thick': !announcement.is_active}")
					.text {{ announcement.text }}
					.show-until {{ announcement.show_until }}
		.announcement(v-if="activeAnnouncement")
			.header
				h2(v-if="!activeAnnouncement.id") New Announcement
				template(v-else)
					h2 Edit Announcement
					.actions
						bunt-button#btn-toggle-is-active(:class="{'is-active': activeAnnouncement.is_active}", :loading="togglingActive", @click="toggleIsActive") {{ !activeAnnouncement.is_active ? 'activate' : 'deactivate' }}
			scrollbars(y)
				bunt-input-outline-container(label="Text", name="text")
					textarea.text(slot-scope="{focus, blur}", @focus="focus", @blur="blur", v-model="activeAnnouncement.text")
				bunt-input.floating-label(name="show-until", label="Show Until", type="datetime-local", v-model="activeAnnouncement.show_until")
				bunt-button#btn-save(:loading="saving", @click="saveActiveAnnouncement") {{ !activeAnnouncement.id ? 'create' : 'save' }}
	bunt-progress-circular(v-else, size="huge", :page="true")
</template>
<script>
import api from 'lib/api'

export default {
	components: {},
	data () {
		return {
			announcements: null,
			activeAnnouncement: null,
			saving: false,
			togglingActive: false
		}
	},
	async created () {
		this.announcements = await api.call('announcement.list')
	},
	async mounted () {
		await this.$nextTick()
	},
	methods: {
		newAnnouncement () {
			this.activeAnnouncement = {
				is_active: false,
				text: '',
				show_until: null
			}
		},
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
@import '~styles/flex-table'

.c-admin-announcements
	display: flex
	flex-direction: column
	min-height: 0
	#btn-create
		themed-button-primary()
	h2
		margin: 16px
	.page-content
		flex: auto
		display: flex
		min-height: 0
		.announcements-list
			flex-table()
			.announcement
				display: flex
				align-items: center
				color: $clr-primary-text-light
				cursor: pointer
				&.selected
					background-color: $clr-grey-200
			.active
				width: 36px
				padding: 0 4px 0 16px
				text-align: center
			.text
				flex: auto
				ellipsis()
			.show-until
				width: 160px
			.announcement
				.active
					color: $clr-danger
					&.is-active
						color: $clr-success
		> .announcement
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
			#btn-save
				themed-button-primary()
				align-self: flex-start
				padding: 0 32px
</style>
