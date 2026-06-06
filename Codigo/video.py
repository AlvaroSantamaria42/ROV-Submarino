import socket
import threading
import cv2
import numpy as np
import pygame
import os
from datetime import datetime

class ComponenteVideo:
    def __init__(self, ip_pc="192.168.10.1", puerto=5000):
        self.ip = ip_pc
        self.puerto = puerto
        self.ultimo_frame_surface = None
        self.running = False
        self.lock = threading.Lock()
        self.thread = None
        
        # Bandera para avisarle al hilo que guarde la foto original
        self.guardar_proximo_frame = False

    def iniciar(self):
        self.running = True
        self.thread = threading.Thread(target=self._hilo_receptor, daemon=True)
        self.thread.start()

    def _hilo_receptor(self):
        sock_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_video.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        sock_video.bind((self.ip, self.puerto))
        sock_video.settimeout(1.0)
        
        while self.running:
            try:
                packet, addr = sock_video.recvfrom(65535)
                data = np.frombuffer(packet, dtype=np.uint8)
                frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # VALIDACIÓN: Si el usuario solicitó una foto, la guardamos de inmediato
                    if self.guardar_proximo_frame:
                        self._guardar_imagen_disco(frame)
                        self.guardar_proximo_frame = False # Bajamos la bandera

                    # Convertir formato de OpenCV (BGR) a Pygame (RGB) y rotar matrices
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_transpuesto = np.rot90(frame_rgb)
                    frame_transpuesto = cv2.flip(frame_transpuesto, 0)
                    
                    # Convertir la matriz directamente en una superficie de Pygame
                    surface = pygame.surfarray.make_surface(frame_transpuesto)
                    
                    with self.lock:
                        self.ultimo_frame_surface = surface
            except socket.timeout:
                with self.lock:
                    self.ultimo_frame_surface = None
            except Exception:
                break
                
        sock_video.close()

    def capturar_foto(self):
        """ Activa la bandera para que el hilo receptor guarde el próximo frame que llegue """
        self.guardar_proximo_frame = True

    def _guardar_imagen_disco(self, frame_opencv):
        """ Función interna encargada de crear la carpeta y escribir el archivo JPEG nativo """
        try:
            # Creamos la carpeta 'capturas' si no existe
            if not os.path.exists("capturas"):
                os.makedirs("capturas")
            
            # Generamos un nombre único basado en la fecha y hora: capturar_AAAA-MM-DD_HHMMSS.jpg
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            nombre_archivo = f"capturas/captura_{timestamp}.jpg"
            
            # Guardamos usando OpenCV de forma nativa (mantiene la máxima definición)
            cv2.imwrite(nombre_archivo, frame_opencv)
            print(f"[OK] Foto guardada con éxito en: {nombre_archivo}")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar la captura: {e}")

    def obtener_frame(self):
        with self.lock:
            return self.ultimo_frame_surface

    def detener(self):
        self.running = False