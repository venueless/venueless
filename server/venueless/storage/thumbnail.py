import hashlib
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils.timezone import now
from PIL import Image, ImageOps
from PIL.Image import Resampling

from venueless.storage.external import get_extension_from_response, retrieve_url
from venueless.storage.models import StoredFile


def resize_image(image, width, height):
    image = ImageOps.exif_transpose(image)

    if image.width / image.height > width / height:
        newwidth = int(image.height * (width / height))
        newheight = image.height
    else:
        newwidth = image.width
        newheight = int(image.width / (width / height))
    image = image.crop(
        (
            0.5 * (image.width - newwidth),
            0.5 * (image.height - newheight),
            0.5 * (image.width - newwidth) + newwidth,
            0.5 * (image.height - newheight) + newheight,
        )
    )

    image.thumbnail((width, height), resample=Resampling.LANCZOS)

    return image


def get_thumbnail(world, url, width, height):
    response = retrieve_url(url)
    content_type, extension = get_extension_from_response(response)
    if not extension:
        return

    filename = (
        f"thumb_{hashlib.sha256(url.encode()).hexdigest()[:32]}_{width}x{height}.png"
    )
    try:
        sf = StoredFile.objects.get(
            world=world,
            filename=filename,
            public=True,
        )
        return sf.file.url
    except StoredFile.DoesNotExist:
        pass

    image = Image.open(BytesIO(response.content), formats=("PNG", "GIF", "JPEG"))
    try:
        image.load()
    except:
        raise ValueError("Could not load image")

    image_out = resize_image(image, width, height)
    if image_out.mode == "P":
        image_out = image_out.convert("RGBA")
    if image_out.mode not in ("1", "L", "RGB", "RGBA"):
        image_out = image_out.convert("RGB")
    buffer = BytesIO()
    image_out.save(fp=buffer, format="PNG")
    imgfile = ContentFile(buffer.getvalue())

    uid = uuid.uuid4()
    stored_file = StoredFile.objects.create(
        id=uid,
        world=world,
        date=now(),
        filename=filename,
        type="image/png",
        public=True,
        source_url=response.url[:254],
    )
    stored_file.file.save(filename, imgfile)
    return stored_file.file.url
