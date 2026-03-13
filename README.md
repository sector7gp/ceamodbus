# CEAModbus

Control de drivers de motores Brushless (BLDC) mediante el protocolo Modbus RTU.

## Descripción

CEAModbus es una aplicación de escritorio multiplataforma escrita en Python diseñada para interactuar con controladores de motores brushless a través de una interfaz USB-RS485. Permite el monitoreo en tiempo real de los parámetros del motor y el control de operación.

## Características

- **Monitoreo en Tiempo Real**: Visualización de velocidad de seteo y velocidad de feedback (RPM).
- **Control de Operación**: Habilitar/Deshabilitar motor, control de freno y dirección de giro.
- **Configuración de Parámetros**: Ajuste de rampa de aceleración/desaceleración y velocidad máxima.
- **Diagnóstico**: Lectura y reset de códigos de alarma (Hall failure, etc.).
- **Interfaz Moderna**: Diseño premium utilizando `CustomTkinter`.

## Requisitos

- Python 3.8+
- Interfaz USB a RS485 (Configuración: 9600, 8, N, 1).

## Implementación

### Estructura del Proyecto

- `app.py`: Servidor backend (FastAPI) que maneja la comunicación Modbus.
- `modbus_manager.py`: Módulo de comunicación serie.
- `static/`: Frontend (HTML/JS/CSS) del dashboard.
- `requirements.txt`: Dependencias del proyecto.

### Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/sector7gp/ceamodbus.git
   cd CEAModbus
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

### Uso

1. Iniciar el servidor:
   ```bash
   python app.py
   ```
2. Abrir el navegador en: `http://localhost:8000`

| Registro | Función | Descripción |
| :--- | :--- | :--- |
| `0x0056` | Lectura/Escritura | Velocidad de seteo (RPM) |
| `0x005F` | Lectura | Velocidad de feedback (RPM) |
| `0x0066` | Lectura/Escritura | Estado Habilitado (0=On, 1=Off) |
| `0x006A` | Lectura/Escritura | Estado Freno (0=Brake, 1=No Brake) |
| `0x006D` | Lectura/Escritura | Dirección (1=Forward, 0=Backwards) |
| `0x0076` | Lectura/Escritura | Código de Alarma / Reset |

---
*Desarrollado para el control industrial eficiente.*
