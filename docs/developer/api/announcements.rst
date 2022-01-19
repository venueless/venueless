Announcements module
====================

The announcements module allows organisers to push announcements to all users.
Announcements can either have an expiry timestamp (``show_until``), or can
be deactivated manually by the administrators.

Receiving announcements
-----------------------

Announcements are always sent out with a ``created_or_updated`` message::

    <= ["announcement.created_or_updated", {"id": "", "text": "", "show_until": "", "is_active": true}]

Additionally, all currently visible announcements are listed in the initial
response after authenticating, as the ``"announcements"`` field.

List announcements
------------------

To receive a list of all available announcements::

    => ["announcement.list", 1234, {}]
    <- ["success", 1234, []]

Creating or updating an announcement
------------------------------------

To create an announcement, a user with the permission ``WORLD_ANNOUNCE`` sends
a message like this::

    => ["announcement.create", 1234, {"text": "Announcement text", "show_until": "timestamp or null", "is_active": true}]
    <- ["success", 1234, {"announcement": []}]

Setting ``is_active`` to ``false`` will keep the announcement hidden until it
is published, otherwise it will be pushed to all users immediately.

To update an announcement, include its ``id`` and send an
``announcement.update`` message.
