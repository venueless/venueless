<!-- eslint-disable vue/no-mutating-props -->
<template lang="pug">
.c-trait-grants
	.header
		.role Role
		.traits Required traits (comma separated)
		.actions
	.trait-grant(v-for="(val, key) of traitGrants")
		.role {{ key }}
		bunt-input.traits(name="trait-grant", :modelValue="getTraitGrants(val)", placeholder="(everyone)", @update:modelValue="setTraitGrants(key, $event)")
		.actions
			bunt-icon-button(@click="removeTraitGrant(key)") delete-outline
	.add-role
		bunt-select(v-model="newRole", name="remainingRoles", label="New role", :options="remainingRoles")
		bunt-button.btn-add-role(@click="addTraitGrant") Add role
</template>
<script>
import { parseTraitGrants, stringifyTraitGrants } from 'lib/traitGrants'

export default {
	props: {
		traitGrants: Object,
		config: Object
	},
	emits: ['changed'],
	data () {
		return {
			newRole: null
		}
	},
	computed: {
		remainingRoles () {
			const existingRoles = Object.keys(this.traitGrants)
			return Object.keys(this.config.roles).filter(role => !existingRoles.includes(role))
		}
	},
	created () {},
	mounted () {
		this.$nextTick(() => {
		})
	},
	methods: {
		getTraitGrants (traits) {
			return stringifyTraitGrants(traits)
		},
		setTraitGrants (role, traits) {
			if (typeof this.traitGrants[role] !== 'undefined') {
				// eslint-disable-next-line vue/no-mutating-props
				this.traitGrants[role] = parseTraitGrants(traits)
			}
			this.$emit('changed')
		},
		removeTraitGrant (role) {
			// eslint-disable-next-line vue/no-mutating-props
			delete this.traitGrants[role]
			this.$emit('changed')
		},
		addTraitGrant () {
			// eslint-disable-next-line vue/no-mutating-props
			this.traitGrants[this.newRole] = []
			this.newRole = null
			this.$emit('changed')
		}
	}
}
</script>
<style lang="stylus">
.c-trait-grants
	display: flex
	flex-direction: column
	.header, .trait-grant
		display: flex
		height: 56px
		flex: none
		align-items: center
		border-bottom: border-separator()
		.bunt-input
			padding-top: 0
		.role, .traits
			flex: 1
		.actions
			width: 56px
		& > *
			box-sizing: border-box
			padding-left: 8px
		> :first-child
			padding-left: 16px
		> :last-child
			padding-right: 8px
	.header
		border-bottom-width: 3px
		& > *
			font-weight: 600
			padding-left: 16px
	.trait-grant
		&:hover
			background-color: $clr-grey-100
	.add-role
		display: flex
		padding: 8px
		align-items: center
		.bunt-input
			padding-top: 0
			height: 36px
			margin-right: 8px
</style>
