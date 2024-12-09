"""Model serving module using NVIDIA Triton."""

import os
import time
from pathlib import Path
from typing import Dict, Optional, List, Any
import logging
from contextlib import asynccontextmanager

import tritonclient.http as triton_http
from fastapi import FastAPI, HTTPException, Security, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from pydantic import BaseModel, Field, validator
import uvicorn
from rich.console import Console
import numpy as np

from srt_model_quantizing.quantizer import ModelQuantizer, QuantizationConfig
from srt_model_quantizing.utils.helpers import setup_environment, get_gpu_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Enhanced metrics
INFERENCE_REQUESTS = Counter('inference_requests_total', 'Total number of inference requests', ['model_name', 'status'])
INFERENCE_LATENCY = Histogram('inference_latency_seconds', 'Inference request latency', ['model_name'])
MODEL_LOAD_TIME = Histogram('model_load_time_seconds', 'Time taken to load models', ['model_name'])
ACTIVE_REQUESTS = Gauge('active_requests', 'Number of active inference requests')
GPU_MEMORY_USAGE = Gauge('gpu_memory_usage_bytes', 'GPU memory usage in bytes', ['device'])
MODEL_MEMORY_USAGE = Gauge('model_memory_usage_bytes', 'Model memory usage in bytes', ['model_name'])

class InferenceRequest(BaseModel):
    """Inference request model."""
    model_name: str = Field(..., description="Name of the model to use for inference")
    inputs: Dict[str, List[float]] = Field(..., description="Input data for inference")
    batch_size: Optional[int] = Field(1, description="Batch size for inference")
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1:
            raise ValueError("Batch size must be greater than 0")
        return v
    
    @validator('inputs')
    def validate_inputs(cls, v):
        if not v:
            raise ValueError("Inputs cannot be empty")
        return v

class InferenceResponse(BaseModel):
    """Inference response model."""
    outputs: Dict[str, List[float]] = Field(..., description="Model outputs")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    model_name: str = Field(..., description="Name of the model used")
    timestamp: float = Field(default_factory=time.time, description="Timestamp of inference")

class ModelServer:
    """NVIDIA Triton model server wrapper with enhanced functionality."""
    
    def __init__(self, model_repository: Path):
        self.model_repository = model_repository
        self.client = triton_http.InferenceServerClient(
            url="localhost:8000",
            verbose=False,
            connection_timeout=5.0,
            network_timeout=60.0
        )
        self.loaded_models = set()
        self.model_configs = {}
        
    async def load_model(self, model_name: str) -> None:
        """Load a model into Triton server with enhanced error handling."""
        if model_name in self.loaded_models:
            return
            
        with MODEL_LOAD_TIME.labels(model_name=model_name).time():
            try:
                # Check if model exists in repository
                model_path = self.model_repository / model_name
                if not model_path.exists():
                    logger.error(f"Model not found: {model_name}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Model {model_name} not found in repository"
                    )
                
                # Load model configuration
                model_config = self.client.get_model_config(model_name)
                self.model_configs[model_name] = model_config
                
                # Load model into Triton
                self.client.load_model(model_name)
                self.loaded_models.add(model_name)
                
                # Update metrics
                model_size = sum(p.stat().st_size for p in model_path.rglob('*') if p.is_file())
                MODEL_MEMORY_USAGE.labels(model_name=model_name).set(model_size)
                
                logger.info(f"Successfully loaded model: {model_name}")
                console.log(f"[green]Loaded model: {model_name}")
                
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load model: {str(e)}"
                )
    
    async def infer(self, request: InferenceRequest) -> InferenceResponse:
        """Perform inference using Triton with enhanced monitoring and error handling."""
        ACTIVE_REQUESTS.inc()
        start_time = time.time()
        
        try:
            # Ensure model is loaded
            await self.load_model(request.model_name)
            
            # Prepare inputs with validation
            inputs = []
            for name, data in request.inputs.items():
                if not data:
                    raise ValueError(f"Empty input data for {name}")
                
                # Convert to numpy array with proper shape and type
                input_data = np.array(data, dtype=np.float32)
                if input_data.ndim == 1:
                    input_data = input_data.reshape(request.batch_size, -1)
                
                input_tensor = triton_http.InferInput(
                    name,
                    input_data.shape,
                    "FP32"
                )
                input_tensor.set_data_from_numpy(input_data)
                inputs.append(input_tensor)
            
            # Run inference with timeout
            result = await self.client.async_infer(
                request.model_name,
                inputs,
                request_id=str(time.time()),
                timeout=30.0
            )
            
            # Process outputs
            outputs = {}
            for output in result.as_numpy():
                outputs[output.name] = output.tolist()
            
            # Calculate latency
            latency = (time.time() - start_time) * 1000
            
            # Update metrics
            INFERENCE_REQUESTS.labels(
                model_name=request.model_name,
                status="success"
            ).inc()
            INFERENCE_LATENCY.labels(
                model_name=request.model_name
            ).observe(latency / 1000)  # Convert to seconds for histogram
            
            return InferenceResponse(
                outputs=outputs,
                latency_ms=latency,
                model_name=request.model_name
            )
            
        except Exception as e:
            # Update error metrics
            INFERENCE_REQUESTS.labels(
                model_name=request.model_name,
                status="error"
            ).inc()
            
            logger.error(f"Inference failed for {request.model_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference failed: {str(e)}"
            )
        finally:
            ACTIVE_REQUESTS.dec()

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="SRT Model Quantizing Server",
    description="High-performance model serving API using NVIDIA Triton",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "models:read": "Read model information",
        "models:infer": "Perform inference",
        "admin": "Administrative access"
    }
)

