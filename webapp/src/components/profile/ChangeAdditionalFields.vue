<!-- eslint-disable vue/no-mutating-props -->
<template lang="pug">
.c-additional-fields
	template(v-for="field of fields")
		bunt-input(v-if="field.type === 'text'", v-model="modelValue[field.id]", :name="field.label", :label="field.label", :disabled="disabled")
		bunt-input-outline-container(v-if="field.type === 'textarea'", :label="field.label", :name="field.label", :class="{disabled: disabled}")
			template(#default="{focus, blur}")
				textarea(v-model="modelValue[field.id]", :disabled="disabled", @focus="focus", @blur="blur")
		bunt-select(v-if="field.type === 'select'", v-model="modelValue[field.id]", :label="field.label", name="field.label", :options="field.choices.split(', ')", :disabled="disabled")
		bunt-input(v-if="field.type === 'link'", v-model="modelValue[field.id]", :name="field.label", :label="field.label", :disabled="disabled")
</template>
<script>
import { mapState } from 'vuex'

export default {
	props: {
		modelValue: Object,
		disabled: {
			type: Boolean,
			default: false
		}
	},
	computed: {
		...mapState(['world']),
		fields () {
			return this.world?.profile_fields
		}
	}
}
</script>
<style lang="stylus">
.c-additional-fields
	display: flex
	flex-direction: column
	.bunt-input-outline-container
		margin-bottom 16px
		textarea
			font-family $font-stack
			font-size 16px
			background-color transparent
			border none
			outline none
			resize vertical
			min-height 250px
			padding 0 8px
	.bunt-input-outline-container.disabled
		background-color $clr-grey-200
</style>
