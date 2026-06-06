import socket
import pygame
import os  

class ComponenteMotores:
    def __init__(self, screen, title_font, motor_font, font, info_pantalla):
        self.screen = screen
        self.title_font = title_font
        self.motor_font = motor_font
        self.font = font
        self.SCREEN_HEIGHT = info_pantalla.current_h
        
        self.UDP_IP_RPi = "192.168.10.2"
        self.PUERTO_MOTORES = 5005
        self.sock_motores = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.pos_pan = 0.0
        self.pos_tilt = 0.0
        self.VELOCIDAD_CAMARA = 0.02
        self.DEADZONE = 0.05
        
        # Cargar chasis
        self.chasis_surface = None
        if os.path.exists("chasis_top.png"):
            try:
                chasis_original = pygame.image.load("chasis_top.png").convert_alpha()
                self.chasis_surface = pygame.transform.smoothscale(chasis_original, (190, 190))
            except: pass

    def actualizar_y_dibujar(self, joy, X_VIDEO, Y_VIDEO, VIDEO_W, VIDEO_HEIGHT):
        # 1. Leer entradas del Joystick
        lateral = joy.get_axis(0)
        avance = -joy.get_axis(1)  
        giro = joy.get_axis(2)
        vertical = -joy.get_axis(3) 
        
        if abs(lateral) < self.DEADZONE: lateral = 0
        if abs(avance) < self.DEADZONE: avance = 0
        if abs(giro) < self.DEADZONE: giro = 0
        if abs(vertical) < self.DEADZONE: vertical = 0

        # Hat para Pan-Tilt
        if joy.get_numhats() > 0:
            hat_x, hat_y = joy.get_hat(0)
            self.pos_pan = max(-1.0, min(1.0, self.pos_pan + hat_x * self.VELOCIDAD_CAMARA))
            self.pos_tilt = max(-1.0, min(1.0, self.pos_tilt + hat_y * self.VELOCIDAD_CAMARA))

        # --- SEGURO DE BOTÓN RB (BOTÓN 5) ---
        boton_rb = joy.get_button(5)
        m5 = 0.0
        m6 = 0.0
        
        if boton_rb:
            # MODO VERTICAL ACTIVO: Habilitamos profundidad y bloqueamos el giro por completo
            giro = 0.0
            
            if vertical > 0: 
                m5 = vertical
            elif vertical < 0: 
                m6 = abs(vertical)
        else:
            # MODO HORIZONTAL ACTIVO: Bloqueamos profundidad y el giro funciona normal
            m5 = m6 = 0.0

        # Mezcla Vectorial (Afectada por la anulación de giro si RB está presionado)
        m1 = m2 = m3 = m4 = 0.0
        if avance > 0: m1 = m2 = avance
        elif avance < 0: m3 = m4 = abs(avance)
        
        if lateral > 0: m1 = max(m1, lateral); m3 = max(m3, lateral)
        elif lateral < 0: m2 = max(m2, abs(lateral)); m4 = max(m4, abs(lateral))
        
        if giro > 0: m1 = max(m1, giro); m4 = max(m4, giro)
        elif giro < 0: m2 = max(m2, abs(giro)); m3 = max(m3, abs(giro))

        # Escalamiento de motores verticales
        if m5 >= 0.20: m5 = 0.40 + ((m5 - 0.20) / 0.80) * 0.60
        else: m5 = 0.0
        if m6 >= 0.20: m6 = 0.40 + ((m6 - 0.20) / 0.80) * 0.60
        else: m6 = 0.0

        # Enviar UDP
        msg = f"{m1:.2f},{m2:.2f},{m3:.2f},{m4:.2f},{m5:.2f},{m6:.2f},{self.pos_pan:.2f},{self.pos_tilt:.2f}"
        self.sock_motores.sendto(msg.encode(), (self.UDP_IP_RPi, self.PUERTO_MOTORES))

        # --- DIBUJAR PANEL ---
        PANEL_M_X, PANEL_M_Y = 30, 490
        pygame.draw.rect(self.screen, (22, 28, 38), (PANEL_M_X, PANEL_M_Y, 300, 320))
        pygame.draw.rect(self.screen, (40, 140, 190), (PANEL_M_X, PANEL_M_Y, 300, 320), 1)
        self.screen.blit(self.font.render("Motores:", True, (255, 255, 0)), (PANEL_M_X + 15, PANEL_M_Y + 15))

        IMG_X, IMG_Y = PANEL_M_X + 20, PANEL_M_Y + 55
        if self.chasis_surface:
            self.screen.blit(self.chasis_surface, (IMG_X, IMG_Y))

        motor_overlays = [
            {"name": "M1", "val": m1, "cx": IMG_X + 28,  "cy": IMG_Y + 28,  "m_type": "diag_der_arriba"}, 
            {"name": "M2", "val": m2, "cx": IMG_X + 162, "cy": IMG_Y + 28,  "m_type": "diag_izq_arriba"}, 
            {"name": "M3", "val": m3, "cx": IMG_X + 28,  "cy": IMG_Y + 162, "m_type": "diag_der_abajo"},  
            {"name": "M4", "val": m4, "cx": IMG_X + 162, "cy": IMG_Y + 162, "m_type": "diag_izq_abajo"},  
            {"name": "M5", "val": m5, "cx": IMG_X + 43,  "cy": IMG_Y + 95,  "m_type": "circular"},  
            {"name": "M6", "val": m6, "cx": IMG_X + 147, "cy": IMG_Y + 95,  "m_type": "circular"}   
        ]

        for mov in motor_overlays:
            mx, my = mov["cx"], mov["cy"]
            pot = mov["val"]
            m_type = mov["m_type"]
            color_barra = (0, 255, 100) if pot > 0 else (50, 60, 75)
            max_len = 24  
            len_b = int(max_len * pot)

            if m_type == "circular":
                if pot > 0:
                    pygame.draw.circle(self.screen, (0, int(120 + (pot * 135)), 50), (mx, my), 16)
                    pygame.draw.circle(self.screen, (0, 255, 100), (mx, my), 16, 2)
                    lbl = self.motor_font.render(mov["name"], True, (255, 255, 255))
                else:
                    pygame.draw.circle(self.screen, (35, 45, 60), (mx, my), 15, 1)
                    lbl = self.motor_font.render(mov["name"], True, (110, 125, 140))
                self.screen.blit(lbl, (mx - 6, my - 6))
            else:
                if m_type == "diag_izq_arriba":
                    pygame.draw.line(self.screen, (35, 40, 50), (mx + 10, my + 10), (mx - max_len, my - max_len), 6)
                    if pot > 0: pygame.draw.line(self.screen, color_barra, (mx + 10, my + 10), (mx + 10 - len_b, my + 10 - len_b), 6)
                elif m_type == "diag_der_arriba":
                    pygame.draw.line(self.screen, (35, 40, 50), (mx - 10, my + 10), (mx + max_len, my - max_len), 6)
                    if pot > 0: pygame.draw.line(self.screen, color_barra, (mx - 10, my + 10), (mx - 10 + len_b, my + 10 - len_b), 6)
                elif m_type == "diag_izq_abajo":
                    pygame.draw.line(self.screen, (35, 40, 50), (mx + 10, my - 10), (mx - max_len, my + max_len), 6)
                    if pot > 0: pygame.draw.line(self.screen, color_barra, (mx + 10, my - 10), (mx + 10 - len_b, my - 10 + len_b), 6)
                elif m_type == "diag_der_abajo":
                    pygame.draw.line(self.screen, (35, 40, 50), (mx - 10, my - 10), (mx + max_len, my + max_len), 6)
                    if pot > 0: pygame.draw.line(self.screen, color_barra, (mx - 10, my - 10), (mx - 10 + len_b, my - 10 + len_b), 6)

                lbl = self.motor_font.render(mov["name"], True, (255, 255, 255) if pot > 0 else (110, 125, 140))
                desfase_x = 10 if "der" in m_type else -24
                self.screen.blit(lbl, (mx + desfase_x, my - 6))

        pot_max = max(m1, m2, m3, m4, m5, m6) * 100
        output_txt = self.font.render(f"Potencia: {pot_max:.0f}%", True, (0, 255, 100) if pot_max > 0 else (100, 110, 120))
        self.screen.blit(output_txt, (45, PANEL_M_Y + 275))

        # --- PANEL PAN-TILT ---
        MIRA_X = X_VIDEO + VIDEO_W + 20
        MIRA_Y = Y_VIDEO + (VIDEO_HEIGHT // 2) - 60
        pygame.draw.rect(self.screen, (22, 28, 38), (MIRA_X, MIRA_Y, 120, 120))
        pygame.draw.rect(self.screen, (40, 140, 190), (MIRA_X, MIRA_Y, 120, 120), 1)
        self.screen.blit(self.motor_font.render("POS CAMARA", True, (255, 255, 0)), (MIRA_X + 25, MIRA_Y + 10))
        pygame.draw.line(self.screen, (45, 55, 70), (MIRA_X + 60, MIRA_Y + 30), (MIRA_X + 60, MIRA_Y + 110), 1)
        pygame.draw.line(self.screen, (45, 55, 70), (MIRA_X + 20, MIRA_Y + 70), (MIRA_X + 100, MIRA_Y + 70), 1)
        pygame.draw.circle(self.screen, (0, 210, 255), (int(MIRA_X + 60 + (self.pos_pan * 40)), int(MIRA_Y + 70 - (self.pos_tilt * 40))), 5)

    def cerrar(self):
        self.sock_motores.close()