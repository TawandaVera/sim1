
from pydantic import BaseModel, Field, validator, conint, confloat
from typing import Dict, Any, List, Literal, Optional

class DistNormal(BaseModel):
    distribution: Literal["normal"]
    mean: float
    std: float
    @validator("std")
    def std_pos(cls, v): 
        if v <= 0: 
            raise ValueError("std must be > 0")
        return v

class DistBeta(BaseModel):
    distribution: Literal["beta"]
    alpha: confloat(gt=0)
    beta: confloat(gt=0)

class DistLogNormal(BaseModel):
    distribution: Literal["lognormal"]
    mean: confloat(gt=0)
    sigma: confloat(gt=0)

Distribution = DistNormal | DistBeta | DistLogNormal

class Physics(BaseModel):
    ingestion_latency_minutes: Dict[str, DistNormal]
    failure_rates: Dict[str, Distribution]
    scraping_risks: Dict[str, Distribution]

class CFO(BaseModel):
    budget_threshold_monthly_usd: confloat(gt=0)
    veto_on_margin_below: confloat(gt=0, lt=1)
    spend_flex_percent: confloat(ge=0, le=1)

class Legal(BaseModel):
    veto_triggers: Dict[str, Any]

class ICPBuyer(BaseModel):
    purchase_probability_model: Dict[str, Any]

class Agents(BaseModel):
    cfo: CFO
    legal: Legal
    icp_buyer: ICPBuyer

class PricingTier(BaseModel):
    name: str
    price_monthly: confloat(gt=0)

class Pricing(BaseModel):
    service_first: Dict[str, confloat(ge=0)]
    product_led: Dict[str, List[PricingTier]]

class Economy(BaseModel):
    cac: Distribution
    ltv: Distribution
    pricing: Pricing
    churn_triggers: Dict[str, Any]

class Scenario(BaseModel):
    description: str
    scraping_multiplier: confloat(ge=0)
    api_cost_multiplier: confloat(gt=0)
    latency_penalty_multiplier: confloat(gt=0)
    legal_risk_multiplier: confloat(gt=0)

class SimParams(BaseModel):
    runs: conint(ge=1)
    seed: Optional[int] = None
    time_horizon_months: conint(ge=1)

class Config(BaseModel):
    meta: Dict[str, Any]
    sim_params: SimParams
    physics: Physics
    agents: Agents
    economy: Economy
    scenarios: Dict[str, Scenario]
