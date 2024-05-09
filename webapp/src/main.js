/* global RELEASE */
import { createApp } from 'vue'
import { RouterView } from 'vue-router'
import jwtDecode from 'jwt-decode'
import Buntpapier from 'buntpapier'
import VueVirtualScroller from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { v4 as uuid } from 'uuid'
import moment from 'lib/timetravelMoment' // init timetravel before anything else to avoid module loading race conditions
import router from 'router'
import store from 'store'
import LinkIconButton from 'components/link-icon-button'
import Scrollbars from 'components/Scrollbars'
import MediaQueries from 'components/mixins/media-queries'
import dynamicLineClamp from './components/directives/dynamic-line-clamp'
import 'styles/global.styl'
import 'roboto-fontface'
import 'roboto-fontface/css/roboto-condensed/roboto-condensed-fontface.css'
import '@mdi/font/css/materialdesignicons.css'
import 'quill/dist/quill.core.css'
import '@pretalx/schedule/style'
import 'styles/quill.styl'
import i18n, { init as i18nInit } from 'i18n'
import { emojiPlugin } from 'lib/emoji'
import features from 'features'
import config from 'config'

async function init ({token, inviteToken}) {
	const app = createApp(RouterView)
	app.use(store)
	app.use(router)
	app.use(Buntpapier)
	app.use(VueVirtualScroller)
	app.component('scrollbars', Scrollbars)
	app.component('link-icon-button', LinkIconButton)
	app.use(MediaQueries)
	app.use(emojiPlugin)
	app.use(dynamicLineClamp)
	await i18nInit(app)
	// TODO or provide
	app.config.globalProperties.$features = features

	window.vapp = app.mount('#app')

	app.config.errorHandler = (error, vm, info) => {
		// gracefully fail on vue errors, because otherwise vue thinks it should just stop working completely
		console.error('[VUE] ', info, vm, error)
	}

	store.commit('setUserLocale', i18n.resolvedLanguage)
	store.dispatch('updateUserTimezone', localStorage.userTimezone || moment.tz.guess())

	const route = router.currentRoute.value
	const anonymousRoomId = route.name === 'standalone:anonymous' ? route.params.roomId : null
	if (token) {
		localStorage.token = token
		router.replace(location.pathname)
		store.dispatch('login', {token})
	} else if (localStorage.token) {
		store.dispatch('login', {token: localStorage.token})
	} else if (inviteToken && anonymousRoomId) {
		const clientId = uuid()
		localStorage[`clientId:room:${anonymousRoomId}`] = clientId
		router.replace(location.pathname)
		store.dispatch('login', {clientId, inviteToken})
	} else if (anonymousRoomId && localStorage[`clientId:room:${anonymousRoomId}`]) {
		const clientId = localStorage[`clientId:room:${anonymousRoomId}`]
		store.dispatch('login', {clientId})
	} else {
		console.warn('no token found, login in anonymously')
		let clientId = localStorage.clientId
		if (!clientId) {
			clientId = uuid()
			localStorage.clientId = clientId
		}
		store.dispatch('login', {clientId})
	}
	if (store.state.token && jwtDecode(store.state.token).traits.includes('-kiosk')) {
		store.watch(state => state.user, ({profile}) => {
			router.replace({name: 'standalone:kiosk', params: {roomId: profile.room_id}})
		}, {deep: true})
	}
	store.dispatch('connect')

	setTimeout(() => {
		store.commit('updateNow')
		setInterval(() => {
			store.commit('updateNow')
		}, 60000)
	}, 60000 - Date.now() % 60000) // align with full minutes
	setInterval(() => store.dispatch('notifications/pollExternals'), 1000)
	window.__venueless__release = RELEASE

	window.addEventListener('beforeinstallprompt', function (event) {
		console.log('install prompt', event)
	})
}

const hashParams = new URLSearchParams(window.location.hash.substring(1))

const token = hashParams.get('token')
const inviteToken = hashParams.get('invite')

if (config.externalAuthUrl && !token) {
	window.location = config.externalAuthUrl
} else {
	init({token, inviteToken})
}

// remove all old service workers
// navigator.serviceWorker?.getRegistrations().then((registrations) => {
// 	for (const registration of registrations) {
// 		console.warn('Removed an old service worker')
// 		registration.unregister()
// 	}
// })

if ('serviceWorker' in navigator) {
	const testNotification = new Notification('', {silent: true})
	testNotification.addEventListener('show', () => {
		testNotification.close()
	})
	// THIS WILL TRIGGER A NOTIFICATION PERMISSION REQUEST
	const serviceWorker = await navigator.serviceWorker.register(
		import.meta.env.MODE === 'production' ? '/sw.js' : '/dev-sw.js?dev-sw', { type: import.meta.env.MODE === 'production' ? 'classic' : 'module' }
	)
	serviceWorker.update()
	console.log(serviceWorker)
	window.serviceWorker = serviceWorker
}
