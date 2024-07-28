// moment does not let us clone and only locally override `now`
// we need to get a clean instance to manipulate
// import config from 'config'
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
import moment2 from 'moment?timetraveling'
import momentTimezone from 'moment-timezone'

moment2.now = function () { return '2018-01-01T00:00:00Z' }
console.log('moments', moment(), moment2(), momentTimezone())

export default moment
