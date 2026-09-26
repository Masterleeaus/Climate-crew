from typing import List, Literal, Any
from pydantic import BaseModel, Field

class CausalNode(BaseModel):
    description: str = Field(description="Description of the event or consequence")
    category: Literal["Physical", "Economic", "Social", "Logistics", "Root"] = Field(description="Category of the impact")
    impact_score: float = Field(description="Severity score 1-10")
    probability: float = Field(default=0.0, description="Likelihood of this consequence occurring (0-1)")
    time_lag: str = Field(default="immediate", description="Estimated time until impact (e.g., '2 days')")
    evidence: str = Field(default="LLM inference", description="Source of this prediction (e.g., 'ML Model', 'Historical Data')")
    children: List['CausalNode'] = Field(default_factory=list, description="Consequences of this event")

class ActionItem(BaseModel):
    trigger_event: str = Field(description="The event causing this need")
    action: str = Field(description="Specific, detailed action to take. Mention specific items, locations, or protocols.")
    assigned_to: str = Field(description="Specific role or department responsible (e.g., 'Regional Logistics Manager', 'Store Operations Lead')")
    priority: Literal["Critical", "High", "Medium"] = Field(description="Urgency level")
    resource_needed: List[str] = Field(description="Resources required")

class ActionPlan(BaseModel):
    items: List[ActionItem]

class Alert(BaseModel):
    role: Literal["CEO", "Store Manager", "Logistics Head", "General"]
    subject: str
    body: str
    actionable_steps: List[str]

class CommunicationPackage(BaseModel):
    alerts: List[Alert]
    public_advisory: str = Field(description="Safety recommendations for the general public in the affected region")

# --- UI / Dashboard Models ---

class MapMarker(BaseModel):
    lat: float
    lon: float
    label: str
    type: Literal["Store", "Warehouse", "Vehicle", "Hazard"]
    status: Literal["Safe", "At Risk", "Critical"]

class KPIGauge(BaseModel):
    label: str
    value: float
    unit: str
    threshold: Literal["Normal", "Warning", "Critical"]

class DashboardPayload(BaseModel):
    map_center_lat: float
    map_center_lon: float
    map_zoom: int
    active_layers: List[str] = Field(description="Layers to enable e.g., 'Wildfire', 'Traffic', 'Fog'")
    markers: List[MapMarker]
    kpis: List[KPIGauge]
    news_ticker: List[str] = Field(description="Breaking news style headlines")
    risk_score: int = Field(description="0-100 overall risk score")
