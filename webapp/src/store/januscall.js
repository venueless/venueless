export default {
	namespaced: true,
	state: {
		targetMuteState: false,
	},
	getters: {
	},
	mutations: {
		setTargetMuteState (state, data) {
			state.targetMuteState = data
		}
	},
	actions: {
		'api::janus.muted' ({state, dispatch}, payload) {
			dispatch('setTargetMuteState', true)
		},
	}
}
