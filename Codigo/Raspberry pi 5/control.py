import subprocess
import sys
import time

# ==========================================
# IMPORTO CODIGOS
# ==========================================
SCRIPT_MOTORES = "motores.py"
SCRIPT_VIDEO = "video.py"
SCRIPT_TELEMETRIA = "telemetria.py"

print("=============================")
print("      INICIANDO SISTEMA      ")
print("=============================")

proceso_motores = None
proceso_video = None
proceso_telemetria = None

try:
    print(f"[1/3] Iniciando control de motores ({SCRIPT_MOTORES})...")
    proceso_motores = subprocess.Popen([sys.executable, SCRIPT_MOTORES])
    time.sleep(0.3)

    print(f"[2/3] Iniciando transmision de video ({SCRIPT_VIDEO})...")
    proceso_video = subprocess.Popen([sys.executable, SCRIPT_VIDEO])
    time.sleep(0.3)

    print(f"[3/3] Iniciando telemetria ({SCRIPT_TELEMETRIA})...")
    proceso_telemetria = subprocess.Popen([sys.executable, SCRIPT_TELEMETRIA])

    print("\nTodas las funciones cargadas")

    # monitoreo por si se cae un codigo
    while True:

        # --- REINICIO DE MOTORES SI SE CAEN ---
        if proceso_motores.poll() is not None:
            print("\n[AVISO] Control de motores caido. Reiniciando...")
            try:
                proceso_motores.terminate()
                proceso_motores.wait()
            except:
                pass
            proceso_motores = subprocess.Popen([sys.executable, SCRIPT_MOTORES])

        # --- REINICIO DE VIDEO SI SE CAE ---
        if proceso_video.poll() is not None:
            print("\n[AVISO] Transmision de video caida. Reiniciando...")
            try:
                proceso_video.terminate()
                proceso_video.wait()
            except:
                pass
            proceso_video = subprocess.Popen([sys.executable, SCRIPT_VIDEO])

        # --- REINICIO DE TELEMETRIA SI SE CAE ---
        if proceso_telemetria.poll() is not None:
            print("\n[AVISO] Telemetria caida. Reiniciando...")
            try:
                proceso_telemetria.terminate()
                proceso_telemetria.wait()
            except:
                pass
            proceso_telemetria = subprocess.Popen([sys.executable, SCRIPT_TELEMETRIA])

        time.sleep(1)

except KeyboardInterrupt:
    print("\nCerrando procesos...\n")
finally:
    # Apago ordenado con ctrl+C
    for p, nombre in [
        (proceso_telemetria, "Telemetria"),
        (proceso_video, "Video"),
        (proceso_motores, "Motores")
    ]:
        if p and p.poll() is None:
            try:
                p.terminate()
                p.wait()
                print(f"- {nombre} finalizado.")
            except Exception as e:
                print(f"Error al cerrar {nombre}: {e}")

    print("==================================")
    print("         SISTEMA APAGADO          ")
    print("==================================")
