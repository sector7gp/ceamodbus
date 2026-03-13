import customtkinter as ctk
from modbus_manager import ModbusManager
import threading
import time

class CEAModbusApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CEAModbus - Motor Brushless Control")
        self.geometry("800x600")
        
        # Modern UI Styling
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.modbus = ModbusManager()

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar for connections
        self.sidebar = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="CEA Modbus", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.conn_status = ctk.CTkLabel(self.sidebar, text="Desconectado", text_color="red")
        self.conn_status.grid(row=1, column=0, padx=20, pady=10)

        self.connect_btn = ctk.CTkButton(self.sidebar, text="Conectar", command=self.toggle_connection)
        self.connect_btn.grid(row=2, column=0, padx=20, pady=10)

        # Main Dashboard
        self.dashboard = ctk.CTkFrame(self)
        self.dashboard.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Speed Display
        self.speed_label = ctk.CTkLabel(self.dashboard, text="Velocidad Feedback", font=ctk.CTkFont(size=16))
        self.speed_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.speed_value = ctk.CTkLabel(self.dashboard, text="0 RPM", font=ctk.CTkFont(size=40, weight="bold"))
        self.speed_value.grid(row=1, column=0, padx=20, pady=10)

        # Controls
        self.ctrl_frame = ctk.CTkFrame(self.dashboard)
        self.ctrl_frame.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        
        self.enable_switch = ctk.CTkSwitch(self.ctrl_frame, text="Habilitar Motor", command=self.update_motor_state)
        self.enable_switch.grid(row=0, column=0, padx=20, pady=10)

        self.speed_input = ctk.CTkEntry(self.ctrl_frame, placeholder_text="Set Speed (RPM)")
        self.speed_input.grid(row=1, column=0, padx=20, pady=10)
        
        self.set_speed_btn = ctk.CTkButton(self.ctrl_frame, text="Setear Velocidad", command=self.update_speed)
        self.set_speed_btn.grid(row=1, column=1, padx=20, pady=10)

        self.running = False

    def toggle_connection(self):
        if not self.running:
            if self.modbus.connect():
                self.conn_status.configure(text="Conectado", text_color="green")
                self.connect_btn.configure(text="Desconectar")
                self.running = True
                threading.Thread(target=self.poll_data, daemon=True).start()
        else:
            self.running = False
            self.modbus.disconnect()
            self.conn_status.configure(text="Desconectado", text_color="red")
            self.connect_btn.configure(text="Conectar")

    def poll_data(self):
        while self.running:
            data = self.modbus.read_motor_status()
            if data:
                self.speed_value.configure(text=f"{data['feedback_speed']} RPM")
            time.sleep(1)

    def update_motor_state(self):
        enabled = self.enable_switch.get()
        self.modbus.set_enabled(enabled)

    def update_speed(self):
        try:
            rpm = int(self.speed_input.get())
            self.modbus.set_speed(rpm)
        except ValueError:
            pass

if __name__ == "__main__":
    app = CEAModbusApp()
    app.mainloop()
