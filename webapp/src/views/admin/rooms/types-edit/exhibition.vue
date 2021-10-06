<template lang="pug">
.c-exhibition-settings
	bunt-select(v-model="modules['exhibition.native'].config.layout", label="Layout", name="layout", :options="layoutOptions")
</template>
<script>
import mixin from './mixin'

export default {
	mixins: [mixin],
	data () {
		return {
			layoutOptions: [{
				id: null,
				label: 'Exhibition'
			}, {
				id: 'poster',
				label: 'Posters?'
			}]
		}
	}
}
</script>
<style lang="stylus">
</style>
