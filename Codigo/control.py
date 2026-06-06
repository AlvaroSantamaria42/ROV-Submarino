import sys
import pygame
import time 
import socket
import threading

# Importo codigos
from motores import ComponenteMotores
from video import ComponenteVideo

VERSION_SOFTWARE = "v1.3.0"  # Versión con Telemetría Completa (GY-21 + MS5837)
LOOP_HZ = 25  
running = True

# ==========================================
# TELEMETRIA UNIFICADA ENRIQUECIDA
# ==========================================
UDP_IP_PC = "192.168.10.1"   # IP de esta PC
PUERTO_TELEMETRIA = 5006     # Puerto coincidente con la Rasp

# Variables globales para los 6 datos
temp_cpu_global = "--.-"
temp_int_global = "--.-"
humi_int_global = "--.-"
temp_agua_global = "--.-"
presion_global = "--.-"
profundidad_global = "--.-"

def hilo_receptor_telemetria():
    """ Hilo de fondo encargado de escuchar y desempaquetar los 6 sensores de la Rasp """
    global temp_cpu_global, temp_int_global, humi_int_global
    global temp_agua_global, presion_global, profundidad_global, running
    
    sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_in.bind((UDP_IP_PC, PUERTO_TELEMETRIA))
    sock_in.settimeout(2.5) # Si pasan 2.5 segundos sin datos, asumimos desconexión
    
    while running:
        try:
            data, addr = sock_in.recvfrom(1024)
            # Desempaquetamos el string largo de 6 datos (split por comas)
            datos_lista = data.decode().split(",")
            
            if len(datos_lista) == 6:
                temp_cpu_global = datos_lista[0]
                temp_int_global = datos_lista[1]
                humi_int_global = datos_lista[2]
                temp_agua_global = datos_lista[3]
                presion_global = datos_lista[4]
                profundidad_global = datos_lista[5]
        except socket.timeout:
            # Si se corta la señal, mostramos guiones en todo por seguridad
            temp_cpu_global = "--.-"
            temp_int_global = "--.-"
            humi_int_global = "--.-"
            temp_agua_global = "--.-"
            presion_global = "--.-"
            profundidad_global = "--.-"
        except Exception:
            break
            
    sock_in.close()

# Inicialización de Pygame General
pygame.init()
pygame.joystick.init()

info_pantalla = pygame.display.Info()
SCREEN_WIDTH = info_pantalla.current_w
SCREEN_HEIGHT = info_pantalla.current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("ROV Control Station - ESTACION UNIFICADA")
pygame.mouse.set_visible(False)

# Fuentes tipográficas
font = pygame.font.SysFont("Consolas", 18)  
motor_font = pygame.font.SysFont("Consolas", 12, bold=True) 
version_font = pygame.font.SysFont("Consolas", 14)  
title_font = pygame.font.SysFont("Consolas", 28, bold=True)
clock = pygame.time.Clock()

if pygame.joystick.get_count() == 0:
    print("Error: No se detectó Joystick")
    pygame.quit()
    sys.exit()

joy = pygame.joystick.Joystick(0)
joy.init()

# Dimensiones fijas para el cuadro del video central
VIDEO_W, VIDEO_HEIGHT = 960, 720
X_VIDEO = (SCREEN_WIDTH - VIDEO_W) // 2 + 50  
Y_VIDEO = (SCREEN_HEIGHT - VIDEO_HEIGHT) // 2

# INSTANCIAMOS LOS DOS MÓDULOS QUE TENES SEPARADOS
motores_rov = ComponenteMotores(screen, title_font, motor_font, font, info_pantalla)
video_rov = ComponenteVideo(ip_pc="192.168.10.1", puerto=5000)

# PRENDEMOS LOS HILOS DE FONDO
video_rov.iniciar()

thread_telemetria = threading.Thread(target=hilo_receptor_telemetria, daemon=True)
thread_telemetria.start()

# Variables para capturas de foto
tiempo_foto = 0.0  
DURACION_CARTEL = 1.0  
ultima_foto_surface = None  

