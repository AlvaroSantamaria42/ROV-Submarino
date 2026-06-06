import cv2
import socket
import time

# ==========================================
# CONFIGURACION DE RED Y DIRECCIONES
# ==========================================
IP_PC = "192.168.10.1"  # IP de la PC receptora
PUERTO_VIDEO = 5000     # Puerto coincidente con tu script de PC

# ==========================================
# CONFIGURACION DE LA CAMARA
# ==========================================
# 0 suele ser la camara por defecto (/dev/video0)
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
# Configuramos la resolucion  que espera mi receptor (320x240)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
# ==========================================
# TRANSMISION DE VIDEO
# ==========================================
if __name__ == "__main__":
    # Creo el socket UDP nativo
    sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #print(f"Transmitiendo video a {IP_PC}:{PUERTO_VIDEO}...")

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error al leer de la camara.")
                break

            # comprimimos el frame a formato JPEG
            # l receptor necesita este formato para que cv2.imdecode funcione
            resultado, enc_img = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

            if resultado:
                # convierto la imagen codificada a bytes crudos
                data = enc_img.tobytes()

                # el UDP tiene un limite de 65507 bytes por paquete
                if len(data) < 65507:
                    sock_video.sendto(data, (IP_PC, PUERTO_VIDEO))
                else:
                    print("Frame demasiado grande para un solo paquete UDP.")

            # una pausita para controlar los FPS (aprox 30 FPS) y no saturar la red
            time.sleep(0.03)

    except KeyboardInterrupt:
        print("")
    finally:
        # Liberamos todos los recursos
        cap.release()
        sock_video.close()
        print("Recursos de video liberados.")
