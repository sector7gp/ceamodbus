import logging
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

class ModbusManager:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, slave_id=1):
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.client = ModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=1
        )
        
    def connect(self):
        return self.client.connect()
        
    def disconnect(self):
        self.client.close()
        
    def read_motor_status(self):
        """
        Reads essential motor registers.
        """
        try:
            # Registers according to documentation
            # 0x0056: Set speed (index 0)
            # 0x005F: Feedback speed (index 9, 0x5F-0x56=9)
            # 0x0066: Enable state (index 16, 0x66-0x56=16) 
            # We need to read at least 17 registers to reach 0x0066
            res = self.client.read_holding_registers(address=0x0056, count=17, slave=self.slave_id)
            if res.isError():
                return None
            
            data = {
                "set_speed": res.registers[0],          # 0x0056
                "feedback_speed": res.registers[9],     # 0x005F
                "is_enabled": res.registers[16] == 0,    # 0x0066: 0=Enabled, 1=Disabled
            }
            return data
        except ModbusException as e:
            logging.error(f"Modbus error: {e}")
            return None

    def set_speed(self, rpm):
        self.client.write_register(address=0x0056, value=rpm, slave=self.slave_id)

    def set_enabled(self, enabled=True):
        value = 0 if enabled else 1
        self.client.write_register(address=0x0066, value=value, slave=self.slave_id)
