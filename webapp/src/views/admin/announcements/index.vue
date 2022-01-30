<template lang="pug">
.c-admin-announcements
	.ui-page-header
		h1 Announcements
		.actions
			bunt-link-button#btn-create(:to="{name: 'admin:announcements:item', params: {announcementId: 'new'}}") Create a new announcement
	.page-content(v-if="announcements")
		.announcements-list
			.header
				.active active
				.text text
				.show-until show until
			.tbody
				router-link.announcement.table-row(v-for="announcement of announcements", :to="{name: 'admin:announcements:item', params: {announcementId: announcement.id}}")
					.active.mdi(:class="{'is-active': announcement.is_active, 'mdi-check-bold': announcement.is_active, 'mdi-close-thick': !announcement.is_active}")
					.text {{ announcement.text }}
					.show-until {{ announcement.show_until }}
		router-view(:announcements="announcements")
	bunt-progress-circular(v-else, size="huge", :page="true")
</template>
<script>
import api from 'lib/api'

export default {
	components: {},
	data () {
		return {
			announcements: null,
			activeAnnouncement: null
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
				&.router-link-exact-active
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
</style>
