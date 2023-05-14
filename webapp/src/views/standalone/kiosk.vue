<template lang="pug">
.v-standalone-kiosk
	transition(name="kiosk")
		.slide(:key="activeSlide.id")
			component(:is="activeSlide.component", :room="room")
</template>
<script>
import PollSlide from './Poll'
// import VoteSlide from './Vote'
import QuestionSlide from './Question'
import NextSessionSlide from './NextSession'
import ViewersSlide from './Viewers'

const SLIDES = [{
	id: 'poll',
	condition () {
		return !!this.$store.getters['poll/pinnedPoll']
	},
	component: PollSlide
// }, {
// 	id: 'vote',
// 	condition () {
// 		return !!this.$store.getters['poll/pinnedPoll']
// 	},
// 	component: VoteSlide
}, {
	id: 'question',
	condition () {
		return !!this.$store.getters['question/pinnedQuestion']
	},
	component: QuestionSlide
}, {
	id: 'nextSession',
	condition () {
		return !!this.$store.getters['schedule/sessions']?.find(session => session.room === this.room && session.start.isAfter(this.now))
	},
	component: NextSessionSlide
}, {
	id: 'viewers',
	condition () {
		return true
	},
	component: ViewersSlide
}]

const SLIDE_INTERVAL = 20000

export default {
	props: {
		room: Object
	},
	data () {
		return {
			activeSlide: SLIDES[0],
		}
	},
	mounted () {
		setTimeout(this.nextSlide.bind(this), SLIDE_INTERVAL)
	},
	methods: {
		nextSlide () {
			let index = SLIDES.indexOf(this.activeSlide)
			let nextSlide
			do {
				index++
				nextSlide = SLIDES[(index) % SLIDES.length]
			} while (!nextSlide.condition.call(this))
			this.activeSlide = nextSlide
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
