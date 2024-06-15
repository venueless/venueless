<script setup>
import { watch, onMounted } from 'vue'
import { useStore } from 'vuex'
import moment from 'lib/timetravelMoment'
import PollSlide from './Poll'
import VoteSlide from './Vote'
import QuestionSlide from './Question'
import NextSessionSlide from './NextSession'
import CurrentSessionSlide from './CurrentSession'
import ViewersSlide from './Viewers'

const { room, config } = defineProps({
	room: Object,
	config: Object
})

const store = useStore()

const SLIDE_INTERVAL = ENV_DEVELOPMENT ? 2000 : 20000

function isSlideEnabled (slide) {
	return !config.slides || config.slides[slide] !== false
}

const SLIDES = [{
	id: 'poll',
	condition () {
		return isSlideEnabled('pinned_poll') && !!store.getters['poll/pinnedPoll']
	},
	watch () {
		return isSlideEnabled('pinned_poll') && store.getters['poll/pinnedPoll']
	},
	priority: 10,
	component: PollSlide
}, {
	id: 'vote',
	condition () {
		return isSlideEnabled('pinned_poll_voting') && !!store.getters['poll/pinnedPoll']
	},
	priority: 10,
	component: VoteSlide
}, {
	id: 'question',
	condition () {
		return isSlideEnabled('pinned_question') && !!store.getters['question/pinnedQuestion']
	},
	watch () {
		return isSlideEnabled('pinned_question') && store.getters['question/pinnedQuestion']
	},
	priority: 10,
	component: QuestionSlide
}, {
	id: 'nextSession',
	condition () {
		if (!isSlideEnabled('next_session')) return false
		const currentSession = store.getters['schedule/currentSessionPerRoom']?.[room.id]?.session
		const nextSession = store.getters['schedule/sessions']?.find(session => session.room === room && session.start.isAfter(store.state.now))
		return !!nextSession && (!currentSession || !currentSession.id || currentSession.end.isBefore(moment().add(10, 'minutes')))
	},
	watch () {
		return isSlideEnabled('next_session') && store.getters['schedule/sessions']
	},
	priority: 1,
	component: NextSessionSlide
}, {
	id: 'currentSession',
	condition () {
		if (!isSlideEnabled('current_session')) return false
		const currentSession = store.getters['schedule/currentSessionPerRoom']?.[room.id]?.session
		return !!currentSession && currentSession.id // sessions without id are breaks
	},
	watch () {
		return isSlideEnabled('current_session') && store.getters['schedule/sessions']
	},
	priority: 1,
	component: CurrentSessionSlide
}, {
	id: 'viewers',
	condition () {
		return isSlideEnabled('viewers') && store.state.roomViewers?.length > 0
	},
	watch () {
		return isSlideEnabled('viewers') && store.state.roomViewers
	},
	priority: 1,
	component: ViewersSlide
}]

let activeSlide = $shallowRef(SLIDES[0])

let slideTimer

function nextSlide () {
	if (slideTimer) clearTimeout(slideTimer)
	let index = SLIDES.indexOf(activeSlide)
	const stoppingIndex = Math.max(0, index)
	let newSlide
	do {
		index++
		if (index >= SLIDES.length) index = 0
		const slide = SLIDES[index]
		if (
			slide.priority > (newSlide?.priority ?? 0) &&
			slide.condition()
		) newSlide = SLIDES[index]
	} while (index !== stoppingIndex)
	activeSlide = newSlide
	slideTimer = setTimeout(nextSlide, SLIDE_INTERVAL)
}

for (const slide of SLIDES) {
		if (slide.watch) {
			watch(slide.watch, () => {
				if (slide.condition()) {
					activeSlide = slide
				} else {
					nextSlide()
				}
			})
		}
	}

onMounted(() => {
	nextSlide()
	
})

</script>
<template lang="pug">
.v-standalone-kiosk
	transition(name="kiosk")
		.slide(v-if="activeSlide", :key="activeSlide.id")
			component(:is="activeSlide.component", :room="room")
</template>
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
		&.kiosk-enter-from
			translate: -100vw 0
		&.kiosk-leave-to
			translate: 100vw 0
</style>
