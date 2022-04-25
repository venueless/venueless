from channels_redis.pubsub import RedisPubSubChannelLayer


class ChannelLayer(RedisPubSubChannelLayer):
    async def group_discard(self, group, channel):
        # Silently fail if group currently not subscribed
        group_channel = self._get_group_channel_name(group)
        if group_channel not in self.groups:
            return
        group_channels = self.groups[group_channel]
        assert channel in group_channels
        group_channels.remove(channel)
        if len(group_channels) == 0:
            del self.groups[group_channel]
            shard = self._get_shard(group_channel)
            await shard.unsubscribe(group_channel)