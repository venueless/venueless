import path from 'path'
import vue from '@vitejs/plugin-vue2'
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
		port: 8880
	},
	plugins:[
		vue(),
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
		}
	},
	optimizeDeps: {
		exclude: ['buntpapier'],
		include: ['buntpapier > fuzzysearch']
	},
	define: {
		ENV_DEVELOPMENT: process.env.NODE_ENV === 'development',
		RELEASE: `'${process.env.VENUELESS_COMMIT_SHA}'`
	}
}
