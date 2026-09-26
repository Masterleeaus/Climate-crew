from .base import BaseDataSource
from .openaq import OpenAQClient, WAQIClient
from .usgs_earthquake import USGSEarthquakeClient
from .nasa_firms import NASAFIRMSClient
from .global_forest_watch import GlobalForestWatchClient
from .open_meteo import OpenMeteoClient
from .copernicus import CopernicusMarineClient, CopernicusSentinelClient
from .noaa_ocean import NOAAOceanClient, CoralReefWatchClient, OpenMeteoMarineClient
from .gbif import GBIFClient
from .climate_trace import ClimateTraceClient

# Climate-Finance Data Sources (REAL APIs)
from .yahoo_finance import YahooFinanceClient
from .esg_data import FinnhubClient, AlphaVantageClient, ESGDataClient
from .regulatory_data import CarbonPricingClient, RegulatoryDataClient

# Disaster Management Data Sources
from .disaster_alerts import DisasterAlertsClient
from .evacuation_routing import EvacuationRouter

__all__ = [
    "BaseDataSource",
    "OpenAQClient",
    "WAQIClient",
    "USGSEarthquakeClient",
    "NASAFIRMSClient",
    "GlobalForestWatchClient",
    "OpenMeteoClient",
    "CopernicusMarineClient",
    "CopernicusSentinelClient",
    "NOAAOceanClient",
    "CoralReefWatchClient",
    "OpenMeteoMarineClient",
    "GBIFClient",
    "ClimateTraceClient",
    # Climate-Finance
    "YahooFinanceClient",
    "FinnhubClient",
    "AlphaVantageClient",
    "ESGDataClient",
    "CarbonPricingClient",
    "RegulatoryDataClient",
    # Disaster Management
    "DisasterAlertsClient",
    "EvacuationRouter",
]
