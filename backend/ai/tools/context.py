from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from schemas.price_comparison import CurrentProductInput, PriceComparisonResult


@dataclass
class ToolContext:
    """Bound to one analysis request. Every tool call during that request
    reads from the same db session, user, and candidate product — and, via
    the cache below, the same price-comparison snapshot — so the agent
    can't get inconsistent numbers by calling market tools in different
    orders or more than once.
    """

    db: Session
    user_id: int
    candidate: CurrentProductInput
    _price_comparison_cache: PriceComparisonResult | None = field(
        default=None, init=False, repr=False
    )
