import neostandard from 'neostandard'
import pluginVue from 'eslint-plugin-vue'
import pluginVuePug from 'eslint-plugin-vue-pug'
import {
	configureVueProject,
	defineConfigWithVueTs,
	vueTsConfigs
} from '@vue/eslint-config-typescript'

configureVueProject({ scriptLangs: ['ts', 'js'] })

export default defineConfigWithVueTs(
	{ ignores: ['build/', 'dist/'] },
	neostandard({ env: ['browser'], files: ['**/*.vue'], noJsx: true }),
	pluginVue.configs['flat/recommended'],
	pluginVuePug.configs['flat/recommended'],
	vueTsConfigs.recommended,
	{
		languageOptions: {
			ecmaVersion: 'latest',
			globals: {
				localStorage: 'readonly',
				$: 'readonly',
				$$: 'readonly',
				$ref: 'readonly',
				$computed: 'readonly',
			},
		},
		rules: {
			'@stylistic/arrow-parens': 'off',
			'@stylistic/generator-star-spacing': 'off',
			'no-debugger': 'off',
			'@stylistic/indent': ['error', 'tab', { SwitchCase: 1 }],
			'@stylistic/no-tabs': 'off',
			'@stylistic/comma-dangle': 'off',
			camelcase: ['error', { properties: 'never', ignoreDestructuring: true }],
			curly: 'off',
			'@stylistic/quotes': ['error', 'single', { allowTemplateLiterals: 'always' }],
			'no-return-assign': 'off',
			'no-console': 'off',
			'vue/require-default-prop': 'off',
			'vue/require-v-for-key': 'off',
			'vue/valid-v-for': 'warn',
			'vue/no-reserved-keys': 'off',
			'vue/multi-word-component-names': 'off',
			'vue/max-attributes-per-line': 'off',
			'vue/no-v-html': 'off',
			'vue/attribute-hyphenation': ['warn', 'never'],
			'vue/v-on-event-hyphenation': ['warn', 'never'],
			'@typescript-eslint/ban-ts-comment': 'off',
			'@typescript-eslint/no-explicit-any': 'off',
			'no-use-before-define': 'off',
			'@typescript-eslint/no-unused-vars': ['error', { caughtErrors: 'none' }],
			'@typescript-eslint/no-use-before-define': ['error', { typedefs: false, functions: false }],
			'dot-notation': ['error', { allowKeywords: true }],
			'no-var': 'error',
			'n/no-deprecated-api': 'error',
			'prefer-rest-params': 'error',
			'prefer-spread': 'error',
			'@typescript-eslint/no-unused-expressions': ['error', { allowShortCircuit: true, allowTernary: true, allowTaggedTemplates: true }],
		},
	},
	{
		files: ['**/*.vue'],
		rules: {
			'constructor-super': 'error',
			'no-class-assign': 'error',
			'no-const-assign': 'error',
			'no-dupe-args': 'error',
			'no-dupe-class-members': 'error',
			'no-dupe-keys': 'error',
			'no-func-assign': 'error',
			'no-import-assign': 'error',
			'no-new-native-nonconstructor': 'error',
			'no-obj-calls': 'error',
			'no-redeclare': ['error', { builtinGlobals: false }],
			'no-this-before-super': 'error',
			'no-unreachable': 'error',
			'no-unsafe-negation': 'error',
			'no-with': 'error',
		},
	},
)
