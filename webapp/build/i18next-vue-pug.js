// ⁂ i18next-cli plugin: turn Vue single-file components (pug or HTML templates) into plain
// ⁂ JavaScript before extraction, so $t() calls in bound attributes (:label="$t('...')") are found.
import { parse, compileTemplate } from '@vue/compiler-sfc'
import pug from 'pug'

export default function vuePug () {
	return {
		name: 'vue-pug',
		onLoad (code, path) {
			if (!path.endsWith('.vue')) return code
			const { descriptor, errors } = parse(code, { filename: path })
			if (errors.length) throw new Error(`${path}: ${errors[0].message}`)
			const parts = [descriptor.script?.content, descriptor.scriptSetup?.content]
			if (descriptor.template) {
				const result = compileTemplate({
					id: path,
					filename: path,
					source: descriptor.template.content,
					preprocessLang: descriptor.template.lang,
					// ⁂ Same as @vitejs/plugin-vue: without it pug renders bare boolean attributes (v-else) as v-else="v-else".
					preprocessOptions: { doctype: 'html' },
					preprocessCustomRequire: lang => ({ pug })[lang],
				})
				if (result.errors.length) throw new Error(`${path}: ${result.errors[0]}`)
				parts.push(result.code)
			}
			return parts.filter(Boolean).join('\n;\n')
		},
	}
}
