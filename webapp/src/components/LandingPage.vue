<template lang="pug">
.c-landing-page(v-scrollbar.y="", :style="{'--header-background-color': module.config.header_background_color, '--header-background-image': `url(${module.config.header_background_image})`}")
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
			template(v-if="featuredSessions && featuredSessions.length")
				.header
					h3 {{ $t('LandingPage:sessions:featured:header') }}
					bunt-link-button(:to="{name: 'schedule'}") {{ $t('LandingPage:sessions:featured:link') }}
				session-list(:sessions="featuredSessions")
			.header
				h3 {{ $t('LandingPage:sessions:next:header') }}
				bunt-link-button(:to="{name: 'schedule'}") {{ $t('LandingPage:sessions:next:link') }}
			session-list(:sessions="nextSessions")
		.speakers
			.header
				h3 {{ $t('LandingPage:speakers:header') }}
				bunt-link-button(:to="{name: 'schedule:speakers'}") {{ $t('LandingPage:speakers:link') }}
			.speakers-list(v-if="speakers")
				router-link.speaker(v-for="speaker of speakers.slice(0, 32)", :to="speaker.attendee ? {name: '', params: {}} : { name: 'schedule:speaker', params: { speakerId: speaker.code } }")
					img.avatar(v-if="speaker.avatar", :src="speaker.avatar")
					identicon(v-else, :id="speaker.name")
					.name {{ speaker.name }}
				router-link.additional-speakers(v-if="speakers.length > 32", :to="{name: 'schedule:speakers'}") {{ $t('LandingPage:speakers:more', {additional_speakers: speakers.length - 32}) }}
</template>
<script>
import { mapState, mapGetters } from 'vuex'
import '@splidejs/splide/dist/css/splide.min.css'
import Splide from '@splidejs/splide'
import api from 'lib/api'
import moment from 'lib/timetravelMoment'
import Identicon from 'components/Identicon'
import MarkdownContent from 'components/MarkdownContent'
import SessionList from 'components/SessionList'

export default {
	components: { Identicon, MarkdownContent, SessionList },
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
			return this.sessions.filter(session => session.featured)
		},
		nextSessions () {
			if (!this.sessions) return
			// current or next sessions per room
			const sessions = []
			for (const session of this.sessions) {
				if (!session.room) continue
				if (session.end.isBefore(this.now) || sessions.reduce((acc, s) => s.room === session.room ? ++acc : acc, 0) >= 2) continue
				sessions.push(session)
			}
			return sessions
		},
		speakers () {
			return this.schedule?.speakers.slice().sort((a, b) => a.name.localeCompare(b.name))
		}
	},
	async mounted () {
		// TODO make this configurable?
		const sponsorRoom = this.rooms.find(r => r.id === this.module.config.sponsor_room_id)
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
		background-color: var(--header-background-color)
		background-image: var(--header-background-image)
		background-repeat: no-repeat
		background-size: cover
		background-position: center
		img
			height: 100%
			object-fit: contain
	.content
		display: flex
		justify-content: center
		gap: 32px
		padding: 0 16px
		> *
			flex: 1
			max-width: 640px
			min-width: 0
			display: flex
			flex-direction: column
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
		.bunt-link-button
			themed-button-primary()
	.speakers-list
		display: flex
		flex-wrap: wrap
		justify-content: center
		.speaker
			display: flex
			flex-direction: column
			align-items: center
			gap: 4px
			width: 124px
			cursor: pointer
			padding: 12px 2px
			color: $clr-primary-text-light
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
			padding: 16px 32px 64px
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

	+below('m')
		.content
			flex-direction: column
			align-items: center
			padding: 0 8px
			> *
				max-width: 100%
</style>
