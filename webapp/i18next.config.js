import { defineConfig } from 'i18next-cli'
import vuePug from './build/i18next-vue-pug.js'

export default defineConfig({
	// Only English is extracted, the other locale files are owned by Weblate
	locales: ['en'],
	extract: {
		input: ['src/**/*.{vue,js}'],
		output: 'src/locales/{{language}}.json',
		defaultNS: false,
		keySeparator: false,
		nsSeparator: false,
		functions: ['$t', '*.$t', 't', '*.t'],
		sort: true,
		indentation: 2,
		// Keys built at runtime from a variable
		preservePatterns: [
			'PosterHall:filter:field-*',
			'RoomsSidebar:users-tooltip:*',
			'UserActionPrompt:action.*',
		],
	},
	plugins: [vuePug()],
})
