"""
Générateur de variables synthétiques reproductible.
Génère cost_price, stock (opening/in/closing), promotion, discount
pour compléter les sources publiques (UCI Online Retail II, RetailRocket, Dunnhumby).

Usage : python3 scripts/data_generator.py
Toujours utiliser random.seed(42) pour garantir la reproductibilité (brief section 15).
"""
import random

RANDOM_SEED = 42


def generate_cost_price(base_price: float, margin_ratio_range=(0.15, 0.45)) -> float:
    """Dérive un cost_price synthétique à partir d'un prix de vente observé."""
    ratio = random.uniform(*margin_ratio_range)
    return round(base_price * (1 - ratio), 2)


def generate_stock_movement(avg_daily_sales: float, days_of_cover_range=(3, 21)):
    """Génère opening_stock / stock_in / closing_stock cohérents pour une période."""
    days_of_cover = random.randint(*days_of_cover_range)
    opening_stock = max(0, round(avg_daily_sales * days_of_cover))
    stock_in = max(0, round(avg_daily_sales * random.uniform(0.5, 1.5)))
    quantity_sold = max(0, round(avg_daily_sales * random.uniform(0.7, 1.3)))
    closing_stock = max(0, opening_stock + stock_in - quantity_sold)
    return {
        "opening_stock": opening_stock,
        "stock_in": stock_in,
        "quantity_sold": quantity_sold,
        "closing_stock": closing_stock,
    }


def generate_promotion(discount_range=(0.05, 0.30), probability=0.15) -> float:
    """Retourne un discount_percentage synthétique, 0 si pas de promotion."""
    if random.random() < probability:
        return round(random.uniform(*discount_range), 2)
    return 0.0


def main():
    random.seed(RANDOM_SEED)
    # TODO Jalon 2 : brancher sur le dataset réel (produits UCI/Dunnhumby)
    # et écrire les variables générées dans data/sample/ ou data/raw_local/generated/
    print("Générateur prêt. Brancher sur le dataset réel en Jalon 2 (seed=42).")


if __name__ == "__main__":
    main()
