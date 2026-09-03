import re
from dataclasses import dataclass, field

from schemas.price_comparison import CurrentProductInput, MatchType
from sources.base.source_result import SourceProduct

BRAND_WEIGHT = 0.30
TITLE_WEIGHT = 0.35
CATEGORY_WEIGHT = 0.15
ATTRIBUTES_WEIGHT = 0.20

HIGH_CONFIDENCE_THRESHOLD = 0.75
SIMILAR_THRESHOLD = 0.40

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_ALNUM_RE = re.compile(r"[^a-z0-9]")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _compact(text: str) -> str:
    return _ALNUM_RE.sub("", text.lower())


def _title_similarity(a: str, b: str) -> float:
    tokens_a, tokens_b = _tokens(a), _tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _attribute_similarity(a: dict[str, str], b: dict[str, str]) -> tuple[float, bool]:
    """Returns (similarity, has_conflict). has_conflict is True when a
    shared attribute key (e.g. "color") has different values on each side —
    a strong signal this is a variant (Section 7.1's "same shoe, different
    color") rather than the identical item.
    """
    common_keys = set(k.lower() for k in a) & set(k.lower() for k in b)
    if not common_keys:
        return 0.0, False

    a_lower = {k.lower(): v.lower() for k, v in a.items()}
    b_lower = {k.lower(): v.lower() for k, v in b.items()}
    matches = sum(1 for k in common_keys if a_lower[k] == b_lower[k])
    similarity = matches / len(common_keys)
    return similarity, similarity < 1.0


@dataclass
class MatchResult:
    match_type: MatchType
    confidence: float
    breakdown: dict[str, float] = field(default_factory=dict)


def match_product(candidate: CurrentProductInput, source_product: SourceProduct) -> MatchResult:
    # Strong identity signals short-circuit straight to EXACT_MATCH: either
    # the titles are identical once formatting noise (spacing, punctuation,
    # case) is stripped, or both sides carry the same SKU/model number. A
    # composite score is never allowed to produce EXACT_MATCH itself — that
    # would risk presenting a merely-similar item as the same product,
    # which Section 7.1 explicitly forbids.
    if _compact(candidate.product_name) == _compact(source_product.name):
        return MatchResult(MatchType.EXACT_MATCH, 0.99, {"title_exact": 1.0})

    for cand_id, src_id in (
        (candidate.sku, source_product.sku),
        (candidate.model_number, source_product.model_number),
    ):
        if cand_id and src_id and cand_id.strip().lower() == src_id.strip().lower():
            return MatchResult(MatchType.EXACT_MATCH, 0.97, {"id_exact": 1.0})

    # A category present on both sides that disagrees is a hard
    # disambiguator: a phone and a phone case are different kinds of
    # product for shopping purposes, no matter how similar their titles or
    # brand look.
    if (
        candidate.category
        and source_product.category
        and candidate.category.lower() != source_product.category.lower()
    ):
        return MatchResult(MatchType.NO_MATCH, 0.0, {"category_conflict": 1.0})

    weights: dict[str, float] = {}
    scores: dict[str, float] = {}

    scores["title"] = _title_similarity(candidate.product_name, source_product.name)
    weights["title"] = TITLE_WEIGHT

    if candidate.brand and source_product.brand:
        scores["brand"] = 1.0 if candidate.brand.lower() == source_product.brand.lower() else 0.0
        weights["brand"] = BRAND_WEIGHT

    if candidate.category and source_product.category:
        scores["category"] = 1.0  # equality already guaranteed by the conflict check above
        weights["category"] = CATEGORY_WEIGHT

    attribute_similarity, has_variant_conflict = _attribute_similarity(
        candidate.attributes, source_product.attributes
    )
    if candidate.attributes and source_product.attributes:
        scores["attributes"] = attribute_similarity
        weights["attributes"] = ATTRIBUTES_WEIGHT

    total_weight = sum(weights.values())
    score = (
        sum(scores[key] * weights[key] for key in weights) / total_weight
        if total_weight > 0
        else 0.0
    )
    score = round(score, 3)

    if score >= HIGH_CONFIDENCE_THRESHOLD:
        match_type = MatchType.HIGH_CONFIDENCE_MATCH
    elif score >= SIMILAR_THRESHOLD:
        match_type = MatchType.SIMILAR_PRODUCT
    else:
        match_type = MatchType.NO_MATCH

    # A conflicting variant attribute (different color/size/etc.) means
    # this is, at best, a similar product — never presented as the same
    # item even if everything else lines up.
    if has_variant_conflict and match_type == MatchType.HIGH_CONFIDENCE_MATCH:
        match_type = MatchType.SIMILAR_PRODUCT

    return MatchResult(match_type, score, scores)
