<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted } from 'vue'

const {
	x,
	y
} = defineProps({
	x: Boolean,
	y: Boolean
})

const emit = defineEmits(['resize', 'scroll'])

const dimensions = $ref<{x?, y?}>({})
let draggingDimension = $ref(null)
let draggingOffset = $ref(null)

const thumbStyles = $computed(() => {
	const thumbStyles : {x?, y?} = {}
	if (dimensions?.x) {
		thumbStyles.x = {
			width: dimensions.x.thumbLength + 'px',
			left: dimensions.x.thumbPosition + 'px'
		}
		if (dimensions.x.visibleRatio >= 1) {
			thumbStyles.x.display = 'none'
		}
	}
	if (dimensions?.y) {
		const direction = dimensions.y.direction === 'reverse' ? 'bottom' : 'top'
		thumbStyles.y = {
			height: dimensions.y.thumbLength + 'px',
			[direction]: dimensions.y.thumbPosition + 'px'
		}
		if (dimensions.y.visibleRatio >= 1) {
			thumbStyles.y.display = 'none'
		}
	}
	return thumbStyles
})

const thumbRefs = $ref({})
const contentRef = $ref(null)

// TODO expose
const scrollTop = (y) => {
	contentRef.scrollTop = y
}

if (x) {
	dimensions.x = {
		visibleRatio: null,
		thumbLength: null,
		thumbPosition: null
	}
}
if (y) {
	dimensions.y = {
		visibleRatio: null,
		thumbLength: null,
		thumbPosition: null,
		direction: null
	}
}

function computeDimensions () {
	if (dimensions.x) {
		dimensions.x.visibleRatio = contentRef.clientWidth / contentRef.scrollWidth
		dimensions.x.thumbLength = contentRef.clientWidth * dimensions.x.visibleRatio
	}
	if (dimensions.y) {
		dimensions.y.visibleRatio = contentRef.clientHeight / contentRef.scrollHeight
		dimensions.y.thumbLength = contentRef.clientHeight * dimensions.y.visibleRatio
	}
}

function computeThumbPositions () {
	if (dimensions.x) {
		dimensions.x.thumbPosition = contentRef.scrollLeft / (contentRef.scrollWidth - contentRef.clientWidth) * (contentRef.clientWidth - dimensions.x.thumbLength)
	}
	if (dimensions.y) {
		if (dimensions.y.direction === 'reverse') {
			dimensions.y.thumbPosition = -1 * contentRef.scrollTop / (contentRef.scrollHeight - contentRef.clientHeight) * (contentRef.clientHeight - dimensions.y.thumbLength)
		} else {
			dimensions.y.thumbPosition = contentRef.scrollTop / (contentRef.scrollHeight - contentRef.clientHeight) * (contentRef.clientHeight - dimensions.y.thumbLength)
		}
	}
}

function handleResize () {
	computeDimensions()
	computeThumbPositions()
	emit('resize')
}

const resizeObserver = new ResizeObserver(handleResize)
const mutationObserver = new MutationObserver((records) => {
	for (const record of records) {
		for (const addedNode of record.addedNodes) {
			if (addedNode.nodeType !== Node.ELEMENT_NODE) continue
			resizeObserver.observe(addedNode as Element)
		}
		for (const removedNode of record.removedNodes) {
			if (removedNode.nodeType !== Node.ELEMENT_NODE) continue
			resizeObserver.unobserve(removedNode as Element)
		}
	}
	handleResize()
})

onMounted(async () => {
	await nextTick()
	// setting direction once should be good enough
	if (dimensions.y) {
		const contentStyle = getComputedStyle(contentRef)
		if (contentStyle.flexDirection.endsWith('reverse')) {
			dimensions.y.direction = 'reverse'
		}
	}
	computeDimensions()
	computeThumbPositions()

	resizeObserver.observe(contentRef)
	for (const el of contentRef.children) {
		resizeObserver.observe(el)
	}
	mutationObserver.observe(contentRef, {
		childList: true
	})
})

onBeforeUnmount(() => {
	resizeObserver.disconnect()
	mutationObserver.disconnect()
})

function handleScroll (event) {
	emit('scroll', event)
	computeThumbPositions()
}

