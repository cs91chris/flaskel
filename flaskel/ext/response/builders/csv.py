import csv
import io

from ..dictutils import to_flatten
from .builder import Builder


class CsvBuilder(Builder):
    def _build(self, data, **kwargs):
        data = to_flatten(
            data or [],
            to_dict=kwargs.pop("to_dict", None),
            parent_key=self.conf.get("RB_FLATTEN_PREFIX", ""),
            sep=self.conf.get("RB_FLATTEN_SEPARATOR", ""),
        )

        filename = kwargs.pop("filename", self.conf.get("RB_CSV_DEFAULT_NAME"))
        self._headers.update(
            {
                "X-Total-Rows": len(data),
                "X-Total-Columns": len(data[0].keys()),
                "Content-Disposition": f"attachment; filename={filename}.csv",
            }
        )

        delimiter = self.conf.get("RB_CSV_DELIMITER")
        if delimiter:
            kwargs.update(delimiter=delimiter)

        quotechar = self.conf.get("RB_CSV_QUOTING_CHAR")
        if quotechar:
            kwargs.update(quotechar=quotechar)

        dialect = self.conf.get("RB_CSV_DIALECT")
        if dialect:
            kwargs.update(dialect=dialect)

        return self.to_csv(data or [], **kwargs)

    @staticmethod
    def to_me(data: list, **kwargs):
        kwargs.setdefault("dialect", "excel-tab")
        kwargs.setdefault("delimiter", ";")
        kwargs.setdefault("quotechar", '"')
        kwargs.setdefault("quoting", csv.QUOTE_ALL)

        output = io.StringIO()
        w = csv.DictWriter(output, data[0].keys() if data else "", **kwargs)
        w.writeheader()
        w.writerows(data)

        return output.getvalue()

    @staticmethod
    def to_csv(data, **kwargs):
        return CsvBuilder.to_me(data, **kwargs)

    @staticmethod
    def to_dict(data, **kwargs):
        kwargs.setdefault("dialect", "excel-tab")
        kwargs.setdefault("delimiter", ";")
        kwargs.setdefault("quotechar", '"')
        kwargs.setdefault("quoting", csv.QUOTE_ALL)

        return list(csv.DictReader(io.StringIO(data), **kwargs))
