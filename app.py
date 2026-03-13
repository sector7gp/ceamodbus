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
    interval: int

class AccTimeRequest(BaseModel):
    seconds: int

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
            modbus.set_speed(target_rpm)
            print(f"Sequencer: Sent speed {target_rpm} (Target {sequencer.current_target})")
            
            # Switch for next time
            sequencer.current_target = "B" if sequencer.current_target == "A" else "A"
            
            await asyncio.sleep(sequencer.interval)
        except Exception as e:
            print(f"Sequencer error: {e}")
            await asyncio.sleep(1)

@app.post("/api/sequencer/start")
async def start_sequencer(req: SequencerRequest):
    if sequencer.active:
        return {"status": "already_running"}
    
    sequencer.speed_a = req.speed_a
    sequencer.speed_b = req.speed_b
    sequencer.interval = max(1, req.interval)
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
    modbus.set_speed(req.rpm)
    return {"status": "ok"}

@app.post("/api/toggle")
async def toggle_motor(enabled: bool):
    modbus.set_enabled(enabled)
    return {"status": "ok"}

@app.post("/api/brake")
async def toggle_brake(braked: bool):
    modbus.set_brake(braked)
    return {"status": "ok"}

@app.post("/api/direction")
async def set_direction(forward: bool):
    modbus.set_direction(forward)
    return {"status": "ok"}

@app.post("/api/reset_alarm")
async def reset_alarm():
    modbus.reset_alarm()
    return {"status": "ok"}

@app.post("/api/acc_time")
async def set_acc_time(req: AccTimeRequest):
    modbus.set_acc_time(req.seconds)
    return {"status": "ok"}

@app.post("/api/pole_pairs")
async def set_pole_pairs(count: int):
    modbus.set_pole_pairs(count)
    return {"status": "ok"}

@app.post("/api/max_speed")
async def set_max_speed(rpm: int):
    modbus.set_max_speed(rpm)
    return {"status": "ok"}

@app.post("/api/rs485_control")
async def set_rs485_control(enabled: bool):
    modbus.set_rs485_control(enabled)
    return {"status": "ok"}

@app.post("/api/return_data")
async def set_return_data(enabled: bool):
    modbus.set_return_data(enabled)
    return {"status": "ok"}

@app.post("/api/save")
async def save_params():
    modbus.save_parameters()
    return {"status": "ok"}

@app.post("/api/restore")
async def restore_factory():
    modbus.restore_factory_settings()
    return {"status": "ok"}

# Static files for the frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
