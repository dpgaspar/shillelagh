"""
An adapter that scrapes HTML tables.
"""

# pylint: disable=invalid-name

import urllib.parse
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pandas as pd

from shillelagh.adapters.base import Adapter
from shillelagh.adapters.memory.pandas import get_df_data, get_field, type_map
from shillelagh.fields import Field
from shillelagh.filters import Filter
from shillelagh.lib import SimpleCostModel
from shillelagh.typing import RequestedOrder, Row

SUPPORTED_PROTOCOLS = {"http", "https", "ftp", "file"}
AVERAGE_NUMBER_OF_ROWS = 100


class HTMLTableAPI(Adapter):

    """
    An adapter for scraping HTML tables.
    """

    safe = True

    @staticmethod
    def supports(uri: str, fast: bool = True, **kwargs: Any) -> Optional[bool]:
        parsed = urllib.parse.urlparse(uri)
        if parsed.scheme not in SUPPORTED_PROTOCOLS:
            return False
        if fast:
            return None

        # table index can be specified as an anchor; remove
        uri = urllib.parse.urlunparse(parsed._replace(fragment=""))
        try:
            dataframes = pd.read_html(uri, flavor="bs4")
        except Exception:  # pylint: disable=broad-except
            return False

        return len(dataframes) > 0

    @staticmethod
    def parse_uri(uri: str) -> Tuple[str, int]:
        parsed = urllib.parse.urlparse(uri)

        # extract table index from anchor and remove from URI
        try:
            index = int(parsed.fragment or "0")
        except ValueError:
            index = 0
        uri = urllib.parse.urlunparse(parsed._replace(fragment=""))

        return uri, index

    def __init__(self, uri: str, index: int = 0):
        super().__init__()

        self.df = pd.read_html(uri, flavor="bs4")[index]
        self.columns = {
            column_name: get_field(dtype)
            for column_name, dtype in zip(self.df.columns, self.df.dtypes)
            if dtype.kind in type_map
        }

    def get_columns(self) -> Dict[str, Field]:
        return self.columns

    get_cost = SimpleCostModel(AVERAGE_NUMBER_OF_ROWS)

    def get_data(
        self,
        bounds: Dict[str, Filter],
        order: List[Tuple[str, RequestedOrder]],
    ) -> Iterator[Row]:
        yield from get_df_data(self.df, self.columns, bounds, order)