from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from modbus_manager import ModbusManager
import uvicorn
import os

app = FastAPI(title="CEAModbus API")

# Setup Modbus Manager
# Default for macOS might be something like /dev/tty.usbserial-XXX
# User should list /dev/tty.* to confirm
SERIAL_PORT = os.getenv("MODBUS_PORT", "/dev/tty.usbserial-10") 
modbus = ModbusManager(port=SERIAL_PORT)

class SpeedRequest(BaseModel):
    rpm: int

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
    if data:
        return data
    else:
        # Mocking for UI development if hardware not connected
        return {
            "set_speed": 0,
            "feedback_speed": 0,
            "is_enabled": False,
            "error": "Hardware not connected"
        }

@app.post("/api/speed")
async def set_speed(req: SpeedRequest):
    try:
        modbus.set_speed(req.rpm)
        return {"status": "ok", "speed": req.rpm}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/toggle")
async def toggle_motor(enabled: bool):
    try:
        modbus.set_enabled(enabled)
        return {"status": "ok", "enabled": enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Static files for the frontend
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
