"""
Estimation de l'élasticité prix-demande (Jalon 6).

L'élasticité estimée n'est pas causale — c'est une régression
sur données observationnelles (log(quantité) ~ log(prix) par produit), pas une
expérimentation contrôlée. À ne jamais présenter comme une vérité absolue,
toujours "sous les hypothèses du modèle" (cf. docs/pricing.md).
"""
import numpy as np
import pandas as pd

MIN_DISTINCT_PRICES = 5
MIN_OBSERVATIONS = 20
MIN_PRICE_CV = 0.05  # coefficient de variation minimal pour espérer un signal exploitable

# Élasticité par défaut, appliquée quand un produit n'a pas assez de variation de
# prix observée pour une régression fiable (majorité du catalogue, cf. audit
# 19/08 : 305/4631 produits éligibles à l'estimation). Valeur assumée, pas
# mesurée : -1.5 correspond à une demande modérément élastique, hypothèse
# usuelle pour des biens de consommation courante hors produits de luxe/premiers
# prix (littérature retail générale) — documenté comme telle, jamais confondue
# avec une élasticité observée.
DEFAULT_ASSUMED_ELASTICITY = -1.5

# Bornes de sécurité appliquées à l'élasticité estimée par régression. Sur un
# petit échantillon bruité (peu de variation de prix, confondus avec saisonnalité
# et promotions non contrôlées dans cette régression bivariée simple), le
# coefficient peut sortir d'une plage économiquement plausible pour un bien
# normal (élasticité positive = la demande augmenterait avec le prix, signe
# d'un artefact de régression plutôt que d'un vrai bien de Veblen/Giffen ici).
# Une élasticité non bornée pourrait inverser le sens de la recommandation de
# prix — cf. tests/test_pricing.py.
ELASTICITY_BOUNDS = (-10.0, 0.0)


def is_eligible_for_estimation(price_series: pd.Series) -> bool:
    if len(price_series) < MIN_OBSERVATIONS:
        return False
    if price_series.nunique() < MIN_DISTINCT_PRICES:
        return False
    cv = price_series.std() / price_series.mean() if price_series.mean() else 0
    return cv > MIN_PRICE_CV


def estimate_elasticity(df_product: pd.DataFrame) -> dict:
    """Régression log-log : log(quantité+1) = a + elasticity * log(prix).

    Retourne un dict avec l'élasticité, le R², le nombre d'observations et si
    la valeur est estimée (régression) ou assumée (fallback, cf.
    DEFAULT_ASSUMED_ELASTICITY).
    """
    # log(0) est indéfini : un prix à 0 (article offert/promo à 100%) casserait la
    # régression log-log. Ces lignes sont écartées de l'estimation d'élasticité
    # (mais restent dans fact_sales pour le reste du pipeline).
    df_product = df_product[df_product["unit_price"] > 0]
    prices = df_product["unit_price"]
    if not is_eligible_for_estimation(prices):
        return {
            "elasticity": DEFAULT_ASSUMED_ELASTICITY,
            "r_squared": None,
            "n_observations": len(df_product),
            "is_estimated": False,
        }

    log_price = np.log(prices.values)
    log_qty = np.log(df_product["quantity"].values + 1)

    slope, intercept = np.polyfit(log_price, log_qty, deg=1)
    predicted = slope * log_price + intercept
    ss_res = np.sum((log_qty - predicted) ** 2)
    ss_tot = np.sum((log_qty - log_qty.mean()) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    clipped_slope = float(np.clip(slope, ELASTICITY_BOUNDS[0], ELASTICITY_BOUNDS[1]))

    return {
        "elasticity": clipped_slope,
        "r_squared": float(r_squared),
        "n_observations": len(df_product),
        "is_estimated": True,
    }


def estimate_elasticity_for_all_products(price_history: pd.DataFrame) -> pd.DataFrame:
    """Applique estimate_elasticity à chaque produit du panel. Agrège d'abord
    prix/quantité au niveau produit-jour (plusieurs commandes le même jour pour
    un même produit ne doivent pas être traitées comme des prix indépendants)."""
    daily = (
        price_history.groupby(["product_id", "ds"])
        .agg(unit_price=("unit_price", "mean"), quantity=("quantity", "sum"))
        .reset_index()
    )

    results = []
    for product_id, group in daily.groupby("product_id"):
        result = estimate_elasticity(group)
        result["product_id"] = product_id
        results.append(result)

    return pd.DataFrame(results)[["product_id", "elasticity", "r_squared", "n_observations", "is_estimated"]]
