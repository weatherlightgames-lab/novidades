"""Site novidades.weatherlightgames.pt: página "Novidades Weatherlight", feed RSS, sitemap e robots.

Lê dados.json (escrito pelo bot de novidades sempre que deteta produtos novos) e gera index.html com o
mesmo visual do calendário de eventos (fontes e estilos guardados em bot/estilo.html; dados da loja em bot/loja.json).
"""
import datetime as dt, html, json, os, re
from email.utils import format_datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://novidades.weatherlightgames.pt"
EVENTOS = "https://eventos.weatherlightgames.pt"
DISCORD = "https://discord.com/channels/685894659855220743/1573781369597861978"
AQUI = os.path.dirname(os.path.abspath(__file__))
LOJA = "https://www.weatherlightgames.pt"
DADOS = os.path.join(RAIZ, "dados.json")
DIAS_PAGINA = 42          # a página mostra as últimas 6 semanas
MAX_DADOS = 400           # o ficheiro guarda no máximo 400 produtos
SEM = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Ícone e cor de cada tipo nos filtros (cores da família do calendário)
ESTILO_TIPO = {"Figuras": ("🎎", "#6b3fa0"), "Peluches": ("🧸", "#b23a2e"), "Blind Boxes": ("🎁", "#b8860b"),
               "Model Kits": ("🤖", "#4d5a66"), "TCG": ("🃏", "#1f6f8b"), "Acessórios": ("🛡️", "#2c6fd1"),
               "RPG e Livros": ("📚", "#8a5a2b"), "Miniaturas": ("⚔️", "#a8781a"), "Outros": ("✨", "#46677a")}
# Ordem dos filtros na página
ORDEM = ["TCG", "Acessórios", "Figuras", "Model Kits", "Miniaturas", "Blind Boxes", "Peluches", "RPG e Livros", "Outros"]

# Tipo do produto a partir do nome (ordem importa: o primeiro que bater ganha)
TIPOS = [
    ("Peluches", r"\b(plush|peluche)"),
    ("Blind Boxes", r"\b(blind ?box|gashapon|capsule|mystery|caixa surpresa|trading figure)"),
    ("Model Kits", r"\b(model kit|gunpla|gundam accessories|30 ?mm|figure-rise|kotobukiya)"),
    ("Miniaturas", r"\b(miniaturas?|warhammer|citadel|wizkids|nolzur|reaper|wargam)"),
    ("Figuras", r"\b(figura|figure|nendoroid|figma|statue|estátua)"),
    ("Acessórios", r"\b(sleeves?|deck ?box|playmat|binder|álbum|album|portfolio|dice|dados|toploader|pages|storage|tapete)"),
    ("RPG e Livros", r"\b(daggerheart|dungeons|d&d|rpg|livro|book|manga|mangá)"),
    ("TCG", r"\b(booster|deck|display|bundle|tin|collection|elite trainer|card game|tcg|starter|box)"),
]


def tipo(nome):
    n = (nome or "").lower()
    for t, rx in TIPOS:
        if re.search(rx, n): return t
    return "Outros"


def carregar():
    try: return json.load(open(DADOS))
    except (FileNotFoundError, ValueError): return []


def acrescentar(produtos, quando=None):
    """Junta produtos novos (dicts com url, nome, preco, imagem, stock) ao início do ficheiro."""
    quando = quando or dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    dados = carregar(); urls = {d["url"] for d in dados}
    novos = [{"url": p["url"], "nome": p["nome"], "preco": p.get("preco"), "imagem": p.get("imagem"),
              "imagens": (p.get("imagens") or [])[:6], "marca": p.get("marca"), "gtin": p.get("gtin"),
              "tipo": tipo(p["nome"]), "data": quando} for p in produtos if p["url"] not in urls]
    dados = (novos + dados)[:MAX_DADOS]
    json.dump(dados, open(DADOS, "w"), ensure_ascii=False, indent=1)
    return len(novos)


def quadrado(u):
    """Versão quadrada de 400 px que a Shopkit já gera (muito mais leve que o original)."""
    return re.sub(r"/media/images/(?:thumb/|square/)?", "/media/images/square/", u, count=1)


def fotos(d):
    l = d.get("imagens") or ([d["imagem"]] if d.get("imagem") else [])
    vistos, r = set(), []
    for u in l:
        k = u.rsplit("/", 1)[-1]
        if k not in vistos: vistos.add(k); r.append(u)
    return r


def loja_ld():
    """Dados da loja (GameStore), copiados do calendário de eventos."""
    return json.load(open(os.path.join(AQUI, "loja.json")))