# Initialize server
model_server = None

@app.on_event("startup")
async def startup_event():
    """Initialize the model server on startup with enhanced monitoring."""
    global model_server
    
    try:
        # Setup environment
        setup_environment()
        
        # Start Prometheus metrics server
        start_http_server(8001)
        
        # Initialize model server
        model_repository = Path(os.getenv("MODEL_REPOSITORY", "./models"))
        model_server = ModelServer(model_repository)
        
        # Log GPU information and update metrics
        gpu_info = get_gpu_info()
        if gpu_info["available"]:
            console.log("[green]GPU(s) available for inference:")
            for device in gpu_info["devices"]:
                console.log(f"  - {device['name']} ({device['compute_capability']})")
                GPU_MEMORY_USAGE.labels(device=device['name']).set(device['memory_total'])
        else:
            console.log("[yellow]Warning: No GPUs available")
            
        logger.info("Server startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {str(e)}")
        raise

@app.post("/v2/models/{model_name}/infer",
          response_model=InferenceResponse,
          status_code=status.HTTP_200_OK,
          responses={
              404: {"description": "Model not found"},
              500: {"description": "Internal server error"}
          })
async def infer(
    model_name: str,
    request: InferenceRequest,
    security: SecurityScopes = Security(oauth2_scheme, scopes=["models:infer"])
) -> InferenceResponse:
    """Perform model inference with enhanced error handling and validation."""
    request.model_name = model_name
    return await model_server.infer(request)

@app.get("/v2/health/ready",
         response_model=Dict[str, Any],
         status_code=status.HTTP_200_OK)
async def health_ready() -> Dict[str, Any]:
    """Enhanced health check endpoint."""
    try:
        is_ready = model_server.client.is_server_ready()
        gpu_info = get_gpu_info()
        
        return {
            "status": "ready" if is_ready else "not_ready",
            "gpu_available": gpu_info["available"],
            "loaded_models": list(model_server.loaded_models),
            "active_requests": ACTIVE_REQUESTS._value.get(),
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )

def serve(host: str = "0.0.0.0", port: int = 8000, workers: int = 4):
    """Start the model server with configurable parameters."""
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers,
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise 