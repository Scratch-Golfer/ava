"""Menu definition and order-state logic for the cafe voice ordering prototype.

Keep this file as the single source of truth for what's sellable. Adding a
drink or a size is just adding a dict entry here.
"""

MENU = {
    "espresso": {"sizes": {"single": 2.40, "double": 2.80}},
    "americano": {"sizes": {"small": 2.90, "medium": 3.20, "large": 3.50}},
    "latte": {"sizes": {"small": 3.30, "medium": 3.70, "large": 4.10}},
    "cappuccino": {"sizes": {"small": 3.30, "medium": 3.70, "large": 4.10}},
    "flat white": {"sizes": {"small": 3.40, "medium": 3.70}},
    "cortado": {"sizes": {"small": 3.20}},
    "mocha": {"sizes": {"small": 3.60, "medium": 4.00, "large": 4.40}},
    "filter coffee": {"sizes": {"medium": 2.80}},
    "chai latte": {"sizes": {"small": 3.40, "medium": 3.80, "large": 4.20}},
    "matcha latte": {"sizes": {"small": 3.80, "medium": 4.20, "large": 4.60}},
    "hot chocolate": {"sizes": {"small": 3.20, "medium": 3.60, "large": 4.00}},
    "english breakfast tea": {"sizes": {"small": 2.40, "medium": 2.70, "large": 3.00}},
    "earl grey": {"sizes": {"small": 2.40, "medium": 2.70, "large": 3.00}},
    "peppermint tea": {"sizes": {"small": 2.40, "medium": 2.70, "large": 3.00}},
    "iced latte": {"sizes": {"medium": 3.80, "large": 4.20}},
    "iced americano": {"sizes": {"medium": 3.30, "large": 3.60}},
}

MILK_OPTIONS = ["whole", "semi-skimmed", "oat", "almond", "soy"]
MILK_SURCHARGE = {"oat": 0.50, "almond": 0.50, "soy": 0.40}

EXTRA_SHOT_PRICE = 0.60
SYRUP_PRICE = 0.50
SYRUP_OPTIONS = ["vanilla", "caramel", "hazelnut"]


class OrderState:
    """Holds the cart for the current customer. One instance per session."""

    def __init__(self):
        self.items: list[dict] = []

    def add_item(
        self,
        drink: str,
        size: str,
        milk: str | None = None,
        extra_shots: int = 0,
        syrup: str | None = None,
    ) -> dict:
        drink = drink.lower().strip()
        size = size.lower().strip()

        if drink not in MENU:
            return {"error": f"'{drink}' isn't on the menu."}
        if size not in MENU[drink]["sizes"]:
            available = ", ".join(MENU[drink]["sizes"].keys())
            return {"error": f"'{size}' isn't a valid size for {drink}. Available: {available}"}
        if milk and milk not in MILK_OPTIONS:
            return {"error": f"'{milk}' isn't a milk option we offer."}
        if syrup and syrup not in SYRUP_OPTIONS:
            return {"error": f"'{syrup}' isn't a syrup option we offer."}

        price = MENU[drink]["sizes"][size]
        if milk in MILK_SURCHARGE:
            price += MILK_SURCHARGE[milk]
        price += extra_shots * EXTRA_SHOT_PRICE
        if syrup:
            price += SYRUP_PRICE

        item = {
            "drink": drink,
            "size": size,
            "milk": milk,
            "extra_shots": extra_shots,
            "syrup": syrup,
            "price": round(price, 2),
        }
        self.items.append(item)
        return {"added": item, "running_total": self.total()}

    def total(self) -> float:
        return round(sum(item["price"] for item in self.items), 2)

    def summary(self) -> str:
        if not self.items:
            return "Your order is empty."
        lines = []
        for item in self.items:
            desc = f"{item['size']} {item['drink']}"
            extras = []
            if item["milk"]:
                extras.append(f"{item['milk']} milk")
            if item["extra_shots"]:
                extras.append(f"{item['extra_shots']} extra shot(s)")
            if item["syrup"]:
                extras.append(f"{item['syrup']} syrup")
            if extras:
                desc += " (" + ", ".join(extras) + ")"
            lines.append(f"- {desc}: £{item['price']:.2f}")
        lines.append(f"Total: £{self.total():.2f}")
        return "\n".join(lines)

    def clear(self):
        self.items = []
