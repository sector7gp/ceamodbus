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
        
    def _read_safe(self, address, count):
        try:
            res = self.client.read_holding_registers(address=address, count=count, slave=self.slave_id)
            if res.isError() or not hasattr(res, 'registers') or not res.registers:
                return None
            return res.registers
        except Exception as e:
            logging.error(f"Read error at {hex(address)}: {e}")
            return None

    def read_motor_status(self):
        """
        Reads all documented registers in logical blocks.
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
            "connected": False
        }

        # Block 1: Velocities (0x56 to 0x5F)
        regs = self._read_safe(0x0056, 10)
        if regs:
            status["set_speed"] = regs[0]
            status["feedback_speed"] = regs[9]
            status["connected"] = True

        # Block 2: Logic states (0x66 to 0x6D)
        regs = self._read_safe(0x0066, 8)
        if regs:
            status["is_enabled"] = regs[0] == 0   # 0=Enable, 1=Disable
            status["is_braked"] = regs[4] == 0    # 0=Brake, 1=No Brake
            status["is_forward"] = regs[7] == 1   # 1=Forward, 0=Backwards

        # Block 3: Alarm (0x76)
        regs = self._read_safe(0x0076, 1)
        if regs:
            status["alarm_code"] = regs[0]

        # Block 4: Config (0x86 to 0x8A)
        regs = self._read_safe(0x0086, 5)
        if regs:
            status["pole_pairs"] = regs[0]
            status["acc_time"] = regs[4]

        # Block 5: Max speed (0x92)
        regs = self._read_safe(0x0092, 1)
        if regs:
            status["max_analogue_speed"] = regs[0]

        # Block 6: Connection & Version
        regs = self._read_safe(0x00B6, 6)
        if regs:
            status["rs485_status"] = regs[0]
            status["version"] = regs[5]

        return status

    def set_speed(self, rpm):
        self.client.write_register(address=0x0056, value=rpm, slave=self.slave_id)

    def set_enabled(self, enabled=True):
        self.client.write_register(address=0x0066, value=0 if enabled else 1, slave=self.slave_id)

    def set_brake(self, braked=True):
        self.client.write_register(address=0x006A, value=0 if braked else 1, slave=self.slave_id)

    def set_direction(self, forward=True):
        self.client.write_register(address=0x006D, value=1 if forward else 0, slave=self.slave_id)

    def reset_alarm(self):
        # Writing 0 to 0x0076 resets the alarm
        self.client.write_register(address=0x0076, value=0, slave=self.slave_id)

    def set_acc_time(self, seconds):
        self.client.write_register(address=0x008A, value=seconds, slave=self.slave_id)
