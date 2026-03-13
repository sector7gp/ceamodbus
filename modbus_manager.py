import logging
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException

class ModbusManager:
    def __init__(self, port='/dev/tty.usbmodem593A0392311', baudrate=9600, slave_id=1):
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
        
    def _ensure_connected(self):
        if not self.client.connected:
            logging.info("Attempting to reconnect Modbus...")
            return self.client.connect()
        return True

    def _read_safe(self, address, count):
        if not self._ensure_connected():
            return None
        try:
            res = self.client.read_holding_registers(address=address, count=count, slave=self.slave_id)
            if res.isError():
                # Check for specific Modbus Exception (like 0x86)
                error_msg = f"Modbus Error: {res}"
                if hasattr(res, 'exception_code') and res.exception_code == 0x02:
                    error_msg = "Error: 485 Control Disabled or Invalid Address"
                logging.error(f"Read error at {hex(address)}: {error_msg}")
                # If it's a connection error, close so it reconnects next time
                if "No response received" in str(res) or "Connection" in str(res):
                    self.client.close()
                return None
            if not hasattr(res, 'registers') or not res.registers:
                return None
            return res.registers
        except Exception as e:
            logging.error(f"Read error at {hex(address)}: {e}")
            if "Device not configured" in str(e):
                self.client.close()
            return None

    def _write_safe(self, address, value):
        if not self._ensure_connected():
            return False, "Serial port disconnected"
        try:
            res = self.client.write_register(address=address, value=value, slave=self.slave_id)
            if res.isError():
                if hasattr(res, 'exception_code') and res.exception_code == 0x02:
                    return False, "485 Control Disabled. Check register 0xB6."
                # Close connection on IO errors to force reconnect
                self.client.close()
                return False, f"Modbus Error: {res}"
            return True, "OK"
        except Exception as e:
            self.client.close()
            return False, str(e)

    def read_motor_status(self):
        """
        Reads all documented registers.
        """
        status = {
            "set_speed": 0,
            "feedback_speed": 0,
            "is_enabled": False,
            "is_braked": False,
            "is_forward": True,
            "alarm_code": 0,
            "pole_pairs": 0,
            "acc_time": 0,
            "max_analogue_speed": 0,
            "rs485_status": 0,
            "version": "N/A",
            "connected": False,
            "last_error": None
        }

        # Block 1: Velocities (0x56 to 0x5F)
        regs1 = self._read_safe(0x0056, 1)
        if regs1 is not None:
            status["set_speed"] = regs1[0]
            status["connected"] = True
            
            regs_fb = self._read_safe(0x005F, 1)
            if regs_fb:
                status["feedback_speed"] = regs_fb[0]

        # Block 2: Logic states
        # Habilitar (0x66), Freno (0x6A), Sentido (0x6D)
        r_en = self._read_safe(0x0066, 1)
        if r_en is not None: 
            # Reverted: 0=Enable, 1=Disable (User says inverted)
            status["is_enabled"] = r_en[0] == 0
        
        r_brk = self._read_safe(0x006A, 1)
        if r_brk is not None: 
            # Reverted: 0=Brake Active, 1=No Brake
            status["is_braked"] = r_brk[0] == 0
        
        r_dir = self._read_safe(0x006D, 1)
        if r_dir is not None:
            # 1: Forward, 0: Reverse (per doc)
            status["is_forward"] = r_dir[0] == 1

        # Block 3: Alarm (0x76)
        regs3 = self._read_safe(0x0076, 1)
        if regs3 is not None: status["alarm_code"] = regs3[0]

        # Block 4: Config
        r_pole = self._read_safe(0x0086, 1)
        if r_pole is not None: status["pole_pairs"] = r_pole[0]
        
        r_acc = self._read_safe(0x008A, 1)
        if r_acc is not None:
            status["acc_time"] = r_acc[0] / 10.0

        # Block 5: Max analogue speed (0x92)
        regs5 = self._read_safe(0x0092, 1)
        if regs5 is not None: status["max_analogue_speed"] = regs5[0]

        # Block 6: Connection & Version (0xB6, 0xBB)
        r_485 = self._read_safe(0x00B6, 1)
        if r_485 is not None: status["rs485_status"] = r_485[0]
        
        r_ver = self._read_safe(0x00BB, 1)
        if r_ver is not None: status["version"] = r_ver[0]

        return status

    def set_speed(self, rpm):
        return self._write_safe(address=0x0056, value=rpm)

    def set_enabled(self, enabled=True):
        return self._write_safe(address=0x0066, value=0 if enabled else 1)

    def set_brake(self, braked=True):
        return self._write_safe(address=0x006A, value=0 if braked else 1)

    def set_direction(self, forward=True):
        return self._write_safe(address=0x006D, value=1 if forward else 0)

    def reset_alarm(self):
        return self._write_safe(address=0x0076, value=0)

    def set_acc_time(self, seconds):
        # Convert seconds to 0.1s units (e.g. 9.5s -> 95)
        raw_val = int(seconds * 10)
        return self._write_safe(address=0x008A, value=raw_val)

    def set_pole_pairs(self, count):
        return self._write_safe(address=0x0086, value=count)

    def set_max_speed(self, rpm):
        return self._write_safe(address=0x0092, value=rpm)

    def set_rs485_control(self, enabled=True):
        return self._write_safe(address=0x00B6, value=1 if enabled else 0)

    def set_return_data(self, enabled=True):
        return self._write_safe(address=0x0040, value=0 if enabled else 1)

    def save_parameters(self):
        return self._write_safe(address=0x00BC, value=1)

    def restore_factory_settings(self):
        return self._write_safe(address=0x00CC, value=1)
