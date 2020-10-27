import io
import logging
import tempfile
from collections import Counter, defaultdict
from datetime import timedelta
from os.path import dirname
from urllib.parse import urljoin

import dateutil.parser
import pytz
from django.core.exceptions import PermissionDenied
from django.db.models import Max, Min, Q, Sum
from django.db.models.functions import Greatest, TruncMinute
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.timezone import is_naive, now
from django.views import View
from matplotlib import cbook, dates, pyplot
from matplotlib.figure import Figure
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, PageTemplate, Paragraph

from venueless.core.models import Exhibitor, Room, World
from venueless.core.models.room import RoomView
from venueless.core.permissions import Permission
from venueless.graphs.utils import PdfImage

logger = logging.getLogger(__name__)

EMOJIS = {
    "clap": urljoin(dirname(__file__) + "/", "data/clap.png"),
    "+1": urljoin(dirname(__file__) + "/", "data/plus1.png"),
    "heart": urljoin(dirname(__file__) + "/", "data/heart.png"),
    "open_mouth": urljoin(dirname(__file__) + "/", "data/open_mouth.png"),
    "rolling_on_the_floor_laughing": urljoin(
        dirname(__file__) + "/", "data/rolling_on_the_floor_laughing.png"
    ),
}


class GraphView(View):
    size = (12, 6)
    mimes = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
    }

    @cached_property
    def world(self):
        return get_object_or_404(World, domain=self.request.headers["Host"])

    @cached_property
    def fig(self):
        return Figure(
            figsize=self.size
        )  # Do not enable tight_layout, it breaks emoji markers

    def dispatch(self, request, *args, **kwargs):
        try:
            token = self.world.decode_token(request.GET.get("token"))
            if not token:
                raise PermissionDenied("Invalid token.")
        except:
            raise PermissionDenied("Invalid token.")
        if not self.world.has_permission_implicit(
            traits=token.get("traits"), permissions=[Permission.WORLD_GRAPHS]
        ):
            raise PermissionDenied("Permission denied.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.build()

        t = kwargs["type"]
        buf = io.BytesIO()
        self.fig.savefig(buf, format=t)
        buf.seek(0)
        r = HttpResponse(buf.read(), content_type=self.mimes[t])
        r["Content-Disposition"] = "inline"
        return r

    def build(self):
        raise NotImplementedError()


def build_room_view_fig(fig, room, begin, end, tz):
    gs = fig.add_gridspec(1, 1)
    ax = fig.add_subplot(gs[0, 0])
    views = (
        room.views.filter(
            Q(Q(end__isnull=True) | Q(end__gte=begin)) & Q(start__lte=end)
        )
        .order_by()
        .values("user", "start", "end")
    )

    adds = defaultdict(set)
    for v in views:
        bucket = v["start"].replace(
            second=0, microsecond=0, minute=v["start"].minute // 10 * 10
        )
        while bucket < end and (not v["end"] or bucket < v["end"]):
            adds[bucket].add(v["user"])
            bucket += timedelta(minutes=10)

    all_users = frozenset().union(*adds.values())

    pairs = sorted(adds.items())
    keys = [p[0] for p in pairs]
    values = [len(p[1]) for p in pairs]
    ax.plot(keys, values)

    ax.set_xlim(begin, end)
    if values:
        ax.set_ylim(0, max(values) * 1.1)
    else:
        ax.set_ylim(0, 100)
    ax.grid(True)

    reactions = (
        room.reactions.filter(
            datetime__gte=begin,
            datetime__lte=end,
        )
        .annotate(min=TruncMinute("datetime"))
        .order_by()
        .values("datetime", "reaction")
        .annotate(amount=Sum("amount"))
    )

    reacts = Counter()
    for r in reactions:
        bucket = r["datetime"].replace(
            second=0, microsecond=0, minute=r["datetime"].minute // 10 * 10
        )
        reacts[bucket, r["reaction"]] += 1

    ax.set_ylabel("Unique viewers ({} total)".format(len(all_users)))
    ax2 = ax.twinx()
    if reacts:
        ax2.set_ylim(0, max(reacts.values()) * 1.4)
    else:
        ax2.set_ylim(0, 100)
    ax2.set_xlim(begin, end)
    ax2.set_ylabel("Emoji reactions")

    for r, emoji in EMOJIS.items():
        pairs = sorted(reacts.items())
        keys = [p[0][0] for p in pairs if p[0][1] == r]
        values = [p[1] for p in pairs if p[0][1] == r]

        emoji_img = pyplot.imread(cbook.get_sample_data(emoji))
        fig_box = fig.get_window_extent()
        emoji_size = 0.03
        emoji_axs = [None for i in range(len(keys))]
        for i in range(len(keys)):
            loc = ax2.transData.transform((dates.date2num(keys[i]), values[i]))
            emoji_axs[i] = fig.add_axes(
                [
                    loc[0] / fig_box.width - emoji_size / 2,
                    loc[1] / fig_box.height - emoji_size / 2,
                    emoji_size,
                    emoji_size,
                ],
                anchor="C",
            )
            emoji_axs[i].imshow(emoji_img)
            emoji_axs[i].axis("off")
    ax.set_title(room.name)
    fig.autofmt_xdate()
    ax.xaxis.set_major_formatter(dates.DateFormatter("%d. %H:%M", tz=tz))


class RoomAttendanceGraphView(GraphView):
    @cached_property
    def room(self):
        return get_object_or_404(self.world.rooms, pk=self.request.GET.get("room"))

    def build(self):
        tz = pytz.timezone(self.world.timezone)

        begin = self.room.views.aggregate(min=Min("start"))["min"]
        end = self.room.views.aggregate(max=Max("end"))["max"]

        if "begin" in self.request.GET:
            try:
                begin = dateutil.parser.parse(self.request.GET.get("begin"))
            except ValueError:
                pass

        if "end" in self.request.GET:
            try:
                end = dateutil.parser.parse(self.request.GET.get("end"))
            except ValueError:
                pass

        if is_naive(begin):
            begin = tz.localize(begin)
        if is_naive(end):
            end = tz.localize(end)
        end = max(end, begin + timedelta(minutes=1))
        build_room_view_fig(self.fig, self.room, begin, end, tz)


class ReportView(GraphView):
    mimes = {
        "pdf": "application/pdf",
    }

    def get(self, request, *args, **kwargs):
        t = kwargs["type"]
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            doc = self.get_doc_template()(
                f.name,
                pagesize=self.pagesize,
                leftMargin=15 * mm,
                rightMargin=15 * mm,
                topMargin=20 * mm,
                bottomMargin=15 * mm,
            )
            doc.addPageTemplates(
                [
                    PageTemplate(
                        id="All",
                        frames=self.get_frames(doc),
                        onPage=self.on_page,
                        pagesize=self.pagesize,
                    )
                ]
            )
            doc.build(self.get_story())
            f.seek(0)
            r = HttpResponse(f.read(), content_type=self.mimes[t])
            r["Content-Disposition"] = "inline"
            return r

    @property
    def pagesize(self):
        from reportlab.lib import pagesizes

        return pagesizes.portrait(pagesizes.A4)

    def get_doc_template(self):
        from reportlab.platypus import BaseDocTemplate

        return BaseDocTemplate

    def get_frames(self, doc):
        from reportlab.platypus import Frame

        self.frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="normal",
        )
        return [self.frame]

    @cached_property
    def stylesheet(self):
        from reportlab.lib.styles import getSampleStyleSheet

        style = getSampleStyleSheet()
        return style

    def on_page(self, canvas, doc):
        canvas.saveState()
        self.page_footer(canvas, doc)
        self.page_header(canvas, doc)
        canvas.restoreState()

    def page_footer(self, canvas, doc):
        from reportlab.lib.units import mm

        canvas.setFont("Helvetica", 8)
        # canvas.drawString(15 * mm, 10 * mm, _("Page %d") % (doc.page,))
        canvas.drawRightString(
            self.pagesize[0] - 15 * mm,
            10 * mm,
            now().astimezone(self.tz).strftime("%d.%m.%Y %H:%M:%S"),
        )

    def get_right_header_string(self):
        return "venueless"

    def get_left_header_string(self):
        return self.world.title

    def page_header(self, canvas, doc):
        from reportlab.lib.units import mm

        canvas.setFont("Helvetica", 10)
        canvas.drawString(
            15 * mm, self.pagesize[1] - 15 * mm, self.get_left_header_string()
        )
        canvas.drawRightString(
            self.pagesize[0] - 15 * mm,
            self.pagesize[1] - 15 * mm,
            self.get_right_header_string(),
        )
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.line(
            15 * mm,
            self.pagesize[1] - 17 * mm,
            self.pagesize[0] - 15 * mm,
            self.pagesize[1] - 17 * mm,
        )

    @cached_property
    def tz(self):
        return pytz.timezone(self.world.timezone)

    @cached_property
    def date_begin(self):
        begin = RoomView.objects.filter(room__world=self.world).aggregate(
            min=Min("start")
        )["min"]

        if "begin" in self.request.GET:
            try:
                begin = dateutil.parser.parse(self.request.GET.get("begin"))
            except ValueError:
                pass
        return begin.astimezone(self.tz)

    @cached_property
    def date_end(self):
        end = RoomView.objects.filter(room__world=self.world).aggregate(
            max=Greatest(Max("start"), Max("end"))
        )["max"]

        if "end" in self.request.GET:
            try:
                end = dateutil.parser.parse(self.request.GET.get("end"))
            except ValueError:
                pass
        return end.astimezone(self.tz)

    def get_story(self):
        s = [
            Paragraph(self.world.title, self.stylesheet["Heading1"]),
            # todo: sums of rooms
            # todo: number of chat messages
            # todo: number of 1:1 combinations
            # todo: number of exhibitors
            # todo: number of users
        ]

        for room in self.world.rooms.all():
            types = [m["type"] for m in room.module_config]
            if any(
                t.startswith("livestream.")
                or t.startswith("chat.")
                or t.startswith("call.")
                for t in types
            ):
                s += self.story_for_room(room)

        for exhibitor in self.world.exhibitors.all():
            s += self.story_for_exhibitor(exhibitor)
        return s

    def story_for_room(self, room: Room):
        s = [
            PageBreak(),
            Paragraph(room.name, self.stylesheet["Heading2"]),
            # todo: total unique users
            # todo: average time spent per user
        ]
        day = self.date_begin
        while day.date() <= self.date_end.date():

            fig = Figure(figsize=(7, 4))
            gds = day.replace(hour=self.date_begin.hour, minute=0, second=0)
            gde = day.replace(
                hour=self.date_end.hour, minute=self.date_end.minute, second=0
            )
            build_room_view_fig(fig, room, gds, gde, self.tz)
            imgdata = io.BytesIO()
            fig.savefig(imgdata, format="PDF")
            s.append(
                KeepTogether(
                    [
                        Paragraph(
                            date_format(day, "SHORT_DATE_FORMAT"),
                            self.stylesheet["Heading3"],
                        ),
                        PdfImage(imgdata),
                    ]
                )
            )

            day += timedelta(days=1)
        return s

    def story_for_exhibitor(self, exhibitor: Exhibitor):
        s = [
            PageBreak(),
            Paragraph(exhibitor.name, self.stylesheet["Heading2"]),
            # todo: views
            # todo: unique users
            # todo: contact requests
        ]
        return s
