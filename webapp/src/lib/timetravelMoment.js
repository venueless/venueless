// moment does not let us clone and only locally override `now`
// we need to get a clean instance to manipulate
// delete require.cache[require.resolve('moment')]
// const moment = require('moment-timezone')
// moment.locale(config.dateLocale || 'en-ie') // use ireland for 24h clock
// // moment.tz.setDefault('America/New_York')

// for (const key of Object.keys(require.cache)) {
// 	if (!key.includes('node_modules/moment')) continue
// 	delete require.cache[key]
// }
// // conf the global moment instance here
// const mainMoment = require('moment')
// mainMoment.locale(config.dateLocale || 'en-ie') // use ireland for 24h clock
// if (config.timetravelTo) {
// 	const timetravelTimestamp = moment(config.timetravelTo).valueOf()
// 	moment.now = function () { return timetravelTimestamp }
// 	console.warn('timetraveling to', moment()._d)
// }

import moment from 'moment'
// import moment2 from 'moment?timetraveling'
import 'moment-timezone'
// just load all relevant locales
// TODO figure this out correctly to save a bit of bundle size
import 'moment/dist/locale/en-ie'
import 'moment/dist/locale/de'
import 'moment/dist/locale/pt-br'
import config from 'config'

const locale = config.dateLocale || 'en-ie'
// const localeModules = import.meta.glob('../../node_modules/moment/dist/locale/*.js')
// console.log('localeModules', localeModules)
// doesn't work in build, somehow the file does never finish loading
// const localeModule = (await import(`../../node_modules/moment/dist/locale/${locale}.js`)).default
// moment.locale(locale, localeModule._config)

moment.locale(locale) // use ireland for 24h clock

// moment2.now = function () { return '2018-01-01T00:00:00Z' }

export default moment
