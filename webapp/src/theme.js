// TODO
// - icon button hover background on dark bg
import Color from 'color'
import { kebabCase } from 'lodash'
import config from 'config'

const clamp = (value, max) => Math.min(Math.max(value || 0, 0), max)

// ⁂ "normal" blend of foreground over background, same math and rounding as color-blend@4's normal()
const blend = function (background, foreground) {
	const ba = clamp(background.alpha(), 1)
	const fa = clamp(foreground.alpha(), 1)
	const a = clamp(fa + ba - fa * ba, 1)
	const channel = (bc, fc) => {
		bc = clamp(bc, 255)
		fc = clamp(fc, 255)
		const mixed = (1 - fa / a) * bc + (fa / a) * Math.round((1 - ba) * fc + ba * (fc / 255 * 255))
		return Math.round(clamp(mixed, 255))
	}
	return Color({
		r: channel(background.red(), foreground.red()),
		g: channel(background.green(), foreground.green()),
		b: channel(background.blue(), foreground.blue()),
		alpha: a
	})
}

// returns first color with enough (>=4.5) contrast or failing that, the color with the highest contrast
// on background, alpha gets blended
const firstReadable = function (colors, background = '#FFF', threshold = 4.5) {
	background = Color(background)
	let best
	let bestContrast = 0
	for (let color of colors) {
		color = Color(color)
		const contrast = background.contrast(blend(background, color))
		if (contrast >= threshold) return color
		else if (contrast > bestContrast) {
			best = color
			bestContrast = contrast
		}
	}
	// console.warn('THEME COLOR HAS NOT ENOUGH CONTRAST', best.string(), 'on', background.string(), '=', bestContrast)
	return best
}

const CLR_PRIMARY_TEXT = { LIGHT: Color('rgba(0, 0, 0, .87)'), DARK: Color('rgba(255, 255, 255, 1)') }
const CLR_SECONDARY_TEXT = { LIGHT: Color('rgba(0, 0, 0, .54)'), DARK: Color('rgba(255, 255, 255, .7)') }
const CLR_SECONDARY_TEXT_FALLBACK = { LIGHT: Color('rgba(0, 0, 0, .74)'), DARK: Color('rgba(255, 255, 255, .9)') }
const CLR_DISABLED_TEXT = { LIGHT: Color('rgba(0, 0, 0, .38)'), DARK: Color('rgba(255, 255, 255, .5)') }
const CLR_DIVIDERS = { LIGHT: Color('rgba(255, 255, 255, .63)'), DARK: Color('rgba(255, 255, 255, .63)') }

const DEFAULT_COLORS = {
	primary: '#673ab7',
	sidebar: '#180044',
	bbb_background: '#333333',
}

const DEFAULT_LOGO = {
	url: '/venueless-logo-full-white.svg',
	fitToWidth: false
}

const DEFAULT_IDENTICONS = {
	style: 'identiheart'
}

const configColors = config.theme?.colors

const themeConfig = {
	colors: configColors,
	logo: Object.assign({}, DEFAULT_LOGO, config.theme?.logo),
	streamOfflineImage: config.theme?.streamOfflineImage,
	identicons: Object.assign({}, DEFAULT_IDENTICONS, config.theme?.identicons),
}

const colors = Object.keys(DEFAULT_COLORS).reduce((acc, key) => (acc[key] = Color((configColors ?? DEFAULT_COLORS)[key]), acc), {}) // eslint-disable-line no-sequences

// modded colors
colors.primaryDarken15 = colors.primary.darken(0.15)
colors.primaryDarken20 = colors.primary.darken(0.20)
colors.primaryAlpha60 = colors.primary.alpha(0.6)
colors.primaryAlpha50 = colors.primary.alpha(0.5)
colors.primaryAlpha18 = colors.primary.alpha(0.18)
// TODO hack alpha via rgba(var(--three-numbers), .X)

// text on main background
// TODO support switching main background
colors.textPrimary = firstReadable([CLR_PRIMARY_TEXT.LIGHT, CLR_PRIMARY_TEXT.DARK])
colors.textSecondary = firstReadable([CLR_SECONDARY_TEXT.LIGHT, CLR_SECONDARY_TEXT.DARK])
colors.textDisabled = firstReadable([CLR_DISABLED_TEXT.LIGHT, CLR_DISABLED_TEXT.DARK])
colors.dividers = firstReadable([CLR_DIVIDERS.LIGHT, CLR_DIVIDERS.DARK])

// button + inputs
colors.inputPrimaryBg = colors.primary
colors.inputPrimaryFg = firstReadable([CLR_PRIMARY_TEXT.LIGHT, CLR_PRIMARY_TEXT.DARK], colors.primary)
colors.inputPrimaryBgDarken = colors.primary.darken(0.15)
// secondary inputs are transparent
colors.inputSecondaryFg = colors.primary
colors.inputSecondaryFgAlpha = colors.primary.alpha(0.08)
// sidebar
colors.sidebarTextPrimary = firstReadable([CLR_PRIMARY_TEXT.LIGHT, CLR_PRIMARY_TEXT.DARK], colors.sidebar)
colors.sidebarTextSecondary = firstReadable([CLR_SECONDARY_TEXT.LIGHT, CLR_SECONDARY_TEXT_FALLBACK.LIGHT, CLR_SECONDARY_TEXT.DARK, CLR_SECONDARY_TEXT_FALLBACK.DARK], colors.sidebar)
colors.sidebarTextDisabled = firstReadable([CLR_DISABLED_TEXT.LIGHT, CLR_DISABLED_TEXT.DARK], colors.sidebar)
colors.sidebarActiveBg = firstReadable(['rgba(0, 0, 0, 0.08)', 'rgba(255, 255, 255, 0.4)'], colors.sidebar)
colors.sidebarActiveFg = firstReadable([CLR_PRIMARY_TEXT.LIGHT, CLR_PRIMARY_TEXT.DARK], colors.sidebar)
colors.sidebarHoverBg = firstReadable(['rgba(0, 0, 0, 0.12)', 'rgba(255, 255, 255, 0.3)'], colors.sidebar)
colors.sidebarHoverFg = firstReadable([CLR_PRIMARY_TEXT.LIGHT, CLR_PRIMARY_TEXT.DARK], colors.sidebar)

// TODO warn if contrast if failing

const themeVariables = {}
for (const [key, value] of Object.entries(colors)) {
	themeVariables[`--clr-${kebabCase(key)}`] = value.string()
}

export default themeConfig
export { themeVariables, colors, DEFAULT_COLORS, DEFAULT_LOGO, DEFAULT_IDENTICONS }

export function computeForegroundColor (bgColor) {
	return firstReadable([CLR_PRIMARY_TEXT.LIGHT, CLR_PRIMARY_TEXT.DARK], bgColor)
}

const root = document.documentElement

for (const [key, value] of Object.entries(themeVariables)) {
	root.style.setProperty(key, value)
}
