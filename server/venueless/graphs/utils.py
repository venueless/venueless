import logging
from datetime import timedelta
from io import BytesIO

import requests
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.platypus import Flowable
from svglib.svglib import svg2rlg

from venueless.core.models import World

logger = logging.getLogger(__name__)


class SvgImage(Flowable):
    # Inspired by https://github.com/rgacote/reportlab-flowable-for-rml/tree/main
    # (c) Raymond GA Côté, BSD 3-clause license
    def __init__(self, svg: BytesIO) -> None:
        super().__init__()
        svg.seek(0)
        self.drawing: Drawing = svg2rlg(svg)
        self.width: int = self.drawing.minWidth()
        self.height: int = self.drawing.height
        self.drawing.setProperties({"vAlign": "CENTER", "hAlign": "CENTER"})

    def wrap(self, *_args):
        return self.width, self.height

    def draw(self) -> None:
        renderPDF.draw(self.drawing, self.canv, 0, 0)


def median_value(queryset, term):
    values = [
        v for v in queryset.values_list(term, flat=True).order_by(term) if v is not None
    ]
    count = len(values)
    if not count:
        return timedelta(seconds=0)
    if count % 2 == 1:
        return values[int(round(count / 2))]
    else:
        llim = max(0, int(count / 2 - 1))
        ulim = max(0, int(count / 2 + 1))
        return (
            sum(
                values[llim:ulim],
                start=timedelta(seconds=0),
            )
            / 2
        )


def get_schedule(world: World, fail_silently=True):
    pretalx_config = world.config.get("pretalx", {})
    if pretalx_config.get("url"):
        url = pretalx_config["url"]
    elif pretalx_config.get("domain"):
        domain = pretalx_config.get("domain")
        if not domain.endswith("/"):
            domain += "/"
        url = domain + pretalx_config["event"] + "/schedule/widget/v2.json"
    else:
        return {}

    try:
        r = requests.get(url)
        r.raise_for_status()
        return r.json()
    except requests.RequestException:
        logger.exception(f"Could not load schedule for world {world.pk} from {url}")
        if fail_silently:
            return {}
        else:
            raise


def pretalx_uni18n(i18nstring, locale="en"):
    if not i18nstring:
        return ""
    if isinstance(i18nstring, str):
        return i18nstring
    if i18nstring.get(locale):
        return i18nstring[locale]
    if i18nstring.get("en"):
        return i18nstring["en"]
    return list(i18nstring.values())[0]
