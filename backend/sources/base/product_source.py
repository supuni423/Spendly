from abc import ABC, abstractmethod

from sources.base.source_result import SourceProduct


class ProductSource(ABC):
    """Interface every external product source adapter must implement.

    Adding a newly permitted source (Section 8 of the project spec) means
    writing one class that implements this interface and returns
    SourceProduct — no changes to the matching engine, comparison API, or
    agent tools required.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def search_products(self, query: str, limit: int = 10) -> list[SourceProduct]:
        ...

    @abstractmethod
    def get_product(self, source_product_id: str) -> SourceProduct | None:
        ...

    @abstractmethod
    def get_current_price(self, source_product_id: str) -> float | None:
        ...

    @abstractmethod
    def check_availability(self, source_product_id: str) -> bool:
        ...
