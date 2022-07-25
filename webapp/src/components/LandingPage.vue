<template lang="pug">
.c-landing-page(v-scrollbar.y="", :style="{'--header-background': module.config.header_background_color}")
	.hero
		img(:src="module.config.header_image")
	.sponsors.splide(ref="sponsors")
		.splide__track
			ul.splide__list
				li.splide__slide(v-for="sponsor of sponsors")
					router-link(:to="{name: 'exhibitor', params: {exhibitorId: sponsor.id}}")
						img.sponsor(:src="sponsor.logo", :alt="sponsor.name")
	.content
		.schedule
			.header
				h3 Featured Sessions
				router-link(:to="{name: 'schedule'}") full schedule
			.sessions
				.session(v-for="{session, state}, index of featuredSessions", :class="{live: state.isLive}")
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
			.header
				h3 Sessions Happening Soon
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
				h3 Our Speakers
				router-link(:to="{name: 'schedule:speakers'}") full list
			.speakers-list(v-if="speakers")
				.speaker(v-for="speaker of speakers.slice(0, 32)")
					img.avatar(v-if="speaker.avatar", :src="speaker.avatar")
					identicon(v-else, :id="speaker.name")
					.name {{ speaker.name }}
				router-link(:to="{name: 'schedule:speakers'}").additional-speakers(v-if="speakers.length > 32") and {{ speakers.length - 32 }} more
</template>
<script>
import { mapState, mapGetters } from 'vuex'
import '@splidejs/splide/dist/css/splide.min.css'
import Splide from '@splidejs/splide'
import api from 'lib/api'
import moment from 'lib/timetravelMoment'
import Identicon from 'components/Identicon'
import MarkdownContent from 'components/MarkdownContent'

export default {
	components: { Identicon, MarkdownContent },
	props: {
		module: Object
	},
	data () {
		return {
			moment,
			sponsors: null
		}
	},
	computed: {
		...mapState(['now', 'rooms']),
		...mapState('schedule', ['schedule']),
		...mapGetters('schedule', ['sessions']),
		featuredSessions () {
			if (!this.sessions) return
			// return this.sessions.filter(session => session.featured)
			// TODO remove mock data
			return this.sessions.slice(0, 3).map(session => ({session, state: this.getSessionState(session)}))
		},
		nextSessions () {
			if (!this.sessions) return
			// current or next sessions per room
			const sessions = []
			// TODO filter out sessions with no venueless room?
			for (const session of this.sessions) {
				if (!session.room) continue
				if (session.end.isBefore(this.now) || sessions.reduce((acc, s) => s.session.room === session.room ? ++acc : acc, 0) >= 2) continue
				sessions.push({session, state: this.getSessionState(session)})
			}
			return sessions
		},
		speakers () {
			return this.schedule?.speakers.slice().sort((a, b) => a.name.localeCompare(b.name))
		}
	},
	async mounted () {
		// TODO make this configurable?
		const sponsorRoom = this.rooms.find(r => r.modules[0].type === 'exhibition.native')
		if (!sponsorRoom) return
		this.sponsors = (await api.call('exhibition.list', {room: sponsorRoom.id})).exhibitors
		await this.$nextTick()
		new Splide(this.$refs.sponsors, {
			type: 'loop',
			autoWidth: true,
			clones: 50,
			focus: 'center',
			// padding: '16px 0'
		}).mount()
	},
	methods: {
		getSessionState (session) {
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
				flex: none
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
		.additional-speakers
			font-size: 18px
			font-weight: 600
			align-self: center
			margin: 0 auto
	.sponsors
		padding: 8px 0 16px 0
		.sponsor
			height: 10vh
			max-height: 10vh
			max-width: unquote("min(260px, 90vw)")
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