def preco(p):
    try: return f"{float(p):.2f} €".replace(".", ",")
    except (TypeError, ValueError): return ""


def lisboa(iso):
    """Data/hora em Lisboa (WET/WEST) sem depender de tzdata."""
    t = dt.datetime.fromisoformat(iso)
    if t.tzinfo is None: t = t.replace(tzinfo=dt.timezone.utc)
    t = t.astimezone(dt.timezone.utc)
    y = t.year
    ini = max(dt.datetime(y, 3, d, 1, tzinfo=dt.timezone.utc) for d in range(25, 32) if dt.date(y, 3, d).weekday() == 6)
    fim = max(dt.datetime(y, 10, d, 1, tzinfo=dt.timezone.utc) for d in range(25, 32) if dt.date(y, 10, d).weekday() == 6)
    return t + dt.timedelta(hours=1 if ini <= t < fim else 0)


def concha():
    """Fontes e estilos do calendário de eventos (cópia em bot/estilo.html)."""
    return open(os.path.join(AQUI, "estilo.html")).read()


def gerar():
    dados = carregar()
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_PAGINA)
    vis = [d for d in dados if dt.datetime.fromisoformat(d["data"]).astimezone(dt.timezone.utc) >= limite]
    grupos, ordem = {}, []
    for d in vis:
        l = lisboa(d["data"]); k = l.date()
        if k not in grupos: grupos[k] = []; ordem.append(k)
        grupos[k].append(d)
    tipos = ORDEM
    presentes = [t for t in tipos if any(d["tipo"] == t for d in vis)]
    filtros = ('<div class="flt"><p class="flt-t">Filtra por categoria <span>· podes escolher várias</span></p>'
               '<div class="filters" role="group" aria-label="Filtrar por categoria (podes escolher várias)">'
               '<button type="button" class="f f-all" data-t="all" aria-pressed="true"><img src="/logos/wl.webp" alt="" width="139" height="160">Todas</button>'
               + "".join(f'<button type="button" class="f" data-t="{html.escape(t)}" aria-pressed="false" style="--gc:{ESTILO_TIPO[t][1]}">'
                         f'<span class="ic" aria-hidden="true">{ESTILO_TIPO[t][0]}</span>{html.escape(t)}</button>' for t in presentes)
               + '</div></div>')

    def card(d):
        fs = fotos(d)
        alt = html.escape(d["nome"])
        img = "".join(f'<img src="{html.escape(quadrado(u))}" alt="{alt if i == 0 else ""}" loading="lazy"{" class=on" if i == 0 else ""}>'
                      for i, u in enumerate(fs)) or '<i></i>'
        if len(fs) > 1: img += '<b class="dots">' + "<u></u>" * len(fs) + "</b>"
        return (f'<a class="np" data-t="{html.escape(d["tipo"])}" href="{html.escape(d["url"])}" target="_blank" rel="noopener">'
                f'<span class="ph{" sl" if len(fotos(d)) > 1 else ""}">{img}</span><span class="tg">{html.escape(d["tipo"])}</span>'
                f'<strong>{html.escape(d["nome"])}</strong><span class="pr">{preco(d.get("preco"))}</span>'
                f'<em>Ver na loja ↗</em></a>')

    blocos = "".join(
        f'<section class="dia"><h2>{SEM[k.weekday()].capitalize()}, {k.day} de {MES[k.month - 1]}</h2>'
        f'<div class="grid">{"".join(card(d) for d in grupos[k])}</div></section>' for k in ordem)
    if not blocos:
        blocos = '<section class="box"><p class="m">As novidades aparecem aqui assim que chegam à loja online.</p></section>'
    estilos = concha()
    url = f"{BASE}/"
    desc = ("Novidades da Weatherlight, loja de hobby em Évora (Alentejo, Portugal): figuras de anime, TCG, blind boxes, "
            "Gunpla, peluches e acessórios acabados de chegar. Atualizado de hora a hora.")
    og = next((d["imagem"] for d in vis if d.get("imagem")), "")
    ld_loja = loja_ld(); ld_loja["@id"] = LOJA + "/#loja"

    def produto(d):
        x = {"@type": "Product", "name": d["nome"], "url": d["url"], "image": fotos(d)[:3] or None,
             "brand": {"@type": "Brand", "name": d["marca"]} if d.get("marca") else None, "gtin13": d.get("gtin") or None,
             "offers": {"@type": "Offer", "price": d.get("preco"), "priceCurrency": "EUR", "url": d["url"],
                        "seller": {"@id": ld_loja["@id"]}} if d.get("preco") is not None else None}
        return {k: v for k, v in x.items() if v}
    ld = {"@context": "https://schema.org", "@graph": [ld_loja, {
        "@type": "CollectionPage", "name": "Novidades Weatherlight — Évora, Alentejo, Portugal", "url": url, "inLanguage": "pt-PT",
        "about": {"@id": ld_loja["@id"]}, "spatialCoverage": {"@type": "Place", "name": "Évora, Alentejo, Portugal"},
        "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": produto(d)}
                                                                for i, d in enumerate(vis[:50])]}}]}
    css = (".lede a{color:var(--hd-ink)}.f .ic{font-size:1.25rem;line-height:1}.flt{margin:0 0 1.6rem}"
           "@media (max-width:640px){.f{flex-direction:column;gap:.1rem;height:3.5rem;line-height:1.1;text-align:center}.f .ic{font-size:1.05rem}}"
           ".dia{margin:0 0 2rem}.dia h2{font-size:1.05rem;letter-spacing:.06em;text-transform:uppercase;margin:0 0 .8rem}"
           ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:1rem}"
           ".np{display:flex;flex-direction:column;gap:.35rem;background:#fff;border:1px solid var(--line);border-radius:12px;padding:.7rem;color:inherit;text-decoration:none;transition:transform .15s,box-shadow .15s}"
           ".np:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(40,70,85,.12)}"
           ".ph{display:block;position:relative;aspect-ratio:1;background:#fff;border-radius:8px;overflow:hidden}"
           ".ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:block;transform:scale(1.25);opacity:0;transition:opacity .35s}"
           ".ph img.on{opacity:1}.dots{position:absolute;left:0;right:0;bottom:6px;display:flex;justify-content:center;gap:5px}"
           ".dots u{width:6px;height:6px;border-radius:50%;background:var(--line);text-decoration:none}.dots u.on{background:var(--ink)}"
           ".intro{display:block;margin:0 0 1.2rem}.intro a{display:inline}.ph i{display:block;width:100%;height:100%;background:var(--foam)}"
           ".tg{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}"
           ".np strong{font-weight:500;font-size:.92rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}"
           ".pr{font-weight:600;color:var(--brass)}.np em{font-style:normal;font-size:.85rem;color:var(--link);margin-top:auto}"
           ".hid{display:none!important}"
           "@media (max-width:480px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:.7rem}}")
    js = ("document.querySelectorAll('.ph.sl').forEach(ph=>{const im=[...ph.querySelectorAll('img')],dt=[...ph.querySelectorAll('.dots u')];let i=0,t=null,x=null,sw=false;"
          "const ir=n=>{i=(n+im.length)%im.length;im.forEach((m,k)=>m.classList.toggle('on',k===i));dt.forEach((m,k)=>m.classList.toggle('on',k===i))};ir(0);"
          "ph.addEventListener('mouseenter',()=>{ir(1);t=setInterval(()=>ir(i+1),1100)});ph.addEventListener('mouseleave',()=>{clearInterval(t);ir(0)});"
          "ph.addEventListener('touchstart',e=>{x=e.touches[0].clientX;sw=false},{passive:true});"
          "ph.addEventListener('touchend',e=>{const d=e.changedTouches[0].clientX-x;if(Math.abs(d)>30){sw=true;ir(i+(d<0?1:-1))}});"
          "ph.closest('a').addEventListener('click',e=>{if(sw){e.preventDefault();sw=false}})});"
          "const fb=[...document.querySelectorAll('.f')],box=document.querySelector('.filters');"
          "const apl=()=>{const sel=fb.filter(b=>b.dataset.t!=='all'&&b.getAttribute('aria-pressed')==='true').map(b=>b.dataset.t);"
          "fb.find(b=>b.dataset.t==='all')?.setAttribute('aria-pressed',sel.length?'false':'true');box&&box.classList.toggle('sel',sel.length>0);"
          "document.querySelectorAll('.np').forEach(c=>c.classList.toggle('hid',sel.length>0&&!sel.includes(c.dataset.t)));"
          "document.querySelectorAll('.dia').forEach(s=>s.classList.toggle('hid',!s.querySelector('.np:not(.hid)')))};"
          "fb.forEach(b=>b.onclick=()=>{if(b.dataset.t==='all')fb.forEach(x=>x.setAttribute('aria-pressed','false'));"
          "else b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')==='true'?'false':'true');apl()});")
    page = f"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Novidades Weatherlight | Évora, Alentejo, Portugal</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="Novidades Weatherlight" href="{url}feed.xml">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_PT"><meta property="og:site_name" content="Weatherlight Games &amp; Collectibles"><meta property="og:title" content="Novidades Weatherlight — Évora, Alentejo">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}">
{f'<meta property="og:image" content="{html.escape(og)}">' if og else ''}
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{estilos}
<style>{css}</style>
</head>
<body>
<header class="home">
  <div class="wrap">
    <span class="eyebrow">Atualizado de hora a hora · Évora</span>
    <h1>Novidades <em>Weatherlight</em></h1>
    <p class="sub">Os produtos novos da Weatherlight, a tua loja de hobby em Évora, no Alentejo</p>
    <p class="lede">Trading Card Games, Acessórios, Figuras de Anime, Model Kits, Miniaturas, Blind Boxes e Peluches: tudo o que chega à Weatherlight aparece agora aqui, no próprio dia. Encontras na nossa <a href="{LOJA}/" target="_blank" rel="noopener">loja online</a> e na loja física em Évora.</p>
    <div class="info"><a href="{LOJA}/" target="_blank" rel="noopener">🛒 Loja online</a><a href="{DISCORD}" target="_blank" rel="noopener">🔔 Alertas no Discord</a><a href="{EVENTOS}/">📅 Eventos e torneios</a><a href="{html.escape(ld_loja.get("hasMap", ""))}" target="_blank" rel="noopener">📍 Mapa</a><a href="https://www.instagram.com/weatherlightgames/" target="_blank" rel="noopener">Instagram</a><a href="{url}feed.xml">RSS</a></div>
  </div>
