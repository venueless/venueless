<template lang="pug">
.c-roulette
	bunt-progress-circular(size="huge", :page="true", v-if="loading")
</template>
<script>
import { Janus } from 'janus-gateway'
import { mapState } from 'vuex'

export default {
	props: {
		module: {
			type: Object,
			required: true
		}
	},
	data () {
		return {
			url: null,
			server: null,
			roomId: null,
			loading: null,
			janus: null,
			pluginHandle: null,
			ourId: null,
			ourPrivateId: null,
			feeds: [],
		}
	},
	computed: {
		...mapState(['user']),
	},
	async created () {
		// todo fetch from server
		this.server = 'https://dev-janus.venueless.events/janus'
		this.roomId = 1234
		this.initJanus()
	},
	destroyed () {
		this.janus.destroy()
	},
	methods: {
		attachToRoom () {
			this.janus.attach(
				{
					plugin: 'janus.plugin.videoroom',
					opaqueId: this.user.id,
					success: function (pluginHandle) {
						this.pluginHandle = pluginHandle
						Janus.log('Plugin attached! (' + this.pluginHandle.getPlugin() + ', id=' + this.pluginHandle.getId() + ')')
						Janus.log('  -- This is a publisher/manager')
						this.loading = false
					},
					error: function (error) {
						Janus.error('  -- Error attaching plugin...', error)
						alert('Error attaching plugin... ' + error)
					},
					consentDialog: function (on) {
						Janus.debug('Consent dialog should be ' + (on ? 'on' : 'off') + ' now')
						// TODO
					},
					iceState: function (state) {
						Janus.log('ICE state changed to ' + state)
					},
					mediaState: function (medium, on) {
						Janus.log('Janus ' + (on ? 'started' : 'stopped') + ' receiving our ' + medium)
					},
					webrtcState: function (on) {
						Janus.log('Janus says our WebRTC PeerConnection is ' + (on ? 'up' : 'down') + ' now')
						if (!on)
							return
					},
					onmessage: function (msg, jsep) {
						Janus.debug(' ::: Got a message (publisher) :::', msg)
						var event = msg.videoroom
						Janus.debug('Event: ' + event)
						if (event) {
							if (event === 'joined') {
								// Publisher/manager created, negotiate WebRTC and attach to existing feeds, if any
								this.ourId = msg.id
								this.ourPrivateId = msg.private_id
								Janus.log('Successfully joined room ' + msg.room + ' with ID ' + this.ourId)
								this.publishOwnFeed(true)
								// Any new feed to attach to?
								if (msg.publishers) {
									var list = msg.publishers
									Janus.debug('Got a list of available publishers/feeds:', list)
									for (const f of list) {
										const id = f.id
										const display = f.display
										const audio = f.audio_codec
										const video = f.video_codec
										Janus.debug('  >> [' + id + '] ' + display + ' (audio: ' + audio + ', video: ' + video + ')')
										this.newRemoteFeed(id, display, audio, video)
									}
								}
							} else if (event === 'destroyed') {
								// The room has been destroyed
								Janus.warn('The room has been destroyed!')
								alert('The room has been destroyed')  // todo
							} else if (event === 'event') {
								// Any new feed to attach to?
								if (msg.publishers) {
									const list = msg.publishers
									Janus.debug('Got a list of available publishers/feeds:', list)
									for (const f of list) {
										const id = f.id
										const display = f.display
										const audio = f.audio_codec
										const video = f.video_codec
										Janus.debug('  >> [' + id + '] ' + display + ' (audio: ' + audio + ', video: ' + video + ')')
										this.newRemoteFeed(id, display, audio, video)
									}
								} else if (msg.leaving) {
									// One of the publishers has gone away?
									const leaving = msg.leaving
									Janus.log('Publisher left: ' + leaving)
									let remoteFeed = null
									let remoteFeedIndex = null
									for (const fi in this.feeds) {
										if (this.feeds[fi] && this.feeds[fi].rfid === leaving) {
											remoteFeed = this.feeds[fi]
											remoteFeedIndex = fi
											break
										}
									}
									if (remoteFeed != null) {
										Janus.debug('Feed ' + remoteFeed.rfid + ' (' + remoteFeed.rfdisplay + ') has left the room, detaching')
										this.feeds.splice(remoteFeedIndex, 1)
										remoteFeed.detach()
									}
								} else if (msg.unpublished) {
									// One of the publishers has unpublished?
									const unpublished = msg.unpublished
									Janus.log('Publisher left: ' + unpublished)
									if (unpublished === 'ok') {
										// That's us
										this.pluginHandle.hangup()
										return
									}
									let remoteFeed = null
									let remoteFeedIndex = null
									for (const fi in this.feeds) {
										if (this.feeds[fi] && this.feeds[fi].rfid === unpublished) {
											remoteFeed = this.feeds[fi]
											remoteFeedIndex = fi
											break
										}
									}
									if (remoteFeed != null) {
										Janus.debug('Feed ' + remoteFeed.rfid + ' (' + remoteFeed.rfdisplay + ') has left the room, detaching')
										this.feeds.splice(remoteFeedIndex, 1)
										remoteFeed.detach()
									}
								} else if (msg.error) {
									if (msg.error_code === 426) {
										// This is a "no such room" error: give a more meaningful description
										// todo
										alert(
											'<p>Apparently room <code>' + myroom + '</code> (the one this demo uses as a test room) ' +
														'does not exist...</p><p>Do you have an updated <code>janus.plugin.videoroom.jcfg</code> ' +
														'configuration file? If not, make sure you copy the details of room <code>' + myroom + '</code> ' +
														'from that sample in your current configuration file, then restart Janus and try again.'
										)
									} else {
										alert(msg.error) // todo
									}
								}
							}
						}
						if (jsep) {
							Janus.debug('Handling SDP as well...', jsep)
							this.pluginHandle.handleRemoteJsep({ jsep: jsep })
							// Check if any of the media we wanted to publish has
							// been rejected (e.g., wrong or unsupported codec)
							var audio = msg.audio_codec
							if (this.ourStream && this.ourStream.getAudioTracks() && this.ourStream.getAudioTracks().length > 0 && !audio) {
								// Audio has been rejected
								console.warning("Our audio stream has been rejected, viewers won't hear us")
							}
							var video = msg.video_codec
							if (this.ourStream && this.ourStream.getVideoTracks() && this.ourStream.getVideoTracks().length > 0 && !video) {
								// Video has been rejected
								console.warning("Our video stream has been rejected, viewers won't see us")
								// todo: Hide the webcam video
							}
						}
					},
					onlocalstream: function (stream) {
						Janus.debug(' ::: Got a local stream :::', stream)
						this.ourStream = stream
						// todo: show local stream
						// Janus.attachMediaStream($('#myvideo').get(0), stream)
						// $('#myvideo').get(0).muted = 'muted'
						if (this.pluginHandle.webrtcStuff.pc.iceConnectionState !== 'completed' &&
											this.pluginHandle.webrtcStuff.pc.iceConnectionState !== 'connected') {
							// todo show that we are still publishing…
						}
						const videoTracks = stream.getVideoTracks()
						if (!videoTracks || videoTracks.length === 0) {
							// No webcam
							// todo: no webcam found
						} else {
							// show video
						}
					},
					onremotestream: function (stream) {
						// The publisher stream is sendonly, we don't expect anything here
					},
					oncleanup: function () {
						Janus.log(' ::: Got a cleanup notification: we are unpublished now :::')
						this.ourStream = null
					}
				})
		},
		connectToServer () {
			this.janus = new Janus({
				server: this.server,
				success: this.attachToRoom,
				error (error) {
					Janus.error(error)
					alert(error)
					// todo: handle
				},
				destroyed () {
					alert('destroyed')
					// todo: handle
				}
			})
		},
		initJanus () {
			Janus.init({
				debug: 'all', // todo: conditional
				callback: this.connectToServer,
			})
			this.loading = false
		}
	},
}
</script>
<style lang="stylus">
.c-roulette
	flex: auto
	height: auto  // 100% breaks safari
	display: flex
	flex-direction: column
	position: relative
	iframe
		height: 100%
		width: 100%
		position: absolute
		top: 0
		left: 0
		border: none
		flex: auto // because safari
</style>