# ==========================================
# BUCLE PRINCIPAL
# ==========================================
try:
    while running:
        ahora = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 3: 
                    video_rov.capturar_foto()
                    tiempo_foto = ahora  
                    # Mini retardo antes de leer del disco
                    import glob, os
                    time.sleep(0.15)
                    try:
                        archivos = glob.glob("capturas/*.jpg")
                        if archivos:
                            ultimo_archivo = max(archivos, key=os.path.getmtime)
                            ultima_foto_surface = pygame.image.load(ultimo_archivo).convert()
                    except: pass

        # Fondo base del HUD
        screen.fill((15, 18, 26))  
        screen.blit(title_font.render("ROV SUBMARINO", True, (40, 140, 190)), (30, 30))
        screen.blit(version_font.render(VERSION_SOFTWARE, True, (100, 115, 130)), (30, 70))

        # --- 1. RECUADRO DE TELEMETRÍA (ARRIBA A LA IZQUIERDA) ---
        # Ampliamos el alto a 160 píxeles para meter los 6 datos de forma holgada
        BOX_X, BOX_Y = 30, 95
        pygame.draw.rect(screen, (22, 28, 38), (BOX_X, BOX_Y, 240, 160))
        pygame.draw.rect(screen, (40, 140, 190), (BOX_X, BOX_Y, 240, 160), 1)
        
        # Color dinámico de alerta para CPU
        if temp_cpu_global == "--.-": color_cpu = (100, 110, 120)
        elif float(temp_cpu_global) > 70.0: color_cpu = (255, 50, 50)
        else: color_cpu = (255, 255, 255)
            
        color_int = (100, 110, 120) if temp_int_global == "--.-" else (0, 210, 255)
        color_ext = (100, 110, 120) if temp_agua_global == "--.-" else (0, 255, 120)  # Verde para datos de inmersión

        # Dibujamos las 6 lecturas ordenadas (espaciadas cada 24 píxeles)
        screen.blit(font.render(f"CPU RPi:    {temp_cpu_global} °C", True, color_cpu), (BOX_X + 15, BOX_Y + 10))
        screen.blit(font.render(f"Temp Int:   {temp_int_global} °C", True, color_int), (BOX_X + 15, BOX_Y + 34))
        screen.blit(font.render(f"Humedad:    {humi_int_global} %", True, color_int), (BOX_X + 15, BOX_Y + 58))
        screen.blit(font.render(f"Temp Agua:  {temp_agua_global} °C", True, color_ext), (BOX_X + 15, BOX_Y + 82))
        screen.blit(font.render(f"Presión:    {presion_global} mb", True, color_ext), (BOX_X + 15, BOX_Y + 106))
        screen.blit(font.render(f"Prof:       {profundidad_global} m", True, (255, 255, 0) if profundidad_global != "--.-" else (100, 110, 120)), (BOX_X + 15, BOX_Y + 130))

        # --- 2. MOTORES ---
        # IMPORTANTE ADVERTENCIA: Como este panel de telemetría termina en Y = 255,
        # andá a motores.py y configurá PANEL_M_Y en 275 o más para que no se pisen.
        motores_rov.actualizar_y_dibujar(joy, X_VIDEO, Y_VIDEO, VIDEO_W, VIDEO_HEIGHT)

        # --- 3. VIDEO ---
        video_rect = pygame.Rect(X_VIDEO, Y_VIDEO, VIDEO_W, VIDEO_HEIGHT)
        pygame.draw.rect(screen, (0, 0, 0), video_rect) 
        
        frame_actual = video_rov.obtener_frame()
        if frame_actual is not None:
            frame_escalado = pygame.transform.scale(frame_actual, (VIDEO_W, VIDEO_HEIGHT))
            screen.blit(frame_escalado, (X_VIDEO, Y_VIDEO))
        else:
            no_vid_text = title_font.render("SIN SEÑAL DE VIDEO", True, (255, 60, 60) if int(ahora * 2) % 2 == 0 else (150, 30, 30))
            screen.blit(no_vid_text, (X_VIDEO + 320, Y_VIDEO + 330))
            
        pygame.draw.rect(screen, (40, 140, 190), video_rect, 2)  

        # --- 4. SCREENSHOT ---
        if ahora - tiempo_foto < DURACION_CARTEL:
            ancho_cartel, alto_cartel = 220, 40
            x_cartel = X_VIDEO + VIDEO_W - ancho_cartel - 15
            y_cartel = Y_VIDEO + 15
            pygame.draw.rect(screen, (10, 30, 15), (x_cartel, y_cartel, ancho_cartel, alto_cartel))
            pygame.draw.rect(screen, (0, 255, 100), (x_cartel, y_cartel, ancho_cartel, alto_cartel), 2)
            if int(ahora * 4) % 2 == 0:
                screen.blit(font.render("[ FOTO GUARDADA ]", True, (0, 255, 100)), (x_cartel + 20, y_cartel + 10))
            else:
                screen.blit(font.render("[ FOTO GUARDADA ]", True, (0, 180, 70)), (x_cartel + 20, y_cartel + 10))

        # Miniatura screenshot
        MIRA_X = X_VIDEO + VIDEO_W
        MIRA_Y = Y_VIDEO + (VIDEO_HEIGHT // 2)
        THUMB_X, THUMB_Y, THUMB_W, THUMB_H = MIRA_X + 20, MIRA_Y - 300, 240, 180  
        pygame.draw.rect(screen, (22, 28, 38), (THUMB_X, THUMB_Y, THUMB_W, THUMB_H))
        pygame.draw.rect(screen, (40, 140, 190), (THUMB_X, THUMB_Y, THUMB_W, THUMB_H), 1)
        if ultima_foto_surface is not None:
            foto_escalada = pygame.transform.scale(ultima_foto_surface, (THUMB_W - 4, THUMB_H - 4))
            screen.blit(foto_escalada, (THUMB_X + 2, THUMB_Y + 2))
        else:
            screen.blit(motor_font.render("[VACÍO]", True, (55, 65, 80)), (THUMB_X + 100, THUMB_Y + 85))
        
        # --- 5. ATAJOS ---
        screen.blit(font.render("[ESC] Salir | [Y] Captura", True, (120, 130, 140)), (30, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(LOOP_HZ)

except KeyboardInterrupt:
    pass
finally:
    print("Cerrando programa...")
    running = False
    video_rov.detener()
    motores_rov.cerrar()
    pygame.quit()