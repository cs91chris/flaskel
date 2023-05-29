from vbcore.http.headers import ContentTypeEnum

from .builders import (
    Base64Builder,
    CsvBuilder,
    HtmlBuilder,
    JsonBuilder,
    XmlBuilder,
    YamlBuilder,
)

DEFAULT_BUILDERS = {
    "csv": CsvBuilder(ContentTypeEnum.CSV.value),
    "html": HtmlBuilder(ContentTypeEnum.HTML.value),
    "xml": XmlBuilder(ContentTypeEnum.XML.value),
    "json": JsonBuilder(ContentTypeEnum.JSON.value),
    "yaml": YamlBuilder("application/yaml"),
    "base64": Base64Builder("application/base64"),
}


def set_default_config(app):
    app.config.setdefault(
        "RB_DEFAULT_ACCEPTABLE_MIMETYPES",
        {v.mimetype for _, v in DEFAULT_BUILDERS.items()},
    )
    app.config.setdefault(
        "RB_DEFAULT_RESPONSE_FORMAT", DEFAULT_BUILDERS["json"].mimetype
    )
    app.config.setdefault("RB_FORMAT_KEY", "format")
    app.config.setdefault("RB_DEFAULT_ENCODE", "utf-8")
    app.config.setdefault("RB_DEFAULT_DUMP_INDENT", None)
    app.config.setdefault("RB_BASE64_ALTCHARS", None)
    app.config.setdefault("RB_HTML_DEFAULT_TEMPLATE", None)
    app.config.setdefault("RB_HTML_AS_TABLE", False)
    app.config.setdefault("RB_YAML_ALLOW_UNICODE", True)
    app.config.setdefault("RB_CSV_DEFAULT_NAME", "filename")
    app.config.setdefault("RB_CSV_DELIMITER", ";")
    app.config.setdefault("RB_CSV_QUOTING_CHAR", '"')
    app.config.setdefault("RB_CSV_DIALECT", "excel-tab")
    app.config.setdefault("RB_XML_CDATA", False)
    app.config.setdefault("RB_XML_ROOT", "ROOT")
    app.config.setdefault("RB_FLATTEN_PREFIX", "")
    app.config.setdefault("RB_FLATTEN_SEPARATOR", "_")
    app.config.setdefault("RB_JSONP_PARAM", "callback")
