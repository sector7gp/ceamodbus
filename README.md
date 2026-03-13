# CEAModbus - Motor Driver Interface

Este proyecto proporciona una interfaz web moderna para controlar y monitorear drivers de motores brushless (BLDC) mediante el protocolo Modbus RTU.

## 🚀 Características
- **Monitoreo en Tiempo Real**: Velocidad (RPM), estado de conexión y códigos de alarma.
- **Control Total**: Habilitación, freno, sentido de giro y rampa de aceleración.
- **Secuenciador**: Ciclo automático entre dos velocidades con intervalos configurables.
- **Gestión de Memoria**: Guardar configuraciones en el driver o restaurar valores de fábrica.

---

## 🛠 Documentación de Registros Modbus

El driver utiliza el protocolo **Modbus RTU (9600, 8, N, 1)** con Function Codes `0x03` (Read) y `0x06` (Write).

### Registros de Lectura (Holding Registers - 03)

| Dirección | Descripción | Rango / Significado |
| :--- | :--- | :--- |
| `0x0056` | Velocidad de Seteo | 0 - 60000 RPM |
| `0x005F` | Velocidad de Feedback | RPM actuales del motor |
| `0x0066` | Estado de Habilitación | 0: Habilitado, 1: Deshabilitado |
| `0x006A` | Estado de Freno | 0: Freno Activo, 1: Sin Freno |
| `0x006D` | Sentido de Giro | 1: Forward, 0: Reverse |
| `0x0076` | Código de Alarma | 0: OK, >0: Código de error |
| `0x0086` | Pares de Polos | Configuración de polos del motor |
| `0x008A` | Tiempo Acc/Dec | 0 - 15 segundos |
| `0x0092` | Velocidad Máx (Analógica) | 0 - 60000 RPM |
| `0x00B6` | Estado de Comunicación | 1: R/W habilitado, 0: Solo lectura |
| `0x00BB` | Versión del Driver | Firmware version code |

### Registros de Escritura (Single Register - 06)

| Dirección | Función | Valor / Lógica |
| :--- | :--- | :--- |
| `0x0040` | Retorno de Datos | 0: Retorna datos, 1: Solo ejecuta |
| `0x0056` | Set Speed | 0 - 60000 (RPM) |
| `0x0066` | Enable Control | 0: Habilitar, 1: Deshabilitar |
| `0x006A` | Brake Control | 0: Frenar, 1: Soltar freno |
| `0x006D` | Direction Control | 1: Forward, 0: Reverse |
| `0x0076` | Alarm Reset | Escribir 0 para resetear alarmas activas |
| `0x0086` | Set Pole Pairs | Configura pares de polos |
| `0x008A` | Set Acc/Dec Time | 0 - 15 (Segundos) |
| `0x0092` | Set Max Speed | Límite para control analógico |
| `0x00B6` | RS-485 Control | 1: Habilitar R/W, 0: Solo R |
| `0x00BC` | Save Parameters | Escribir 1 para guardar en memoria no volátil |
| `0x00CC` | Factory Reset | Escribir 1 para restaurar valores por defecto |

---

## 💻 Instalación y Uso

### 1. Requisitos
- Python 3.9+
- Adaptador USB a RS485 conectado.

### 2. Configuración
Instala las dependencias:
```bash
pip install -r requirements.txt
```

### 3. Ejecución
Inicia el servidor backend:
```bash
python app.py
```
Accede a la interfaz en tu navegador: [http://localhost:8000](http://localhost:8000)

---

## 🔧 Architectura del Proyecto
- `app.py`: Servidor FastAPI y lógica de la API / Secuenciador.
- `modbus_manager.py`: Abstracción de la comunicación serie Modbus.
- `static/`: Frontend (HTML5, CSS3, JavaScript).

---

> [!IMPORTANT]
> Asegúrate de configurar el puerto serie correcto en `app.py` o mediante la variable de entorno `MODBUS_PORT`. Por defecto usa `/dev/tty.usbmodem593A0392311`.
