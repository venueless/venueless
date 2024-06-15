module.exports = {
	root: true,
	parser: 'vue-eslint-parser',
	parserOptions: {
		parser: '@typescript-eslint/parser',
		ecmaVersion: 'latest',
		sourceType: 'module'
	},
	extends: [
		'standard',
		'plugin:vue/vue3-recommended',
		'plugin:vue-pug/vue3-recommended',
		'@vue/eslint-config-typescript/recommended'
	],
	// add your custom rules here
	rules: {
		'arrow-parens': 0,
		'generator-star-spacing': 0,
		'no-debugger': 'off',
		indent: [2, 'tab', { SwitchCase: 1 }],
		'no-tabs': 0,
		'comma-dangle': 0,
		curly: 0,
		quotes: ['error', 'single', { allowTemplateLiterals: true }], // not really ideal, but "avoidEscape" only allows double quotes
		'no-return-assign': 0,
		'no-console': 'off',
		'vue/require-default-prop': 0,
		'vue/require-v-for-key': 0,
		'vue/valid-v-for': 'warn',
		'vue/no-reserved-keys': 0,
		'vue/no-setup-props-destructure': 0,
		'vue/multi-word-component-names': 0,
		'vue/max-attributes-per-line': 0,
		'vue/attribute-hyphenation': ['warn', 'never'],
		'vue/v-on-event-hyphenation': ['warn', 'never'],
		'import/first': 0, // does not work with multiple script tags
		// 'no-unused-vars': 0 // does not with setup + pug
		'@typescript-eslint/ban-ts-comment': 0,
		'@typescript-eslint/no-explicit-any': 0,
		'no-use-before-define': 'off',
		'@typescript-eslint/no-use-before-define': ['error', { typedefs: false, functions: false }]
	},
	globals: {
		localStorage: false,
		$: 'readonly',
		$$: 'readonly',
		$ref: 'readonly',
		$computed: 'readonly',
	},
	env: {
		browser: true,
		node: true,
		'vue/setup-compiler-macros': true
	}
}
