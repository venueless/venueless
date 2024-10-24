import api from 'lib/api'

export default {
	namespaced: true,
	state: {
		questions: null
	},
	getters: {
		pinnedQuestion (state) {
			return state.questions?.find(q => q.is_pinned)
		}
	},
	actions: {
		async changeRoom ({ state }, room) {
			state.questions = null
			if (!room) return
			if (room.modules.some(module => module.type === 'question')) {
				state.questions = await api.call('question.list', { room: room.id })
			}
		},
		async submitQuestion ({ state, rootState }, question) {
			const result = await api.call('question.ask', { room: rootState.activeRoom.id, content: question })
			if (state.questions.some(q => q.id === result.question.id)) return
			// add own question to the list since we're not getting a broadcast for own questions waiting in mod queue
			state.questions.push(result.question)
		},
		async vote ({ rootState }, question) {
			await api.call('question.vote', { room: rootState.activeRoom.id, id: question.id, vote: !question.voted })
			question.voted = !question.voted
		},
		approveQuestion ({ rootState }, question) {
			return api.call('question.update', { room: rootState.activeRoom.id, id: question.id, state: 'visible' })
			// update handled in create_or_update
			// TODO error handling
		},
		archiveQuestion ({ rootState }, question) {
			return api.call('question.update', { room: rootState.activeRoom.id, id: question.id, state: 'archived', is_pinned: false })
			// update handled in create_or_update
			// TODO error handling
		},
		unarchiveQuestion ({ rootState }, question) {
			return api.call('question.update', { room: rootState.activeRoom.id, id: question.id, state: 'visible' })
			// update handled in create_or_update
			// TODO error handling
		},
		archiveAll ({ state, rootState }) {
			// just send all updates in parallel
			for (const question of state.questions) {
				api.call('question.update', { room: rootState.activeRoom.id, id: question.id, state: 'archived', is_pinned: false })
			}
		},
		deleteQuestion ({ rootState }, question) {
			return api.call('question.delete', { room: rootState.activeRoom.id, id: question.id })
			// update handled in api::question.deleted
			// TODO error handling
		},
		pinQuestion ({ rootState }, question) {
			return api.call('question.pin', { room: rootState.activeRoom.id, id: question.id })
		},
		// redirect per question menu unpin to global unpin
		unpinQuestion ({ dispatch }) {
			return dispatch('unpinAllQuestions')
		},
		unpinAllQuestions ({ rootState }) {
			return api.call('question.unpin', { room: rootState.activeRoom.id })
		},
		'api::question.created_or_updated' ({ state }, { question }) {
			const existingQuestion = state.questions.find(q => q.id === question.id)
			if (existingQuestion) {
				// assume all keys are already in place
				Object.assign(existingQuestion, question)
			} else {
				state.questions.push(question)
			}
		},
		'api::question.deleted' ({ state }, { id }) {
			const questionIndex = state.questions.findIndex(q => q.id === id)
			if (questionIndex > -1) {
				state.questions.splice(questionIndex, 1)
			}
		},
		'api::question.pinned' ({ state }, { id }) {
			for (const question of state.questions) {
				// unpin all other questions
				question.is_pinned = question.id === id
			}
		},
		'api::question.unpinned' ({ state }) {
			// TODO check room
			for (const question of state.questions) {
				// unpin all questions
				question.is_pinned = false
			}
		}
	}
}