function handlePointerdown (dimension, event) {
	const el = thumbRefs[dimension]
	event.stopPropagation()
	el.setPointerCapture(event.pointerId)
	draggingDimension = dimension
	draggingOffset = event[`offset${dimension.toUpperCase()}`]
	// TODO cancel
	el.addEventListener('pointermove', handlePointermove)
	el.addEventListener('pointerup', handlePointerup)
}

function handlePointermove (event) {
	if (draggingDimension === 'x') {
		const maxX = contentRef.clientWidth - dimensions.x.thumbLength
		const newPosition = event.clientX - contentRef.getBoundingClientRect().left - draggingOffset
		dimensions.x.thumbPosition = Math.min(Math.max(0, newPosition), maxX)
		contentRef.scrollLeft = dimensions.x.thumbPosition / maxX * (contentRef.scrollWidth - contentRef.clientWidth)
	}

	if (draggingDimension === 'y') {
		const maxY = contentRef.clientHeight - dimensions.y.thumbLength
		if (dimensions.y.direction === 'reverse') {
			const newPosition = contentRef.clientHeight - (event.clientY - contentRef.getBoundingClientRect().top + (dimensions.y.thumbLength - draggingOffset))
			dimensions.y.thumbPosition = Math.min(Math.max(0, newPosition), maxY)
			contentRef.scrollTop = -1 * dimensions.y.thumbPosition / maxY * (contentRef.scrollHeight - contentRef.clientHeight)
		} else {
			const newPosition = event.clientY - contentRef.getBoundingClientRect().top - draggingOffset
			dimensions.y.thumbPosition = Math.min(Math.max(0, newPosition), maxY)
			contentRef.scrollTop = dimensions.y.thumbPosition / maxY * (contentRef.scrollHeight - contentRef.clientHeight)
		}
	}
}

function handlePointerup (event) {
	const dimension = draggingDimension
	const el = thumbRefs[dimension]
	draggingDimension = null
	el.releasePointerCapture(event.pointerId)
	el.removeEventListener('pointermove', handlePointermove)
	el.removeEventListener('pointerup', handlePointerup)
}

defineExpose({
	scrollTop,
	contentRef: $$(contentRef)
})

</script>
<template lang="pug">
.c-scrollbars
	.scroll-content(ref="contentRef", @scroll="handleScroll")
		slot
	template(v-for="dim of Object.keys(dimensions)", :key="dim")
		div(:class="[`scrollbar-rail-${dim}`, {active: draggingDimension === dim}]", @pointerdown="handlePointerdown(dim, $event)")
			.scrollbar-thumb(:ref="el => { thumbRefs[dim] = el }", :style="thumbStyles[dim]")
</template>
<style lang="sass">
$rail-width: 15px
$thumb-width: 6px
$thumb-width-hovered: 12px

.c-scrollbars
	display: flex
	flex-direction: column
	position: relative
	box-sizing: border-box
	min-height: 0
	flex: auto
	.scroll-content
		display: flex
		flex-direction: column
		overflow: scroll
		min-height: 0
		&::-webkit-scrollbar
			display: none
		-ms-overflow-style: none
		scrollbar-width: none

	&:hover
		.scrollbar-thumb
			opacity: .4

	.scrollbar-rail-x,
	.scrollbar-rail-y
		position: absolute
		user-select: none
		overflow: hidden
		z-index: 99

	.scrollbar-thumb
		position: absolute
		background-color: var(--clr-blue-grey-600)
		opacity: .2
		border-radius: $thumb-width
		transition: height .3s var(--material-easing), width .3s var(--material-easing), opacity .3s var(--material-easing)

	.scrollbar-rail-x
		height: $rail-width
		width: 100%
		bottom: 0
		.scrollbar-thumb
			bottom: 2px
			height: $thumb-width

		&:hover, &.active
			.scrollbar-thumb
				height: $thumb-width-hovered
				opacity: .8
	.scrollbar-rail-y
		width: $rail-width
		height: 100%
		right: 0
		top: 0

		.scrollbar-thumb
			right: 2px
			width: $thumb-width
		&:hover, &.active
			.scrollbar-thumb
				width: $thumb-width-hovered
				opacity: .8
</style>
