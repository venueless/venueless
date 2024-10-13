// import { contentToPlainText } from 'components/ChatContent'
import { initWasm, Resvg } from '@resvg/resvg-wasm'
import resvgWasm from '@resvg/resvg-wasm/index_bg.wasm?url'
import { renderUrl as renderIdenticonUrl, renderSvg } from 'lib/identicons'
// TODO mirror config, theme
// TODO https://developer.mozilla.org/en-US/docs/Web/API/Navigator/setAppBadge

const svgText = `<svg viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<defs>
	<svg id="svg1">
		<rect width="50%" height="50%" fill="green" />
	</svg>
</defs>
<use id="use1" x="0" y="0" xlink:href="#svg1" />
<use id="use2" x="50%" y="50%" xlink:href="#svg1" />
</svg>`

const init = (async () => {
	await initWasm(fetch(resvgWasm))
	const opts = {
		fitTo: {
			mode: 'width',
			value: 500,
		},
		font: {
			loadSystemFonts: false, // It will be faster to disable loading system fonts.
		},
		logLevel: 'off',
	}
	const svg = new Resvg(svgText, opts)
	const pngData = svg.render().asPng()
	// console.log(`data:image/png;base64,${btoa(pngData)}`)
	// console.info('Original SVG Size:', `${svg.width} x ${svg.height}`)
	// console.info('Output PNG Size  :', `${svg.render().width} x ${svg.render().height}`)
})()

addEventListener('install', () => {
	self.skipWaiting()
})

async function handleNotification({ channel_name, event, user, link }) {
	const clients = await self.clients.matchAll({type: 'window'})
	if (clients.some(client => client.visibilityState === 'visible')) return
	await init
	let icon
	if (user) {
		if (user.profile?.avatar?.url) {
			icon = user.profile.avatar.url
		} else {
			const svg = new Resvg(svgText, {
				fitTo: { mode: 'width', value: 192 },
				font: {
					loadSystemFonts: false
				},
				logLevel: 'off'
			})
			const pngData = svg.render().asPng()
			icon = `data:image/png;base64,${btoa(pngData)}`
		}
	}
	await self.registration.showNotification(channel_name, {
		body: event.content.body,
		tag: channel_name,
		icon,
		data: {
			link
		}
	})
}

addEventListener('push', (event) => {
	// display notification
	const data = event.data.json()
	event.waitUntil(handleNotification(data))
})

addEventListener('notificationclick', (event) => {
	event.notification.close()

	// This looks to see if the current is already open and
	// focuses if it is
	event.waitUntil((async () => {
		const clients = await self.clients.matchAll({
			type: 'window',
		})
		console.log(clients)
		if (clients[0]) {
			clients[0].focus()
			clients[0].navigate(event.notification.data.link)
		}
	})())
})
