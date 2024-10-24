/* global ENV_DEVELOPMENT */
import { cloneDeep } from 'lodash'
let config
if (ENV_DEVELOPMENT || !window.venueless) {
	const hostname = window.location.hostname
	const host = window.location.host
	const isSSL = window.location.protocol === 'https:'
	const wsProtocol = isSSL ? 'wss:' : 'ws:'
	let api = {
		base: `http://${hostname}:8375/api/v1/worlds/sample/`,
		socket: `ws://${hostname}:8375/ws/world/sample/`,
		upload: `http://${hostname}:8375/storage/upload/`,
		scheduleImport: `http://${hostname}:8375/storage/import/`,
		feedback: `http://${hostname}:8375/_feedback/`,
	}
	if (WITH_PROXY) {
		api = {
			base: '/api/v1/worlds/sample/',
			socket: `${wsProtocol}//${host}/ws/world/sample/`,
			// upload: `http://${hostname}:8375/storage/upload/`,
			// scheduleImport: `http://${hostname}:8375/storage/schedule_import/`,
			// feedback: `http://${hostname}:8375/_feedback/`,
		}
	}
	config = {
		api,
		defaultLocale: 'en',
		locales: ['en', 'de', 'pt_BR'],
	}
} else {
	// load from index.html as `window.venueless = {…}`
	config = cloneDeep(window.venueless)
}
export default config
