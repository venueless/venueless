<template lang="pug">
.c-admin-room(v-scrollbar.y="")
	.header
		h2 Room configuration
	bunt-progress-circular(size="huge", v-if="error == null && config == null")
	.error(v-if="error") We could not fetch the current configuration.
	.main-form(v-if="config != null")
		bunt-input(v-model="config.name", label="Name", name="name")
		bunt-input(v-model="config.description", label="Description", name="description")
		bunt-input(v-model="config.sorting_priority", label="Sorting priority", name="sorting_priority")
		upload-url-input(v-model="config.picture", label="Picture", name="picture")
		table.trait-grants
			thead
				tr
					th Role
					th Required traits
					th
			tbody
				tr(v-for="(val, key, index) in config.trait_grants")
					td
						bunt-input(:value="key", label="Role name", @input="set_role_name(key, $event)", name="n", :disabled="index < Object.keys(config.trait_grants).length - 1")
					td
						bunt-input(label="Required traits (comma-separated)", @input="set_trait_grants(key, $event)", name="g"
												:value="val ? val.join(', ') : ''")
					td.actions
						bunt-icon-button(@click="remove_role(key)") delete
			tfoot
				tr
					td
						bunt-button.btn-add-role(@click="add_role") Add role
					td
					td
		bunt-button.btn-save(@click="save", :loading="saving") Save
</template>
<script>
// TODO
// - search
import api from 'lib/api'
import i18n from '../../i18n'
import UploadUrlInput from '../../components/config/UploadUrlInput'

export default {
	name: 'AdminRoom',
	components: { UploadUrlInput },
	props: {
		editRoomId: String
	},
	data () {
		return {
			config: null,

			saving: false,
			error: null
		}
	},
	computed: {
		locales () {
			return i18n.availableLocales
		}
	},
	methods: {
		set_trait_grants (role, traits) {
			if (typeof this.config.trait_grants[role] !== 'undefined') {
				this.$set(this.config.trait_grants, role, traits.split(',').map((i) => i.trim()))
			}
		},
		remove_role (role) {
			this.$delete(this.config.trait_grants, role)
		},
		add_role () {
			this.$set(this.config.trait_grants, '', [])
		},
		toggle_trait_grants (role, toggle) {
			if (toggle) {
				this.$set(this.config.trait_grants, role, [])
			} else {
				this.$delete(this.config.trait_grants, role)
			}
		},
		set_role_name (old, n) {
			this.$set(this.config.trait_grants, n, this.config.trait_grants[old])
			this.$delete(this.config.trait_grants, old)
		},
		async save () {
			// TODO validate values
			this.saving = true
			await api.call('room.config.patch', {
				room: this.editRoomId,
				name: this.config.name,
				description: this.config.description,
				sorting_priority: this.config.sorting_priority,
				picture: this.config.picture,
				trait_grants: this.config.trait_grants,
			})
			this.saving = false
			// TODO error handling
		},
	},
	async created () {
		// We don't use the global world object since it e.g. currently does not contain locale and timezone
		// TODO: Force reloading if world.updated is received from the server
		try {
			this.config = await api.call('room.config.get', {room: this.editRoomId})
		} catch (error) {
			this.error = error
			console.log(error)
		}
	}
}
</script>
<style lang="stylus">
.c-admin-room
	padding: 16px
	.trait-grants
		width: 100%
		th
			text-align: left
			border-bottom: 1px solid #ccc
			padding: 10px
		td
			vertical-align: center
		td.actions
			text-align: right
	h2
		margin-top: 0
		margin-bottom: 16px
	.btn-save
		margin-top: 16px
		themed-button-primary(size: large)
	.btn-add-role
		margin-top: 16px
		themed-button-default()
</style>
