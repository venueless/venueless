import Vue from 'vue'
import moment from 'moment'
import api from 'lib/api'

export default {
	namespaced: true,
	state: {
		announcements: []
	},
	getters: {
		visibleAnnouncements (state, getters, rootState) {
			return state.announcements.filter(announcement => announcement.is_active && (!announcement.show_until || announcement.show_until.isAfter(rootState.now)))
		}
	},
	mutations: {
		setAnnouncements (state, announcements) {
			for (const announcement of announcements) {
				if (announcement.show_until) announcement.show_until = moment(announcement.show_until)
			}
			state.announcements = announcements
		}
	},
	actions: {
		async 'api::announcement.created_or_updated' ({state}, announcement) {
			const existingAnnouncement = state.announcements.find(a => a.id === announcement.id)
			if (existingAnnouncement) {
				for (let [key, value] of Object.entries(announcement)) {
					if (key === 'show_until' && value) value = moment(value)
					Vue.set(existingAnnouncement, key, value)
				}
			} else {
				state.announcements.push(announcement)
			}
		}
	}
}
