from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from modbus_manager import ModbusManager
import uvicorn
import os

app = FastAPI(title="CEAModbus API")

# Setup Modbus Manager
SERIAL_PORT = os.getenv("MODBUS_PORT", "/dev/tty.usbmodem593A0392311") 
modbus = ModbusManager(port=SERIAL_PORT)

class SpeedRequest(BaseModel):
    rpm: int

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
    # If not connected or read failure, read_motor_status returns a dict with default values and connected=False
    return data

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
