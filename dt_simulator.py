
import json, math, random, statistics
from typing import Dict, Any, Tuple, List

# Sampling helpers
def sample_dist(d: Dict[str, Any]) -> float:
    kind = d.get("distribution")
    if kind == "normal":
        return random.gauss(d["mean"], d["std"])
    if kind == "beta":
        return random.betavariate(d["alpha"], d["beta"])
    if kind == "lognormal":
        # mean here is the *linear* mean target; convert to mu, sigma in log-space approximately
        # Using approximation: linear_mean ≈ exp(mu + sigma^2/2) => mu ≈ ln(mean) - sigma^2/2
        sigma = d["sigma"]
        mu = math.log(d["mean"]) - 0.5 * (sigma ** 2)
        return random.lognormvariate(mu, sigma)
    raise ValueError(f"Unknown distribution: {kind}")

def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def run_scenario(cfg: Dict[str, Any], scenario_key: str) -> Dict[str, Any]:
    prng_seed = cfg["sim_params"].get("seed")
    if prng_seed is not None:
        random.seed(prng_seed + hash(scenario_key) % 1000000)

    runs = cfg["sim_params"]["runs"]
    months = cfg["sim_params"]["time_horizon_months"]
    scen = cfg["scenarios"][scenario_key]

    # Pre-bind commonly used dists
    hallu = cfg["physics"]["failure_rates"]["hallucination_rate"]
    precision = cfg["physics"]["failure_rates"]["recall_precision"]
    honey = cfg["physics"]["scraping_risks"]["honey_pot_probability"]
    lat_hil = cfg["physics"]["ingestion_latency_minutes"]["human_in_loop_validation"]
    lat_qc  = cfg["physics"]["ingestion_latency_minutes"]["manual_qc"]

    cac_d = cfg["economy"]["cac"]
    ltv_d = cfg["economy"]["ltv"]
    churn = cfg["economy"]["churn_triggers"]

    # Pricing heuristic: pick middle tier for product-led; retainer for service-first
    tier_prices = [t["price_monthly"] for t in cfg["economy"]["pricing"]["product_led"]["tiers"]]
    mid_tier_price = sorted(tier_prices)[len(tier_prices)//2] if tier_prices else 0.0
    retainer = cfg["economy"]["pricing"]["service_first"]["monthly_retainer"]

    # Collector
    revenue_samples, churn_samples, margin_samples, risk_events = [], [], [], []

    for r in range(runs):
        # Sample core "physics"
        p = clip(sample_dist(precision), 0.0, 1.0)  # precision
        h = clip(sample_dist(hallu), 0.0, 1.0)      # hallucination rate
        honey_p = clip(sample_dist(honey), 0.0, 1.0)

        latency_minutes = max(0.0, sample_dist(lat_hil) + sample_dist(lat_qc))
        latency_minutes *= scen["latency_penalty_multiplier"]

        # Risk math
        terms_violation_prob = scen["scraping_multiplier"] * (0.10 + 0.5 * honey_p) * scen["legal_risk_multiplier"]
        legal_veto = terms_violation_prob > cfg["agents"]["legal"]["veto_triggers"].get("terms_violation_probability_gt", 1.0)

        # Buyer model features (toy placeholders)
        coverage_ratio = clip(0.75 + 0.10 * scen["scraping_multiplier"] - 0.05 * legal_veto, 0.0, 1.0)
        data_freshness_days = max(0.0, 7.0 - 2.0 * scen["scraping_multiplier"] + 0.5 * legal_veto)

        w = cfg["agents"]["icp_buyer"]["purchase_probability_model"]["weights"]
        intercept = cfg["agents"]["icp_buyer"]["purchase_probability_model"]["intercept"]

        # Assume normalized research_intensity and funding_history_score around mid
        research_intensity = 0.6
        funding_history = 0.6

        lin = (intercept
               + w["research_intensity"] * research_intensity
               + w["funding_history_score"] * funding_history
               + w["data_freshness_days"] * data_freshness_days
               + w["coverage_ratio"] * coverage_ratio)

        win_prob = clip(logistic(lin), 0.0, 1.0)

        # Demand proxy: expected new customers this month (toy)
        # Higher when product-led mid tier attractive & latency is low & precision is high
        demand = 3.0 * win_prob * (0.8 + 0.2 * (p > 0.9)) * (1.0 - min(latency_minutes/120.0, 0.5))
        # Stochastic new customers (Poisson-ish using Gamma-Poisson approximation)
        lam = max(0.1, demand)
        new_customers = random.poisson(lam) if hasattr(random, "poisson") else max(0, int(random.expovariate(1.0/lam)))

        # Price mix: blend between service-first and product-led based on scenario
        price_per_customer = 0.5 * retainer + 0.5 * mid_tier_price

        # Churn probability blended by triggers
        churn_prob = churn["missed_grant_opportunity_prob"] * (1.0 + 0.5 * h) \
                   + churn["data_latency_over_sla_prob"] * (1.0 + 0.01 * max(0.0, latency_minutes-60.0)) \
                   + (0.02 if p < churn["precision_drop_below"] else 0.0)
        churn_prob = clip(churn_prob, 0.0, 0.9)

        # Unit economics
        cac = sample_dist(cac_d) * scen["api_cost_multiplier"]
        ltv = sample_dist(ltv_d)
        gross_margin = clip((ltv - cac) / max(ltv, 1e-9), 0.0, 1.0)

        # CFO veto if margins too low
        if gross_margin < cfg["agents"]["cfo"]["veto_on_margin_below"]:
            # Reduce new customers due to slowed spend/experiments
            new_customers = int(new_customers * 0.6)

        # Monthly aggregates (toy, per-run == per-month here for simplicity)
        revenue = new_customers * price_per_customer
        churned = int(new_customers * churn_prob)

        revenue_samples.append(revenue)
        churn_samples.append(churn_prob)
        margin_samples.append(gross_margin)
        risk_events.append(1 if legal_veto else 0)

    def summarize(x: List[float]) -> Dict[str, float]:
        if not x: return {"mean": 0, "p10": 0, "p50": 0, "p90": 0}
        xs = sorted(x)
        n = len(xs)
        def pct(p): 
            idx = min(n-1, max(0, int(p*(n-1))))
            return xs[idx]
        return {
            "mean": statistics.fmean(xs),
            "p10": pct(0.10),
            "p50": pct(0.50),
            "p90": pct(0.90)
        }

    return {
        "revenue_usd": summarize(revenue_samples),
        "churn_rate": summarize(churn_samples),
        "gross_margin": summarize(margin_samples),
        "legal_veto_rate": summarize(risk_events)
    }

def run_all(cfg: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for scen in cfg["meta"]["scenarios"]:
        out[scen] = run_scenario(cfg, scen)
    return out

if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to JSON config")
    ap.add_argument("--out", default="dt_results.json")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)
    results = run_all(cfg)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
