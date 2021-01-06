<template lang="pug">
.rich-text-content(v-html="renderedContent")
</template>
<script>
import Quill from 'quill'

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
}
</script>
