<script setup>
import { SlickList, SlickItem, DragHandle, ElementMixin, HandleDirective } from 'vue-slicksort'
import api from 'lib/api'

let config = $ref()
let error = $ref()

;(async () => {
	try {
		config = await api.call('world.config.get')
	} catch (e) {
		error = e
		console.error(error)
	}
})()

let saving = $ref(false)
let savingError = $ref(null)
async function save () {
	if (!config) return
	saving = true
	try {
		await api.call('world.config.patch', { external_links: config.external_links })
		// Optionally show a success message or handle post-save logic
	} catch (err) {
		savingError = err
		console.error(savingError)
	} finally {
		saving = false
	}
}

function addLink () {
	if (!config || !config.external_links) return
	config.external_links.push({ name: '', url: '' })
}

function removeLink (index) {
	if (!config || !config.external_links) return
	config.external_links.splice(index, 1)
}

</script>
<template lang="pug">
.c-admin-config-links
	.ui-page-header
		h1 External Links
	bunt-progress-circular(v-if="!error && !config", size="huge")
	.error(v-if="error") We could not fetch the current configuration.
	template(v-if="config")
		.ui-form-body
			h3 External Links
			p Configure external links that will be shown at the bottom of the sidebar.
		.links
			.header
				.name Name
				.url URL
				.actions
			SlickList.tbody(v-model:list="config.external_links", v-scrollbar.y="", lockAxis="y", :useDragHandle="true", appendTo=".tbody", @update:list="config.external_links = $event")
				SlickItem.link(v-for="(link, index) of config.external_links", :key="index", :index="index")
					DragHandle.mdi.mdi-drag-vertical
					bunt-input.name(v-model="link.name", name="name", placeholder="Link name")
					bunt-input.url(v-model="link.url", name="url", placeholder="https://example.com/some-page")
					.actions
						bunt-icon-button(@click="removeLink(index)") delete-outline
			bunt-button#btn-add-link(@click="addLink") Add link
	.ui-form-actions
		bunt-button.btn-save(:loading="saving", :errorMessage="savingError", @click="save") Save
	//- .errors {{ validationErrors.join(', ') }}
</template>
<style lang="stylus">
.c-admin-config-links
	flex: auto
	display: flex
	flex-direction: column
	.ui-form-body
		flex: none
	.links
		flex: auto
		display: flex
		flex-direction: column
		.header, .link
			display: flex
			align-items: center
			flex: none
			height: 56px
			border-bottom: border-separator()
			.bunt-input
				input-style(size: compact)
				padding-top: 0
				margin-right: 8px
			.name, .url
					flex: 1
			.actions
				width: 56px
			& > *
				box-sizing: border-box
				padding-left: 16px
			> :first-child
				padding-left: 16px
			> :last-child
				padding-right: 8px
		.header
			display: flex
			font-weight: bold
			margin-bottom: 0.5rem
			border-bottom-width: 3px
			& > *
				font-weight: 600
		.link
			display: flex
			align-items: center
			margin-bottom: 0.5rem
	#btn-add-link
		themed-button-secondary()
		align-self: flex-start
		margin: 8px
</style>
