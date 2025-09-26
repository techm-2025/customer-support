import os
import time 
from datetime import datetime 
from typing import Dict, Optional

def initialize_observability(service_name):
    """Initialize observability with proper configuration for services"""
    try:
        from ioa_observe.sdk.logging.logging import LoggerWrapper
        from ioa_observe.sdk.metrics.metrics import MetricsWrapper
        from ioa_observe.sdk.tracing.tracing import TracerWrapper
        from ioa_observe.sdk import Observe
        
        service_name = service_name
        api_endpoint = os.getenv("OTLP_HTTP_ENDPOINT", "http://localhost:4318")
        
        print(f"OBSERVE_INIT: Initializing observability for service: {service_name}")
        
        Observe.init(service_name, api_endpoint=api_endpoint)
        
        TracerWrapper.set_static_params(
            resource_attributes={
                "service.name": service_name,
                "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "system.type": "Agent"
            },
            enable_content_tracing=True,
            endpoint=api_endpoint,
            headers={}
        )

        LoggerWrapper.set_static_params(
            resource_attributes={
                "service.name": service_name,
                "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            endpoint=api_endpoint,
            headers={}
        )
    
        metrics_endpoint = api_endpoint.replace('4318','4317') if "4318" in api_endpoint else api_endpoint  
        MetricsWrapper.set_static_params(
            resource_attributes={
                "service.name": service_name,
                "service.version": os.getenv("SERVICE_VERSION", "1.0.0")
            },
            endpoint=metrics_endpoint,
            headers={}
        )

        MetricsWrapper()
        
        TracerWrapper()

        LoggerWrapper()
        
        # Verify initialization
        if not TracerWrapper.verify_initialized():
            raise Exception("TracerWrapper failed to initialize")
        return True
    except Exception as e:
        print(f"OBSERVE_INIT: Error initializing observability: {e}")
        return False