/* globals ENV_DEVELOPMENT */
import { ref } from 'vue'
import {
	helpers,
	required as _required,
	maxLength as _maxLength,
	minLength as _minLength,
	email as _email,
	integer as _integer,
	maxValue as _maxValue,
	minValue as _minValue,
	url as _url
} from '@vuelidate/validators/dist/raw.mjs'

export const required = message => helpers.withMessage(message, _required)
export const email = message => helpers.withMessage(message, _email)
export const maxLength = (length, message) => helpers.withMessage(message, _maxLength(length))
export const minLength = (length, message) => helpers.withMessage(message, _minLength(length))
export const integer = message => helpers.withMessage(message, _integer)
export const maxValue = (maxVal, message) => helpers.withMessage(message, _maxValue(maxVal))
export const minValue = (minVal, message) => helpers.withMessage(message, _minValue(minVal))
export const color = message => helpers.withMessage(message, helpers.regex(/^#([a-zA-Z0-9]{3}|[a-zA-Z0-9]{6})$/))

// The strictest regex for YouTube video IDs is probably [0-9A-Za-z_-]{10}[048AEIMQUYcgkosw]
// as per https://webapps.stackexchange.com/questions/54443/format-for-id-of-youtube-video
// but let's not count on YouTube not changing their format. Our main goal here is to prevent
// users from entering full URLs.
export const youtubeid = message => helpers.withMessage(message, helpers.regex(/^[0-9A-Za-z_-]{5,}$/))

const relative = helpers.regex(/^\/.*$/)
const devurl = helpers.regex(/^http:\/\/localhost.*$/) // vuelidate does not allow localhost

export const url = message => helpers.withMessage(message, (value) => (!helpers.req(value) || _url(value) || relative(value) || (ENV_DEVELOPMENT && devurl(value))))

export const isJson = () => {
	return helpers.withMessage(({ $response }) => $response?.message, value => {
		if (!value || value.length === 0) return { $valid: true }
		try {
			JSON.parse(value)
			return { $valid: true }
		} catch (exception) {
			return {
				$valid: false,
				message: exception.message
			}
		}
	})
}
