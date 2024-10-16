/* global ENV_DEVELOPMENT */
import i18next from 'i18next'
import config from 'config'
// Vue.use(VueI18n)
//
// function loadLocaleMessages () {
// 	const locales = require.context('./locales', true, /[A-Za-z0-9-_,\s]+\.js$/i)
// 	const messages = {}
// 	locales.keys().forEach(key => {
// 		const matched = key.match(/([A-Za-z0-9-_]+)\./i)
// 		if (matched && matched.length > 1) {
// 			const locale = matched[1]
// 			messages[locale] = Object.assign({}, locales(key).default, config.theme?.textOverwrites ?? {})
// 		}
// 	})
// 	return messages
// }
//
// export default new VueI18n({
// 	locale: config.locale || 'en',
// 	fallbackLocale: 'en',
// 	messages: loadLocaleMessages()
// })

export default i18next

export function localize (string) {
	if (typeof string === 'string') return string
	for (const lang of i18next.languages) {
		if (string[lang]) return string[lang]
	}
	return Object.values(string)[0]
}

export async function init (app) {
	await i18next
		// dynamic locale loader using webpack chunks
		.use({
			type: 'backend',
			init () {},
			async read (language, namespace, callback) {
				try {
					const locale = await import(/* webpackChunkName: "locale-[request]" */ `./locales/${language}.json`)
					callback(null, locale.default)
				} catch (error) {
					callback(error)
				}
			}
		})
		// inject custom theme text overwrites
		.use({
			type: 'postProcessor',
			name: 'themeOverwrites',
			process (value, key) {
				return config.theme?.textOverwrites?.[key[0]] ?? value
			}
		})
		.init({
			lng: localStorage.userLanguage || config.defaultLocale || config.locale || 'en',
			fallbackLng: 'en',
			debug: ENV_DEVELOPMENT,
			keySeparator: false,
			nsSeparator: false,
			postProcess: ['themeOverwrites']
		})
	app.config.globalProperties.$i18n = i18next
	app.config.globalProperties.$t = i18next.t.bind(i18next)
	app.config.globalProperties.$localize = localize
}
