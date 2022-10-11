import { Random, MersenneTwister19937 } from 'random-js'
import * as identiheart from './renderer-identiheart.js'

const hashFunc = function (source) {
	return String(source).split('').reduce(function (a, b) {
		a = ((a << 5) - a) + b.charCodeAt(0)
		return a & a
	}, 0)
}

export function renderSvg (user) {
	const random = new Random(
		MersenneTwister19937.seed(+hashFunc(user.profile?.avatar?.identicon ?? user.profile?.identicon ?? user.id))
	)

	const config = {
		colorPalette: identiheart.definition.colorPalette.defaults
	}

	return identiheart.renderSvg(random, user.profile, config)
}

export function renderUrl (user) {
	return `data:image/svg+xml;base64,${btoa(renderSvg(user).replace(/[\t\n]/g, ''))}`
}
