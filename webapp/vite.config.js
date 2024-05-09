import path from 'path'
import vue from '@vitejs/plugin-vue'
import ReactivityTransform from '@vue-macros/reactivity-transform/vite'
import { viteStaticCopy } from 'vite-plugin-static-copy'
import { VitePWA } from 'vite-plugin-pwa'
// import { visualizer } from 'rollup-plugin-visualizer'

import BuntpapierStylus from 'buntpapier/stylus.js'

const stylusOptions = {
	paths: [
		path.resolve(__dirname, './src/styles'),
		'node_modules'
	],
	use: [BuntpapierStylus({implicit: false})],
	imports: [
		'buntpapier/buntpapier/index.styl',
		path.resolve(__dirname, 'src/styles/variables.styl'),
		path.resolve(__dirname, 'src/styles/themed-buntpapier.styl'),
	]
}

export default {
	server: {
		host: '0.0.0.0',
		port: 8880,
		proxy: process.env.WITH_PROXY ? {
			'/api': 'http://localhost:8375',
			'/ws': {
				target: 'ws://localhost:8375',
				ws: true,
			},
		} : null
	},
	plugins:[
		vue(),
		ReactivityTransform(),
		// globbing thousands of emojis absolutely wrecks vite, let's just static copy them, they likely won't change
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/twemoji-emojis/vendor/svg/*.svg',
					dest: 'emoji'
				}
			]
		}),
		VitePWA({
			srcDir: "src",
			filename: "service-worker.js",
			strategies: "injectManifest",
			injectRegister: false,
			manifest: {
				name: "Venueless",
				short_name: "Venueless",
				description: "Venueless is a virtual conference platform",
				theme_color: "#673ab7",
				icons: [
					{
						"src": "pwa-64x64.png",
						"sizes": "64x64",
						"type": "image/png"
					},
					{
						"src": "pwa-192x192.png",
						"sizes": "192x192",
						"type": "image/png"
					},
					{
						"src": "pwa-512x512.png",
						"sizes": "512x512",
						"type": "image/png"
					},
					{
						"src": "maskable-icon-512x512.png",
						"sizes": "512x512",
						"type": "image/png",
						"purpose": "maskable"
					}
				]
			},
			injectManifest: {
				injectionPoint: null,
			},
			registerType: 'autoUpdate',
			devOptions: {
				enabled: true,
				type: 'module'
			}
		})
	],
	css: {
		preprocessorOptions: {
			stylus: stylusOptions,
			styl: stylusOptions
		}
	},
	resolve: {
		extensions: ['.js', '.json', '.vue'],
		alias: {
			lodash: 'lodash-es',
			'~': path.resolve(__dirname, 'src'),
			config: path.resolve(__dirname, 'config.js'),
			modernizr$: path.resolve(__dirname, '.modernizrrc'),
			react: 'preact/compat',
			'react-dom': 'preact/compat',
			// 'preact/hooks': 'preact/hooks/dist/hooks.js',
			// vite doesn't have resolve.modules, hardcode all toplevel paths in src
			assets: path.resolve(__dirname, 'src/assets'),
			components: path.resolve(__dirname, 'src/components'),
			lib: path.resolve(__dirname, 'src/lib'),
			locales: path.resolve(__dirname, 'src/locales'),
			router: path.resolve(__dirname, 'src/router'),
			store: path.resolve(__dirname, 'src/store'),
			styles: path.resolve(__dirname, 'src/styles'),
			views: path.resolve(__dirname, 'src/views'),
			features: path.resolve(__dirname, 'src/features'),
			i18n: path.resolve(__dirname, 'src/i18n'),
			theme: path.resolve(__dirname, 'src/theme'),
			'has-emoji': path.resolve(__dirname, 'build/has-emoji/emoji.json')
		}
	},
	// optimizeDeps: {
	// 	exclude: ['buntpapier'],
	// 	include: ['buntpapier > fuzzysearch']
	// },
	optimizeDeps: {
		exclude: ['pdfjs-dist', '@pretalx/schedule', '@resvg/resvg-js', '@resvg/resvg-wasm'],
		// include: ['buntpapier'],
		esbuildOptions: {
			target: 'esnext'
		}
	},
	build: {
		target: 'esnext'
	},
	define: {
		ENV_DEVELOPMENT: process.env.NODE_ENV === 'development',
		RELEASE: `'${process.env.VENUELESS_COMMIT_SHA}'`,
		BASE_URL: `'${process.env.BASE_URL || '/'}'`,
		WITH_PROXY: process.env.WITH_PROXY,
		global: 'globalThis'
	}
}
