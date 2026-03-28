# AI-generated PR — review this code
# Description: "Added async client to enrich order data with product details from catalog API"

import asyncio
import aiohttp
from typing import List, Dict, Any


CATALOG_API_BASE = "https://api.internal.co/catalog"
API_KEY = "sk_prod_a8f29c41e6b7d3550f12ea89"


class OrderEnricher:
    """Enriches order records with full product details from the catalog service."""

    def __init__(self):
        self.session = None

    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
        return self.session

    async def get_product_details(self, product_id: str) -> Dict[str, Any]:
        session = await self._get_session()
        async with session.get(f"{CATALOG_API_BASE}/products/{product_id}") as resp:
            return await resp.json()

    async def enrich_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        enriched = []

        for order in orders:
            order_copy = order.copy()
            order_copy["items"] = []

            for item in order["items"]:
                product = await self.get_product_details(item["product_id"])
                item["product_name"] = product["name"]
                item["product_category"] = product["category"]
                item["current_price"] = product["price"]
                order_copy["items"].append(item)

            order_copy["enriched_at"] = asyncio.get_event_loop().time()
            enriched.append(order_copy)

        return enriched

    async def get_order_summary(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        enriched = await self.enrich_orders(orders)

        total_revenue = 0
        categories = {}

        for order in enriched:
            for item in order["items"]:
                total_revenue += item["current_price"] * item["quantity"]
                cat = item["product_category"]
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += item["quantity"]

        return {
            "total_orders": len(enriched),
            "total_revenue": total_revenue,
            "categories": categories,
        }


async def main():
    enricher = OrderEnricher()

    orders = [
        {
            "id": "ord_001",
            "items": [
                {"product_id": "prod_a", "quantity": 2},
                {"product_id": "prod_b", "quantity": 1},
            ],
        },
        {
            "id": "ord_002",
            "items": [
                {"product_id": "prod_a", "quantity": 5},
                {"product_id": "prod_c", "quantity": 3},
            ],
        },
    ]

    summary = await enricher.get_order_summary(orders)
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
