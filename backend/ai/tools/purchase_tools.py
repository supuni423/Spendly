from ai.tools.context import ToolContext
from services.purchase_service import list_purchases, to_purchase_read

GET_PURCHASE_HISTORY_DECLARATION = {
    "name": "get_purchase_history",
    "description": (
        "Returns the user's past purchases (product name, price, quantity, date, category), "
        "most recent first. Use this to understand what the user already owns."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of purchases to return (default 10).",
            }
        },
    },
}


def get_purchase_history(context: ToolContext, limit: int = 10) -> list[dict]:
    purchases = list_purchases(context.db, context.user_id)[:limit]
    return [
        {
            "product_name": read.product.name,
            "brand": read.product.brand,
            "category": read.product.category,
            "purchase_price": read.purchase_price,
            "quantity": read.quantity,
            "purchase_date": read.purchase_date.isoformat(),
        }
        for read in (to_purchase_read(context.db, p) for p in purchases)
    ]
