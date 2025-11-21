import os, sys, subprocess, platform
import pygame as pg

EDITOR = "editor.py"
VIEWER = "viewer.py"

def run_script(script, args=None, new_console=False):
    if not os.path.exists(script):
        return f"Missing: {script}"

    cmd = [sys.executable, script]  
    if args:
        cmd.extend(args)        

    try:
        if new_console and platform.system() == "Windows":
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(cmd, creationflags=CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(cmd)    
        return f"Launched: {script}"
    except Exception as e:
        return f"Failed to launch {script}: {e}"

pg.init()
W, H = 520, 300                        
screen = pg.display.set_mode((W, H))
pg.display.set_caption("TreatQuest — Launcher")

font = pg.font.SysFont("consolas", 18)
font_big = pg.font.SysFont("consolas", 26)
BG = (22, 22, 26) 

def draw_button(rect, label, hotkey=None, enabled=True, hover=False):
    base = (44, 48, 60) if enabled else (32, 34, 40)   
    hi   = (70, 90, 130)                             
    col = hi if (hover and enabled) else base
    pg.draw.rect(screen, col, rect, border_radius=10)
    pg.draw.rect(screen, (95, 100, 120), rect, 1, border_radius=10)

    text = label if not hotkey else f"{label}  [{hotkey}]"
    tx = font_big.render(text, True, (235, 235, 245))
    screen.blit(tx, (rect.x + 16, rect.y + rect.height//2 - tx.get_height()//2))

def exists(p):
    return os.path.exists(p)

def main():
    status = "Select an option."    
    running = True
    pad = 22                            
    bw, bh = W - pad*2, 64              
    y0 = 90                              
    btn_create = pg.Rect(pad, y0, bw, bh)
    btn_view   = pg.Rect(pad, y0 + bh + pad, bw, bh)

    while running:
        screen.fill(BG)
        title = font_big.render("Map Tools", True, (240, 240, 250))
        screen.blit(title, (pad, 24))

        mx, my = pg.mouse.get_pos()

        hov_create = btn_create.collidepoint(mx, my)
        hov_view   = btn_view.collidepoint(mx, my)

        draw_button(btn_create, "Create Map", "C / 1", enabled=exists(EDITOR),  hover=hov_create)
        draw_button(btn_view,   "View Map",   "V / 2", enabled=exists(VIEWER),  hover=hov_view)

        st = font.render(status, True, (210, 210, 220))
        screen.blit(st, (pad, H - 36))

        pg.display.flip()

        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False

            elif e.type == pg.KEYDOWN:
                k = e.key
                if k in (pg.K_ESCAPE, pg.K_q):
                    running = False

                elif k in (pg.K_c, pg.K_1) and exists(EDITOR):
                    status = run_script(EDITOR)

                elif k in (pg.K_v, pg.K_2) and exists(VIEWER):
                    status = run_script(VIEWER)

            elif e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                if btn_create.collidepoint(e.pos) and exists(EDITOR):
                    status = run_script(EDITOR)
                elif btn_view.collidepoint(e.pos) and exists(VIEWER):
                    status = run_script(VIEWER)

    pg.quit()

if __name__ == "__main__":
    main()