</header>
<main>
  <div class="wrap">
    {filtros}
    {blocos}
    <p class="m small">Atualizado automaticamente de hora a hora. Preços e stock confirmados na loja online.</p>
  </div>
</main>
<footer><div class="wrap"><p class="close">Weatherlight Games &amp; Collectibles · {html.escape(ld_loja.get("address", {}).get("streetAddress", ""))}, {html.escape(ld_loja.get("address", {}).get("postalCode", ""))} Évora · Alentejo, Portugal</p><p class="close">Queres saber primeiro? Ativa as notificações do canal ✨│novidades-wl no nosso <a href="{DISCORD}" target="_blank" rel="noopener">Discord</a>. Torneios e eventos da semana no <a href="{EVENTOS}/">calendário Weatherlight</a>.</p></div></footer>
<script>{js}</script>
</body>
</html>
"""
    open(os.path.join(RAIZ, "index.html"), "w").write(page)
    # RSS
    itens = "".join(
        f"<item><title>{html.escape(d['nome'])}</title><link>{html.escape(d['url'])}</link><guid>{html.escape(d['url'])}</guid>"
        f"<pubDate>{format_datetime(dt.datetime.fromisoformat(d['data']).astimezone(dt.timezone.utc))}</pubDate>"
        f"<category>{html.escape(d['tipo'])}</category>"
        f"<description>{html.escape(preco(d.get('preco')) + (('<br><img src=\"' + d['imagem'] + '\">') if d.get('imagem') else ''))}</description></item>"
        for d in dados[:60])
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Novidades Weatherlight</title>'
           f"<link>{url}</link><description>{html.escape(desc)}</description><language>pt-PT</language>{itens}</channel></rss>\n")
    open(os.path.join(RAIZ, "feed.xml"), "w").write(rss)
    open(os.path.join(RAIZ, "sitemap.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'  <url><loc>{url}</loc><lastmod>{dt.date.today().isoformat()}</lastmod><changefreq>hourly</changefreq></url>\n</urlset>\n')
    open(os.path.join(RAIZ, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    open(os.path.join(RAIZ, "llms.txt"), "w").write(
        f"# Novidades Weatherlight\n\n> Produtos que acabaram de chegar à Weatherlight Games & Collectibles, loja de hobby em Évora "
        f"(Alentejo, Portugal): TCG, figuras de anime, blind boxes, Gunpla, peluches e acessórios. Atualizado de hora a hora.\n\n"
        f"- [Novidades Weatherlight]({url})\n- [Feed RSS]({url}feed.xml)\n- [Loja online]({LOJA}/)\n- [Calendário de eventos]({EVENTOS}/)\n\n"
        "## Últimas novidades\n\n" + "".join(f"- [{d['nome']}]({d['url']}) · {preco(d.get('preco'))}\n" for d in vis[:40]))
    return url


if __name__ == "__main__":
    print(gerar())
