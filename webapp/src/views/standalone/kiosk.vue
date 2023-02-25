<template lang="pug">
.v-standalone-kiosk
	transition(name="kiosk")
		.slide(:key="activeSlide")
			PollSlide(v-if="activeSlide === 'poll'", :room="room")
			VoteSlide(v-else-if="activeSlide === 'vote'", :room="room")
			QuestionSlide(v-else-if="activeSlide === 'question'", :room="room")
			NextSessionSlide(v-else-if="activeSlide === 'nextSession'", :room="room")
			ViewersSlide(v-else-if="activeSlide === 'viewers'", :room="room")
	.reactions
</template>
<script>
import PollSlide from './Poll'
import VoteSlide from './Vote'
import QuestionSlide from './Question'
import NextSessionSlide from './NextSession'
import ViewersSlide from './Viewers'

const SLIDE_ORDER = [
	'poll',
	'vote',
	'question',
	'nextSession',
	'viewers'
]

const SLIDE_INTERVAL = 2000

export default {
	components: {
		PollSlide,
		VoteSlide,
		QuestionSlide,
		NextSessionSlide,
		ViewersSlide
	},
	props: {
		room: Object
	},
	data () {
		return {
			activeSlide: 'poll',
		}
	},
	mounted () {
		setTimeout(this.nextSlide.bind(this), SLIDE_INTERVAL)
	},
	methods: {
		nextSlide () {
			const index = SLIDE_ORDER.indexOf(this.activeSlide)
			this.activeSlide = SLIDE_ORDER[(index + 1) % SLIDE_ORDER.length]
			setTimeout(this.nextSlide.bind(this), SLIDE_INTERVAL)
		}
	}
}
</script>
<style lang="stylus">
.v-standalone-kiosk
	display: flex
	flex-direction: column
	justify-content: center
	align-items: center
	height: 100%
	width: 100%
	position: relative
	> .slide
		position: absolute
		&.kiosk-enter-active, &.kiosk-leave-active
			transition: translate 1s
		&.kiosk-enter
			translate: -100vw 0
		&.kiosk-leave-to
			translate: 100vw 0
</style>
