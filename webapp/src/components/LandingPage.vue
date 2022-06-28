<template lang="pug">
.c-landing-page(v-scrollbar.y="", :style="{'--header-background': module.config.header_background_color}")
	.hero
		img(:src="module.config.header_image")
	.sponsors.splide(ref="sponsors")
		.splide__track
			ul.splide__list
				li.splide__slide(v-for="sponsor of sponsors"): img.sponsor(:src="sponsor.logo", :alt="sponsor.name")
	.content
		.schedule
			.header
				h3 Schedule
				router-link(:to="{name: 'schedule'}") full schedule
			.sessions
				.session(v-for="{session, state}, index of nextSessions", :class="{live: state.isLive}")
					.speaker-avatars
						template(v-for="speaker of session.speakers")
							img(v-if="speaker.avatar", :src="speaker.avatar")
							identicon(v-else, :id="speaker.name")
					.info
						.title-time
							.title {{ $localize(session.title) }}
							.time {{ state.timeString }}
						.speakers-room
							.speakers {{ session.speakers ? session.speakers.map(s => s.name).join(', ') : '' }}
							.room {{ $localize(session.room.name) }}
		.speakers
			.header
				h3 Speakers
				router-link(:to="{name: 'speakers'}") full list
			.speakers-list
				.speaker(v-for="speaker of speakers")
					img.avatar(v-if="speaker.avatar", :src="speaker.avatar")
					identicon(v-else, :id="speaker.name")
					.name {{ speaker.name }}
</template>
<script>
import { mapState, mapGetters } from 'vuex'
import '@splidejs/splide/dist/css/splide.min.css'
import Splide from '@splidejs/splide'
import moment from 'lib/timetravelMoment'
import Identicon from 'components/Identicon'
import MarkdownContent from 'components/MarkdownContent'

// Swiper.use([Autoplay, Navigation, Pagination, Mousewheel, Keyboard, A11y])

export default {
	components: { Identicon, MarkdownContent },
	props: {
		module: Object
	},
	data () {
		return {
			moment,
			sponsors: [{
				name: 'pretix',
				logo: '/sponsors/pretix.svg'
			}, {
				name: 'pretalx',
				logo: '/sponsors/pretalx.svg'
			}, {
				name: 'assegai',
				logo: '/sponsors/assegai.webp'
			}, {
				name: 'feisar',
				logo: '/sponsors/feisar.webp'
			}, {
				name: 'auricom',
				logo: '/sponsors/auricom.webp'
			}, {
				name: 'qirex',
				logo: '/sponsors/qirex.webp'
			}, {
				name: 'tigron',
				logo: '/sponsors/tigron.webp'
			}, {
				name: 'pirhana',
				logo: '/sponsors/pirhana.webp'
			}, {
				name: 'mirage',
				logo: '/sponsors/mirage.webp'
			}, {
				name: 'jebs',
				logo: '/sponsors/jebs.webp'
			}, {
				name: 'kerbodyne',
				logo: '/sponsors/kerbodyne.webp'
			}]
		}
	},
	computed: {
		...mapState(['now']),
		...mapState('schedule', ['schedule']),
		...mapGetters('schedule', ['sessions']),
		nextSessions () {
			if (!this.sessions) return
			const getSessionState = (session) => {
				if (session.start.isBefore(this.now)) {
					return {
						isLive: true,
						timeString: 'live'
					}
				}
				// if (session.start.isBefore(this.now)) {
				// 	return {
				// 		timeString: 'starting soon'
				// 	}
				// }
				return {
					timeString: moment.duration(session.start.diff(this.now)).humanize(true).replace('minutes', 'mins')
				}
			}
			// current or next sessions per room
			const sessions = []
			// TODO filter out sessions with no venueless room?
			for (const session of this.sessions) {
				if (!session.room) continue
				if (session.end.isBefore(this.now) || sessions.reduce((acc, s) => s.session.room === session.room ? ++acc : acc, 0) >= 2) continue
				sessions.push({session, state: getSessionState(session)})
			}
			return sessions
		},
		speakers () {
			return this.schedule?.speakers
		}
	},
	mounted () {
		new Splide(this.$refs.sponsors, {
			type: 'loop',
			autoWidth: true,
			clones: 50,
			focus: 'center',
			// padding: '16px 0'
		}).mount()
	}
}
</script>
<style lang="stylus">
.c-landing-page
	flex: auto
	background-color: $clr-white
	.hero
		height: calc(var(--vh) * 30)
		display: flex
		justify-content: center
		background-color: var(--header-background)
		img
			height: 100%
			object-fit: contain
	.content
		display: flex
		justify-content: center
		gap: 32px
		> *
			flex: 1
			max-width: 640px
	.markdown-content
		padding: 0 16px
		width: 100%
		max-width: 560px
	.header
		display: flex
		justify-content: space-between
		align-items: baseline
		height: 56px
		padding: 0 4px
		h3
			margin: 0
			line-height: 56px
	.sessions
		display: flex
		flex-direction: column
		border: border-separator()
		.session
			height: 56px
			position: relative
			padding: 4px 0
			box-sizing: border-box
			display: flex
			cursor: pointer
			&:not(:last-child)
				border-bottom: border-separator()
			&:hover
				background-color: $clr-grey-100
			.speaker-avatars
				> *:not(:first-child)
					margin-left: -28px
				img
					background-color: $clr-white
					border-radius: 50%
					height: 48px
					width: 48px
					margin: 0 8px 0 4px
					object-fit: cover
			.info
				flex: auto
				min-width: 0
				display: flex
				flex-direction: column
				justify-content: space-between
			.title-time
				flex: none
				display: flex
				align-items: center
				overflow: hidden
			.title
				flex: auto
				// font-weight: 600
				// line-height: 32px
				line-height: 28px
				ellipsis()
			.time
				flex: none
				background-color: $clr-blue-grey-500
				color: $clr-primary-text-dark
				padding: 2px 4px
				margin: 0 4px 4px
				border-radius: 4px
			.speakers-room
				display: flex
				align-items: baseline
				margin-right: 4px
			.speakers, .room
				flex: 1
				color: $clr-secondary-text-light
				ellipsis()
			.room
				margin-left: 4px
				text-align: right
			&.live .time
				background-color: $clr-danger
	.speakers-list
		display: flex
		flex-wrap: wrap
		.speaker
			display: flex
			flex-direction: column
			align-items: center
			gap: 4px
			width: 124px
			cursor: pointer
			padding: 12px 2px
			&:hover
				background-color: $clr-grey-200
			img
				border-radius: 50%
				height: 92px
				width: @height
				object-fit: cover
			.name
				text-align: center
				white-space: break-word
				font-weight: 500
				font-size: 16px
	.sponsors
		padding: 8px 0 16px 0
		.sponsor
			height: 10vh
			max-height: 10vh
			max-width: 90vw
			object-fit: contain
			user-select: none
			margin: 0 24px 16px 24px
		// .splide__pagination
		.splide__pagination__page.is-active
			background-color: var(--clr-primary)
		.splide__arrow
			top: calc(50% - 12px)

	+below('s')
		.hero
			height: auto
	+below('m')
		.content
			flex-direction: column
			align-items: center
			padding: 0 8px
			.sidebar
				width: 100%
				max-width: 560px
</style>
