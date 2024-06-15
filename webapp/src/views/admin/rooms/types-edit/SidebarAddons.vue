<template lang="pug">
.c-sidebar-addons
	h2 Sidebar addons
	bunt-switch(v-model="hasChat", name="enable-chat", label="Enable Chat")
	bunt-switch(v-model="hasQuestions", name="enable-qa", label="Enable Q&A")
	template(v-if="hasQuestions")
		bunt-checkbox(v-model="modules['question'].config.active", label="Active", name="active")
		bunt-checkbox(v-model="modules['question'].config.requires_moderation", label="Questions require moderation", name="requires_moderation")
	bunt-switch(v-if="$features.enabled('polls')", v-model="hasPolls", name="enable-polls", label="Enable Polls")
</template>
<script>
import mixin from './mixin'

export default {
	mixins: [mixin],
	data () {
		return {
		}
	},
	computed: {
		hasChat: {
			get () {
				return !!this.modules['chat.native']
			},
			set (value) {
				if (value) {
					this.addModule('chat.native', { volatile: true })
				} else {
					this.removeModule('chat.native')
				}
			}
		},
		hasQuestions: {
			get () {
				return !!this.modules.question
			},
			set (value) {
				if (value) {
					this.addModule('question', {
						active: true,
						requires_moderation: false
					})
				} else {
					this.removeModule('question')
				}
			}
		},
		hasPolls: {
			get () {
				return !!this.modules.poll
			},
			set (value) {
				if (value) {
					this.addModule('poll', {
						active: true
					})
				} else {
					this.removeModule('poll')
				}
			}
		}
	}
}
</script>
<style lang="stylus">
.c-sidebar-addons
	.bunt-checkbox
		margin-bottom: 8px
</style>
