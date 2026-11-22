"""Capturas do site (página inteira) para posts e vídeos. Corre no GitHub Actions (workflow Capturas)."""
import os, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://novidades.weatherlightgames.pt/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "capturas"
os.makedirs(OUT, exist_ok=True)
PERFIS = {
    "computador": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=2),
    "telemovel": dict(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True,
                      user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"),
}
with sync_playwright() as p:
    b = p.chromium.launch()
    for nome, perfil in PERFIS.items():
        pg = b.new_page(**perfil)
        pg.goto(URL, wait_until="networkidle")
        h = pg.evaluate("document.body.scrollHeight")
        for y in range(0, h, 400):  # passa pela página para carregar as fotos (lazy)
            pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(120)
        pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(1500)
        pg.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{OUT}/{nome}-pagina.png", full_page=True)
        pg.screenshot(path=f"{OUT}/{nome}-topo.png")
        # cartão com o cursor em cima (fotos a passar)
        if nome == "computador":
            c = pg.query_selector(".np .ph.sl")
            if c:
                c.scroll_into_view_if_needed(); pg.mouse.move(0, 0)
                box = c.bounding_box(); pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                pg.wait_for_timeout(1500); pg.screenshot(path=f"{OUT}/computador-hover.png")
        print(nome, h)
    b.close()
