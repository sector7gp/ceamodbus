from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from modbus_manager import ModbusManager
import uvicorn
import os

app = FastAPI(title="CEAModbus API")

import asyncio
from typing import Optional

app = FastAPI(title="CEAModbus API")

# Setup Modbus Manager
SERIAL_PORT = os.getenv("MODBUS_PORT", "/dev/tty.usbmodem593A0392311") 
modbus = ModbusManager(port=SERIAL_PORT)

# Sequencer State
class Sequencer:
    def __init__(self):
        self.active = False
        self.speed_a = 1000
        self.speed_b = 3000
        self.interval = 5
        self.current_target = "A"
        self.task: Optional[asyncio.Task] = None

sequencer = Sequencer()

class SpeedRequest(BaseModel):
    rpm: int

class SequencerRequest(BaseModel):
    speed_a: int
    speed_b: int
    interval: float

class AccTimeRequest(BaseModel):
    seconds: float

@app.on_event("startup")
def startup_event():
    connected = modbus.connect()
    if not connected:
        print(f"Warning: Could not connect to {SERIAL_PORT}")

@app.on_event("shutdown")
def shutdown_event():
    modbus.disconnect()

@app.get("/api/status")
async def get_status():
    data = modbus.read_motor_status()
    # Add sequencer info to status
    data["sequencer"] = {
        "active": sequencer.active,
        "current_target": sequencer.current_target,
        "speed_a": sequencer.speed_a,
        "speed_b": sequencer.speed_b,
        "interval": sequencer.interval
    }
    return data

# --- Sequencer Logic ---

async def sequencer_loop():
    while sequencer.active:
        try:
            target_rpm = sequencer.speed_a if sequencer.current_target == "A" else sequencer.speed_b
            success, msg = modbus.set_speed(target_rpm)
            if not success:
                print(f"Sequencer warning: {msg}")
            
            # Switch for next time
            sequencer.current_target = "B" if sequencer.current_target == "A" else "A"
            
            # Use a smaller sleep chunk to remain responsive to cancelation
            sleep_time = sequencer.interval
            await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Sequencer error: {e}")
            await asyncio.sleep(0.5)

@app.post("/api/sequencer/start")
async def start_sequencer(req: SequencerRequest):
    if sequencer.active:
        await stop_sequencer() # Restart if already running
    
    sequencer.speed_a = req.speed_a
    sequencer.speed_b = req.speed_b
    sequencer.interval = max(0.1, req.interval) # Allow 100ms cycle
    sequencer.active = True
    sequencer.current_target = "A"
    sequencer.task = asyncio.create_task(sequencer_loop())
    return {"status": "started"}

@app.post("/api/sequencer/stop")
async def stop_sequencer():
    sequencer.active = False
    if sequencer.task:
        sequencer.task.cancel()
    return {"status": "stopped"}

@app.post("/api/speed")
async def set_speed(req: SpeedRequest):
    success, msg = modbus.set_speed(req.rpm)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/toggle")
async def toggle_motor(enabled: bool):
    success, msg = modbus.set_enabled(enabled)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/brake")
async def toggle_brake(braked: bool):
    success, msg = modbus.set_brake(braked)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/direction")
async def set_direction(forward: bool):
    success, msg = modbus.set_direction(forward)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/reset_alarm")
async def reset_alarm():
    success, msg = modbus.reset_alarm()
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/acc_time")
async def set_acc_time(req: AccTimeRequest):
    success, msg = modbus.set_acc_time(req.seconds)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/pole_pairs")
async def set_pole_pairs(count: int):
    success, msg = modbus.set_pole_pairs(count)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/max_speed")
async def set_max_speed(rpm: int):
    success, msg = modbus.set_max_speed(rpm)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/rs485_control")
async def set_rs485_control(enabled: bool):
    success, msg = modbus.set_rs485_control(enabled)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/return_data")
async def set_return_data(enabled: bool):
    success, msg = modbus.set_return_data(enabled)
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/save")
async def save_params():
    success, msg = modbus.save_parameters()
    return {"status": "ok" if success else "error", "message": msg}

@app.post("/api/restore")
async def restore_factory():
    success, msg = modbus.restore_factory_settings()
    return {"status": "ok" if success else "error", "message": msg}

# Static files for the frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
