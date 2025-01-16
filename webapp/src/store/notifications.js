// TODO handle mobile stuff
import theme from 'theme'
import api from 'lib/api'
import { renderUrl as renderIdenticonUrl } from 'lib/identicons'
import { isMobile, supportsNotifications, supportsWebPushNotifications } from 'lib/feature-detect'

const loadSettings = function () {
	try {
		return JSON.parse(localStorage.notificationSettings)
	} catch (e) {}
}

export default {
	namespaced: true,
	state: {
		permission: supportsNotifications && Notification.permission,
		permissionPromptDismissed: !!localStorage.notificationPermissionPromptDismissed,
		askingPermission: false,
		settings: loadSettings() || {
			notify: true,
			playSounds: false
		},
		desktopNotifications: []
	},
	getters: {
		showNotificationPermissionPrompt (state) {
			return supportsNotifications && !state.permissionPromptDismissed && state.permission === 'default'
		},
		shouldNotify (state) {
			return state.permission === 'granted' && !!state.settings.notify
		}
	},
	mutations: {
	},
	actions: {
		async init ({ dispatch }) {
			if (!supportsNotifications || Notification.permission !== 'granted') return
			await dispatch('initPushNotifications')
			// TODO resubscribe to push notifications on error
		},
		async initPushNotifications ({ rootState }) {
			if (!isMobile || !supportsWebPushNotifications) return
			const serviceWorker = await navigator.serviceWorker.register(
				import.meta.env.MODE === 'production' ? '/sw.js' : '/dev-sw.js?dev-sw', { type: import.meta.env.MODE === 'production' ? 'classic' : 'module' }
			)
			serviceWorker.update()
			window.serviceWorker = serviceWorker
			// if (await serviceWorker.pushManager.getSubscription()) return
			await navigator.serviceWorker.ready
			// TODO unsubscribe on error
			const subscription = await serviceWorker.pushManager.subscribe({
				userVisibleOnly: true,
				applicationServerKey: rootState.world.vapid_public_key
			})
			api.call('user.web_push.subscribe', {
				subscription: subscription.toJSON()
			})
		},
		// sets state from browser permission and localStorage
		// TODO prevent switching of settings at app load
		pollExternals ({ state }) {
			state.permission = supportsNotifications && Notification.permission
			state.permissionPromptDismissed = !!localStorage.notificationPermissionPromptDismissed
			const settings = loadSettings()
			if (settings) {
				state.settings = settings
			}
		},
		async askForPermission ({ state, dispatch }) {
			if (!supportsNotifications) return
			state.askingPermission = true
			let permission
			// safari only has callback
			try {
				permission = await Notification.requestPermission()
			} catch {
				permission = await new Promise((resolve) => Notification.requestPermission(resolve))
			}
			state.permission = permission
			await dispatch('initPushNotifications')
			state.askingPermission = false
			dispatch('dismissPermissionPrompt')
		},
		dismissPermissionPrompt ({ state }) {
			state.permissionPromptDismissed = true
			localStorage.notificationPermissionPromptDismissed = true
		},
		updateSettings ({ state }, settings) {
			state.settings = Object.assign({}, state.settings, settings)
			localStorage.notificationSettings = JSON.stringify(state.settings)
		},
		async createDesktopNotification ({ state, getters }, { title, body, tag, user, icon, onClose, onClick }) {
			if (!getters.shouldNotify || document.hasFocus()) return // don't show desktop notification when we have focus
			if (isMobile) return // we shouldn't be getting this AT ALL
			if (user) {
				if (user.profile?.avatar?.url) {
					icon = user.profile.avatar.url
				} else {
					const canvas = document.createElement('canvas')
					canvas.height = 192
					canvas.width = 192
					const img = document.createElement('img')
					img.src = renderIdenticonUrl(user, theme.identicons.style)
					const ctx = canvas.getContext('2d')
					await new Promise((resolve) => {
						img.onload = () => {
							ctx.drawImage(img, 0, 0, 192, 192)
							resolve()
						}
					})
					icon = canvas.toDataURL()
				}
			}
			// TODO set tag to handle multiple tabs
			try {
				const desktopNotification = new Notification(title ?? '', { body, icon, tag })
				if (state.settings.playSounds) {
					const audio = new Audio('/notify.wav')
					audio.play()
				}
				desktopNotification.onclose = () => {
					onClose?.(desktopNotification)
					const index = state.desktopNotifications.indexOf(desktopNotification)
					if (index) state.desktopNotifications.splice(index, 1)
				}
				desktopNotification.onclick = () => {
					window.focus()
					onClick?.(desktopNotification)
				}
				state.desktopNotifications.push(desktopNotification)
				return desktopNotification
			} catch (e) {
				// ignore notifications not working on android. Doesn't seem to be a way to detect this without actively trying to show a notification
				if (e.message !== 'Illegal constructor') throw e
			}
		},
		closeDesktopNotifications ({ state }, fn) {
			for (const desktopNotification of state.desktopNotifications) {
				if (fn(desktopNotification)) desktopNotification.close()
			}
			state.desktopNotifications = state.desktopNotifications.filter(n => !fn(n))
		},
		clearDesktopNotifications ({ state }) {
			for (const desktopNotification of state.desktopNotifications) {
				desktopNotification.close()
			}
			state.desktopNotifications = []
		}
	}
}
