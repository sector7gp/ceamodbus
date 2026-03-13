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
        # Note: 0x5F is relative index 9 from 0x56
        regs1 = self._read_safe(0x0056, 10)
        if regs1:
            status["set_speed"] = regs1[0]           # 0x0056
            status["feedback_speed"] = regs1[9]      # 0x005F
            status["connected"] = True

        # Block 2: Logic states (0x66 to 0x6D)
        # 0x66: Enable (idx 0)
        # 0x6A: Brake (idx 4)
        # 0x6D: Direction (idx 7)
        regs2 = self._read_safe(0x0066, 8)
        if regs2:
            status["is_enabled"] = regs2[0] == 0    # 0=Enable, 1=Disable
            status["is_braked"] = regs2[4] == 0     # 0=Brake, 1=No Brake
            # Manual description: "1 it's spinning forward, if it's 0 it's spinning backwards"
            status["is_forward"] = regs2[7] == 1    # 0x6D

        # Block 3: Alarm (0x76)
        regs3 = self._read_safe(0x0076, 1)
        if regs3:
            status["alarm_code"] = regs3[0]

        # Block 4: Config (0x86 to 0x8A)
        # 0x86: Polar logarithm (idx 0)
        # 0x8A: Acc/Dec time (idx 4)
        regs4 = self._read_safe(0x0086, 5)
        if regs4:
            status["pole_pairs"] = regs4[0]         # 0x0086
            status["acc_time"] = regs4[4]           # 0x008A

        # Block 5: Max analogue speed (0x92)
        regs5 = self._read_safe(0x0092, 1)
        if regs5:
            # Note: Max value range 0-60000
            status["max_analogue_speed"] = regs5[0]

        # Block 6: Connection & Version (0xB6, 0xBB)
        # 0xB6: RS485 status
        # 0xBB: Program version
        # 0xBB - 0xB6 = 5. Read 6 registers.
        regs6 = self._read_safe(0x00B6, 6)
        if regs6:
            status["rs485_status"] = regs6[0]       # 0xB6
            status["version"] = regs6[5]            # 0xBB

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
