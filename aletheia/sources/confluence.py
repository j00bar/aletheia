import email.parser
import email.policy
import logging
import os
import re
import shutil
import tempfile
import unicodedata

from atlassian.confluence import Confluence
from bs4 import BeautifulSoup

from .. import DEFAULTS
from ..exceptions import AletheiaException
from ..utils import devel_dir

logger = logging.getLogger(__name__)


def __get_from_env__(key, default=None, coerce=None):
    try:
        value = os.environ[f"ATLASSIAN_{key}"]
        return coerce(value) if coerce else value
    except KeyError:
        if default is not None:
            return default
        raise AletheiaException(
            f"Missing environment variable found with Confluence configuration. {key} not found."
        ) from None


def get_client_from_env():
    client = Confluence(
        url=__get_from_env__("URL"),
        username=__get_from_env__("API_USERNAME"),
        password=__get_from_env__("API_KEY"),
        cloud=__get_from_env__("CLOUD", default=False, coerce=bool),
    )
    return client


def page_to_html_and_attachments(client, page_id, output_path):
    rfc822_bytes = client.get_page_as_word(page_id)
    parser = email.parser.BytesFeedParser(policy=email.policy.default)
    parser.feed(rfc822_bytes)
    msg = parser.close()
    image_src_map = {}
    html = ""
    for part in msg.walk():
        if part.is_multipart():
            continue
        if part.get_content_type() == "text/html":
            html = part.get_content()
        else:
            content_location = part["Content-Location"]
            content_id = content_location.rsplit("/", 1)[-1]
            image_src_map[content_id] = part.get_content()
    doc = BeautifulSoup(html)
    # Fix up embedded images
    for img_src, img_content in image_src_map.items():
        for tag in doc.find_all(lambda tag: tag.name == "img" and tag.get("src") == img_src):
            if "data-linked-resource-default-alias" in tag.attrs:
                img_filename = tag["data-linked-resource-default-alias"]
                attrs_to_keep = ["width", "height"]
                attrs = [str(attr) for attr in tag.attrs if str(attr) not in attrs_to_keep]
                for attr in attrs:
                    del tag[attr]
                tag["src"] = img_filename
                open(os.path.join(output_path, img_filename), "wb").write(img_content)
            else:
                # Remove media groups - the Word export doesn't have the data for them
                tag.extract()
    # If this page has subpages, strip the TOC from the outputted HTML
    for tag in doc.find_all("ul", "childpages-macro"):
        tag.extract()
    open(os.path.join(output_path, "index.html"), "w").write(str(doc))


def slugify(title):
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    title = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"[-\s]+", "-", title).strip("-_")


class Source:
    def __init__(self, config=DEFAULTS, page_id=""):
        self.config = config
        self.page_id = page_id
        self._tempdir = None

    @property
    def working_dir(self):
        if not self._tempdir:
            if self.config.devel:
                self._tempdir = devel_dir(f"confluence--{self.page_id}")
            else:
                self._tempdir = tempfile.mkdtemp()
        return self._tempdir

    def cleanup(self):
        try:
            if self._tempdir:
                shutil.rmtree(self._tempdir)
        except:  # noqa: E722
            logger.warning(f"Cleanup failed removing Confluence tempdir {self._tempdir}")

    def run(self):
        client = get_client_from_env()
        logger.info("Downloading main page from Confluence")
        page_to_html_and_attachments(client, self.page_id, self.working_dir)
        for child_page in client.get_page_child_by_type(self.page_id, type="page", start=None, limit=None):
            logger.info(f"Downloading child page {child_page['title']} from Confluence")
            child_page_dir = os.path.join(self.working_dir, slugify(child_page["title"]))
            os.makedirs(child_page_dir, exist_ok=True)
            page_to_html_and_attachments(client, child_page["id"], child_page_dir)
        logger.info("Confluence download complete.")
        return self.working_dir
