import api from 'lib/api'
import router from 'router'
import i18n from 'i18n'

export default {
	namespaced: true,
	state: {
		staffedExhibitions: [],
		contactRequests: [],
	},
	getters: {
		openContactRequests (state) {
			return state.contactRequests.filter(cr => cr.state === 'open' && !cr.weDismissed)
		}
	},
	mutations: {
		setData (state, data) {
			state.staffedExhibitions = data.exhibitors
			state.contactRequests = data.contact_requests
		}
	},
	actions: {
		async acceptContactRequest ({ dispatch, rootState }, contactRequest) {
			// TODO error handling
			const channel = await dispatch('chat/openDirectMessage', { users: [contactRequest.user], hide: false }, { root: true })
			await api.call('exhibition.contact_accept', { contact_request: contactRequest.id, channel: channel.id })
			contactRequest.state = 'answered'
			contactRequest.answered_by = rootState.user
			contactRequest.timestamp = new Date().toISOString()
			// TODO: send greeting message
		},
		dismissContactRequest (_, contactRequest) {
			// dismissing only soft-removes the contact request popup on THIS client
			contactRequest.weDismissed = true
		},
		async 'api::exhibition.exhibition_data_update' ({ commit }, { data }) {
			commit('setData', data)
		},
		// for staff
		'api::exhibition.contact_request' ({ state, dispatch }, data) {
			const contactRequest = data.contact_request
			state.contactRequests.push(contactRequest)
			// TODO better text
			dispatch('notifications/createDesktopNotification', {
				title: contactRequest.user?.profile.display_name,
				body: i18n.t('ContactRequest:notification:text') + ' ' + contactRequest.exhibitor.name,
				user: contactRequest.user,
				// TODO onClose?
				onClick: () => dispatch('acceptContactRequest', contactRequest)
			}, { root: true })
		},
		'api::exhibition.contact_request_close' ({ state }, data) {
			const contactRequest = data.contact_request
			const existingContactRequest = state.contactRequests.find(cb => cb.id === contactRequest.id)
			if (!existingContactRequest) return
			existingContactRequest.state = contactRequest.state
			existingContactRequest.answered_by = contactRequest.answered_by
			existingContactRequest.timestamp = contactRequest.timestamp
		},
		// for client
		async 'api::exhibition.contact_accepted' (_, data) {
			// DM is automatically opening
			await router.push({ name: 'channel', params: { channelId: data.channel } })
		}

	}
}
