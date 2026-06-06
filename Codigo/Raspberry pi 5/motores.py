import socket
from gpiozero import Servo

# ==========================================
# CONFIGURACION DE RED Y DIRECCIONES
# ==========================================
IP_RASPBERRY = "192.168.10.2"
PUERTO_MOTORES = 5005

# ==========================================
# CONFIGURACION DE MOTORES
# ==========================================
PIN_M1 = 24
PIN_M2 = 25
PIN_M3 = 27
PIN_M4 = 19
PIN_M5 = 16
PIN_M6 = 12

MIN_PULSE = 1.00 / 1000
MAX_PULSE = 2.00 / 1000

# inicializacion de los 6 motores
m1 = Servo(PIN_M1, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)
m2 = Servo(PIN_M2, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)
m3 = Servo(PIN_M3, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)
m4 = Servo(PIN_M4, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)
m5 = Servo(PIN_M5, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)
m6 = Servo(PIN_M6, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)

motores_lista = [m1, m2, m3, m4, m5, m6]

def set_motor(motor_objeto, normalized_value):
    val_remapeado = (normalized_value * 2.0) - 1.0
    motor_objeto.value = val_remapeado

# ==========================================
# CONTROL DE MOTORES
# ==========================================
if __name__ == "__main__":

    # inicio todos los esc a cero
    for m in motores_lista:
        set_motor(m, 0.0)

    sock_motores = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_motores.bind((IP_RASPBERRY, PUERTO_MOTORES))

    try:
        while True:
            data, addr = sock_motores.recvfrom(1024) #espero y recibo datos de pc
            valores = list(map(float, data.decode().split(",")))
            
            # filtro los datos entre 0.0 y 1.0
            motors = [max(0, min(1, m)) for m in valores[0:6]]
            
            set_motor(m1, motors[0])
            set_motor(m2, motors[1])
            set_motor(m3, motors[2])
            set_motor(m4, motors[3])
            set_motor(m5, motors[4])
            set_motor(m6, motors[5])

    except KeyboardInterrupt:
        pass
    finally:
        for m in motores_lista:
            set_motor(m, 0.0)
            try:
                m.close()
            except:
                pass
            
        sock_motores.close()
