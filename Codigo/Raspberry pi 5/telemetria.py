import socket
import time
from smbus2 import SMBus

# ==========================================
# CONFIGURACION DE RED Y DIRECCIONES I2C
# ==========================================
IP_PC = "192.168.10.1"
PUERTO_TELEMETRIA = 5006      # Puerto telemetria

# Sensor sht21/htu21
ADDR_GY21 = 0x40
CMD_TEMP_HOLD = 0xE3
CMD_HUMI_HOLD = 0xE5

# Sensor de presion MS5837-30BA
MS5837_ADDR = 0x76
CMD_RESET = 0x1E
CMD_ADC_READ = 0x00
CMD_CONVERT_D1 = 0x48  # presion
CMD_CONVERT_D2 = 0x58  # temperatura
CMD_PROM_READ = 0xA0

# ==========================================
# CALIBRACION DEL MS5837
# ==========================================
C = []
try:
    with SMBus(1) as bus_init:
        bus_init.write_byte(MS5837_ADDR, CMD_RESET)
        time.sleep(0.1)

        for i in range(7):
            data_prom = bus_init.read_i2c_block_data(MS5837_ADDR, CMD_PROM_READ + i * 2, 2)
            val_coef = data_prom[0] << 8 | data_prom[1]
            C.append(val_coef)
    #print(f"MS5837 calibrado con exito.")

except Exception as e:
    #print(f"No se pudo inicializar el MS5837: {e}")
    C = [0] * 7

# ==========================================
# LECTURA DE SENSORES
# ==========================================
def obtener_temp_cpu():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_cruda = int(f.read())
            return temp_cruda / 1000.0
    except:
        return None

def leer_sensor_gy21(comando):
    try:
        with SMBus(1) as bus:
            data = bus.read_i2c_block_data(ADDR_GY21, comando, 3)
            return ((data[0] << 8) + data[1]) & 0xFFFC
    except:
        return None

def read_ms5837_adc(cmd):
    try:
        with SMBus(1) as bus:
            bus.write_byte(MS5837_ADDR, cmd)
            time.sleep(0.02)
            data = bus.read_i2c_block_data(MS5837_ADDR, CMD_ADC_READ, 3)
            return data[0] << 16 | data[1] << 8 | data[2]
    except:
        return None

if __name__ == "__main__":
    sock_telemetria = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #print(f"Servicio unificado activo. Enviando a {IP_PC}:{PUERTO_TELEMETRIA}...")

    try:
        while True:

            # 1. temp cpu Rpi
            temp_cpu = obtener_temp_cpu()
            txt_temp_cpu = f"{temp_cpu:.1f}" if temp_cpu is not None else "--.-"


            # 2. Sensor sht21/htu21
            raw_temp_int = leer_sensor_gy21(CMD_TEMP_HOLD)
            time.sleep(0.05)
            raw_humi_int = leer_sensor_gy21(CMD_HUMI_HOLD)

            if raw_temp_int is not None and raw_humi_int is not None:
                temp_int = -46.85 + (175.72 * raw_temp_int / 65536.0)
                humi_int = -6.0 + (125.0 * raw_humi_int / 65536.0)
                humi_int = max(0.0, min(100.0, humi_int))

                txt_temp_int = f"{temp_int:.1f}"
                txt_humi_int = f"{humi_int:.1f}"
            else:
                txt_temp_int = "--.-"
                txt_humi_int = "--.-"

            # 3. sensor MS5837-30BA
            time.sleep(0.05)
            D1 = read_ms5837_adc(CMD_CONVERT_D1)

            time.sleep(0.05)
            D2 = read_ms5837_adc(CMD_CONVERT_D2)

            if D1 is not None and D2 is not None and len(C) == 7 and C[1] != 0:

                # Calculo de las variables
                dT = D2 - C[5] * 256
                TEMP = 2000 + dT * C[6] / 8388608
                OFF = C[2] * 65536 + (C[4] * dT) / 128
                SENS = C[1] * 32768 + (C[3] * dT) / 256
                P = (D1 * SENS / 2097152 - OFF) / 8192

                temp_agua = TEMP / 100.0
                pressure_mbar = P / 10.0
                depth_m = (pressure_mbar - 1013.25) * 0.0102

                txt_temp_agua = f"{temp_agua:.1f}"
                txt_presion = f"{pressure_mbar:.1f}"
                txt_depth = f"{depth_m:.2f}"

            else:
                txt_temp_agua = "--.-"
                txt_presion = "--.-"
                txt_depth = "--.-"

            # 4. Vector de variables
            mensaje = f"{txt_temp_cpu},{txt_temp_int},{txt_humi_int},{txt_temp_agua},{txt_presion},{txt_depth}"

            # 5. Envio por UDP
            sock_telemetria.sendto(mensaje.encode(), (IP_PC, PUERTO_TELEMETRIA))

            time.sleep(1.5)

    except KeyboardInterrupt:
        pass

    finally:
        sock_telemetria.close()
