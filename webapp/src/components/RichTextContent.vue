<template lang="pug">
.rich-text-content(v-html="renderedContent", @click="handleClick")
</template>
<script>
import Quill from 'quill'
import router from 'router'

export default {
	props: {
		content: Array,
	},
	computed: {
		renderedContent () {
			const tempCont = document.createElement('div');
			(new Quill(tempCont)).setContents(this.content)
			return tempCont.getElementsByClassName('ql-editor')[0].innerHTML
		},
	},
	methods: {
		handleClick (event) {
			const a = event.target.closest('a')
			if (!a) return
			// from https://github.com/vuejs/vue-router/blob/dfc289202703319cf7beb38d03c9258c806c4d62/src/components/link.js#L165
			// don't redirect with control keys
			if (event.metaKey || event.altKey || event.ctrlKey || event.shiftKey) return
			// don't redirect on right click
			if (event.button !== undefined && event.button !== 0) return
			// don't handle same page links/anchors or external links
			const url = new URL(a.href)
			if (window.location.pathname === url.pathname) return
			if (window.location.hostname !== url.hostname) return
			event.preventDefault()
			router.push(url.pathname + url.hash)
		}
	},
}
</script>
