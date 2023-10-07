import Quill from 'quill'

const Embed = Quill.import('blots/embed')

class MentionBlot extends Embed {
	constructor (scroll, node) {
		super(scroll, node)
		this.clickHandler = null
		this.hoverHandler = null
		this.mounted = false
	}

	static create (data) {
		const node = super.create()
		node.innerText = '@' + data.name

		return MentionBlot.setDataValues(node, data)
	}

	static setDataValues (element, data) {
		const domNode = element
		Object.keys(data).forEach((key) => {
			domNode.dataset[key] = data[key]
		})
		return domNode
	}

	static value (domNode) {
		return domNode.dataset
	}

	attach () {
		super.attach()

		if (!this.mounted) {
			this.mounted = true
			this.clickHandler = this.getClickHandler()
			this.hoverHandler = this.getHoverHandler()

			this.domNode.addEventListener('click', this.clickHandler, false)
			this.domNode.addEventListener('mouseenter', this.hoverHandler, false)
		}
	}

	detach () {
		super.detach()
		this.mounted = false
		if (this.clickHandler) {
			this.domNode.removeEventListener('click', this.clickHandler)
			this.clickHandler = null
		}
	}

	getClickHandler () {
		return (e) => {
			const event = this.buildEvent('mention-clicked', e)
			window.dispatchEvent(event)
			e.preventDefault()
		}
	}

	getHoverHandler () {
		return (e) => {
			const event = this.buildEvent('mention-hovered', e)
			window.dispatchEvent(event)
			e.preventDefault()
		}
	}

	buildEvent (name, e) {
		const event = new Event(name, {
			bubbles: true,
			cancelable: true,
		})
		event.value = Object.assign({}, this.domNode.dataset)
		event.event = e
		return event
	}
}

MentionBlot.blotName = 'mention'
MentionBlot.tagName = 'span'
MentionBlot.className = 'mention'

Quill.register('blots/mention', MentionBlot)
