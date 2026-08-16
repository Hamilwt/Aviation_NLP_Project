"""FastAPI application for Safety NLP Pipeline."""
import logging
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from schemas import (
    ClassifyRequest, ClassifyResponse, AnalyzeRequest, DataAssistantResponse,
    DatasetStats, ModelPerformanceResponse, AlertsResponse,
    SystemControlResponse, ServiceStatus, PipelineRunRequest, PipelineRunResponse,
    HealthResponse, MonitorControlRequest
)
from ml_service import ml_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Process management
class ProcessManager:
    SERVICES = {
        "pipeline": {
            "cmd": [sys.executable, "main.py"],
            "label": "Pipeline",
            "desc": "Full pipeline: fetch → preprocess → train → evaluate → RAG → report",
        },
        "monitor": {
            "cmd": [sys.executable, "-m", "src.monitor"],
            "label": "Monitor",
            "desc": "Real-time incident ingestion, classification, risk scoring & alerting",
        },
    }
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.log_buffers: Dict[str, List[str]] = {name: [] for name in self.SERVICES}
        self.log_threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()
    
    def _read_stream(self, stream, service_name: str):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    with self.lock:
                        self.log_buffers[service_name].append(f"[{service_name}] {line.rstrip()}")
                        # Keep buffer bounded
                        if len(self.log_buffers[service_name]) > 500:
                            self.log_buffers[service_name] = self.log_buffers[service_name][-500:]
        except Exception:
            pass
        finally:
            stream.close()
    
    def start(self, service_name: str) -> tuple[bool, str]:
        with self.lock:
            if service_name in self.processes and self.processes[service_name].poll() is None:
                return False, f"{service_name} already running"
            
            svc = self.SERVICES[service_name]
            cwd = settings.BASE_DIR
            
            try:
                proc = subprocess.Popen(
                    svc["cmd"],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception as e:
                return False, f"Failed to start {service_name}: {e}"
            
            self.processes[service_name] = proc
            
            # Start log reader thread
            t = threading.Thread(
                target=self._read_stream,
                args=(proc.stdout, service_name),
                daemon=True,
            )
            t.start()
            self.log_threads[service_name] = t
            
            return True, f"{svc['label']} started (PID: {proc.pid})"
    
    def stop(self, service_name: str) -> tuple[bool, str]:
        with self.lock:
            if service_name not in self.processes:
                return False, f"{service_name} not running"
            
            proc = self.processes[service_name]
            if proc.poll() is not None:
                self._cleanup(service_name)
                return True, f"{service_name} was already stopped"
            
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            except Exception as e:
                return False, f"Error stopping {service_name}: {e}"
            finally:
                self._cleanup(service_name)
            
            return True, f"{self.SERVICES[service_name]['label']} stopped"
    
    def _cleanup(self, service_name: str):
        self.processes.pop(service_name, None)
        self.log_threads.pop(service_name, None)
    
    def is_running(self, service_name: str) -> bool:
        with self.lock:
            proc = self.processes.get(service_name)
            return proc is not None and proc.poll() is None
    
    def get_logs(self, service_name: str) -> List[str]:
        with self.lock:
            return self.log_buffers.get(service_name, [])[:]
    
    def get_all_status(self) -> Dict[str, bool]:
        return {name: self.is_running(name) for name in self.SERVICES}
    
    def stop_all(self):
        for name in list(self.processes.keys()):
            self.stop(name)


proc_mgr = ProcessManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Safety NLP API...")
    # Load ML artifacts in background
    import threading
    load_thread = threading.Thread(target=ml_service.load_artifacts, daemon=True)
    load_thread.start()
    yield
    # Shutdown
    logger.info("Shutting down...")
    proc_mgr.stop_all()


app = FastAPI(
    title="Safety NLP Pipeline API",
    description="Aviation & Power-Grid Incident Analysis API with TF-IDF + SGD + RAG Explainability",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for plots
if settings.PLOTS_DIR.exists():
    app.mount("/api/plots", StaticFiles(directory=settings.PLOTS_DIR), name="plots")


# Health check
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if ml_service.is_ready() else "loading",
        version="2.0.0",
        model_loaded=ml_service._model is not None,
        data_loaded=ml_service._df is not None,
    )


# Dataset Overview
@app.get("/api/overview", response_model=DatasetStats)
async def get_overview():
    if not ml_service.is_ready():
        raise HTTPException(status_code=503, detail="ML artifacts not loaded yet")
    stats = ml_service.get_dataset_stats()
    return DatasetStats(**stats)


# Model Performance
@app.get("/api/model-performance", response_model=ModelPerformanceResponse)
async def get_model_performance():
    if not ml_service.is_ready():
        raise HTTPException(status_code=503, detail="ML artifacts not loaded yet")
    perf = ml_service.get_model_performance()
    if not perf:
        raise HTTPException(status_code=404, detail="Performance data not available. Run pipeline first.")
    return ModelPerformanceResponse(**perf)


# RAG Explorer - Classify with evidence
@app.post("/api/classify", response_model=ClassifyResponse)
async def classify_incident(request: ClassifyRequest):
    if not ml_service.is_ready():
        raise HTTPException(status_code=503, detail="ML artifacts not loaded yet")
    
    try:
        predicted, evidence, processing_time = ml_service.classify_with_evidence(
            request.narrative, request.top_k
        )
        return ClassifyResponse(
            predicted_label=predicted,
            evidence=evidence,
            processing_time_ms=processing_time
        )
    except Exception as e:
        logger.error("Classification failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Data Assistant
@app.post("/api/analyze", response_model=DataAssistantResponse)
async def analyze_data(request: AnalyzeRequest):
    if not ml_service.is_ready():
        raise HTTPException(status_code=503, detail="ML artifacts not loaded yet")
    
    lines = ml_service.analyze_data(request.query)
    return DataAssistantResponse(lines=lines)


# Live Alerts
@app.get("/api/alerts", response_model=AlertsResponse)
async def get_alerts(limit: int = 50):
    data = ml_service.get_alerts(limit)
    return AlertsResponse(**data)


# System Control
@app.get("/api/system/status", response_model=SystemControlResponse)
async def get_system_status():
    status = proc_mgr.get_all_status()
    services = []
    for name, info in ProcessManager.SERVICES.items():
        running = status[name]
        pid = None
        if running and name in proc_mgr.processes:
            pid = proc_mgr.processes[name].pid
        services.append(ServiceStatus(
            name=name,
            label=info["label"],
            description=info["desc"],
            running=running,
            pid=pid
        ))
    
    logs = {}
    for name in ProcessManager.SERVICES:
        logs[name] = proc_mgr.get_logs(name)
    
    return SystemControlResponse(services=services, logs=logs)


@app.post("/api/system/control/{service_name}")
async def control_service(service_name: str, action: str):
    if service_name not in ProcessManager.SERVICES:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_name}")
    
    if action == "start":
        ok, msg = proc_mgr.start(service_name)
    elif action == "stop":
        ok, msg = proc_mgr.stop(service_name)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    
    return {"success": ok, "message": msg}


@app.post("/api/system/control/all/{action}")
async def control_all_services(action: str):
    if action == "start":
        for name in ProcessManager.SERVICES:
            if not proc_mgr.is_running(name):
                proc_mgr.start(name)
        return {"success": True, "message": "All services started"}
    elif action == "stop":
        proc_mgr.stop_all()
        return {"success": True, "message": "All services stopped"}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")


# Pipeline execution
@app.post("/api/pipeline/run", response_model=PipelineRunResponse)
async def run_pipeline(request: PipelineRunRequest, background_tasks: BackgroundTasks):
    def run_pipeline_task():
        import time
        start = time.perf_counter()
        try:
            cmd = [sys.executable, "main.py"]
            if request.force_refresh:
                cmd.append("--force-refresh")
            if request.no_fetch:
                cmd.append("--no-fetch")
            if request.no_rag:
                cmd.append("--no-rag")
            cmd.extend(["--samples", str(request.samples)])
            
            result = subprocess.run(
                cmd,
                cwd=settings.BASE_DIR,
                capture_output=True,
                text=True,
                timeout=3600,
            )
            
            duration = time.perf_counter() - start
            if result.returncode == 0:
                # Reload artifacts after successful run
                ml_service.load_artifacts()
                return {"success": True, "message": "Pipeline completed successfully", "duration": duration}
            else:
                return {"success": False, "message": result.stderr, "duration": duration}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Pipeline timed out after 1 hour", "duration": time.perf_counter() - start}
        except Exception as e:
            return {"success": False, "message": str(e), "duration": time.perf_counter() - start}
    
    # Run in background
    result = run_pipeline_task()
    return PipelineRunResponse(
        success=result["success"],
        message=result["message"],
        duration_seconds=result.get("duration"),
    )


# Monitor control
@app.post("/api/monitor/control")
async def control_monitor(request: MonitorControlRequest):
    # This would control the monitor process
    # For now, return status
    return {"message": f"Monitor {request.action} requested", "poll_seconds": request.poll_seconds}


# WebSocket for real-time logs
@app.websocket("/api/ws/logs/{service_name}")
async def websocket_logs(websocket: WebSocket, service_name: str):
    await websocket.accept()
    try:
        while True:
            logs = proc_mgr.get_logs(service_name)
            await websocket.send_json({"logs": logs[-50:]})  # Send last 50 lines
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error: %s", e)


# Need to import asyncio
import asyncio


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=True,
    )