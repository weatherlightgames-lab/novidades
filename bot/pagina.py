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
               "TTRPGs": ("🎲", "#8a5a2b"), "Miniaturas": ("⚔️", "#a8781a"), "Bilhetes": ("🎟️", "#2a8a6e"), "Outros": ("✨", "#46677a")}
# Ordem dos filtros na página
ORDEM = ["TCG", "Acessórios", "Figuras", "Model Kits", "Miniaturas", "TTRPGs", "Blind Boxes", "Peluches", "Bilhetes", "Outros"]

# Tipo do produto a partir do nome (ordem importa: o primeiro que bater ganha)
TIPOS = [
    ("Bilhetes", r"\b(bilhetes?|tickets?)\b"),
    ("Miniaturas", r"\b(miniaturas?|gundam assemble|warhammer|citadel|wizkids|nolzur|reaper|wargam)"),
    ("Peluches", r"\b(plush|peluche)"),
    ("Blind Boxes", r"\b(blind ?box|gashapon|capsule|mystery|caixa surpresa|trading figure)"),
    ("Model Kits", r"\b(model kit|gunpla|gundam accessories|30 ?mm|figure-rise|kotobukiya)"),
    ("Figuras", r"\b(figura|figure|nendoroid|figma|statue|estátua)"),
    ("Acessórios", r"\b(sleeves?|deck ?box|playmat|binder|álbum|album|portfolio|dice|dados|toploader|pages|storage|tapete)"),
    ("TTRPGs", r"\b(daggerheart|dungeons|d&d|rpg|ttrpg|livro|book|manga|mangá)"),
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


CA = "https://www.weatherlightgames.pt/page/central-de-ajuda-weatherlight"
GL = "https://www.weatherlightgames.pt/page/glossario"
CONVITE = "https://discord.gg/HTCZeJZuVk"
INSTAGRAM = "https://www.instagram.com/weatherlightgames/"
TIKTOK = "https://www.tiktok.com/@weatherlightcollectibles"
TELEFONE = "266 735 119"
NOVA = ' target="_blank" rel="noopener"'
HORARIO_PADRAO = ('<p class="close hor">🕒 Horário da loja: Quarta e Sexta 15:00–23:00 · Quinta, Sábado e Domingo 15:00–20:30 · '
                  'Segunda e Terça encerrados</p>')


def loja_ld():
    """Dados da loja (GameStore), copiados do calendário de eventos."""
    return json.load(open(os.path.join(AQUI, "loja.json")))


def contacto():
    """Contacto de e-mail da loja, tal como está em bot/loja.json."""
    e = loja_ld().get("email", "")
    return f'<a href="mailto:{e}">{e}</a>' if e else "o formulário de contacto da loja online"


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


def ler(nome, padrao=""):
    try: return open(os.path.join(AQUI, nome)).read()
    except FileNotFoundError: return padrao


def concha():
    """Fontes e estilos do calendário de eventos (cópia em bot/estilo.html, atualizada por sincronizar())."""
    return ler("estilo.html")


def sincronizar():
    """O calendário é a base: copia de lá os estilos e o horário da loja (bot/estilo.html e bot/horario.html)."""
    import urllib.request
    try:
        req = urllib.request.Request(EVENTOS + "/", headers={"User-Agent": "Mozilla/5.0 (WeatherlightNovidades)"})
        t = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    except Exception as e:
        print("Não consegui ler o calendário:", e); return False
    head = t.split("<body")[0]
    estilos = re.findall(r"<style>.*?</style>", head, re.S)
    if not estilos or "--hd-accent" not in "".join(estilos):
        print("O calendário não trouxe os estilos esperados; mantenho os atuais."); return False
    fontes = "\n".join(re.findall(r'<link rel="(?:preconnect|stylesheet)"[^>]*>', head))
    try:  # estilos das páginas interiores (passos, caixas, perguntas frequentes), como na página "Primeira vez"
        req = urllib.request.Request(EVENTOS + "/primeira-vez/", headers={"User-Agent": "Mozilla/5.0 (WeatherlightNovidades)"})
        t2 = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        estilos += [x for x in re.findall(r"<style>.*?</style>", t2.split("<body")[0], re.S) if x not in estilos]
    except Exception as e:
        print("Sem os estilos das páginas interiores:", e)
    open(os.path.join(AQUI, "estilo.html"), "w").write(fontes + "\n" + "\n".join(estilos) + "\n")
    m = re.search(r'<p class="close hor">.*?</p>', t, re.S)
    if m: open(os.path.join(AQUI, "horario.html"), "w").write(m.group(0) + "\n")
    print("Estilos e horário sincronizados com o calendário.")
    return True


CSS = (".np{display:flex;flex-direction:column;gap:.4rem;background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:.7rem;min-width:0}"
       ".np:hover{border-color:var(--sea-2)}"
       ".phl{display:block;border-radius:6px;overflow:hidden}"
       ".ph{display:block;position:relative;aspect-ratio:1;background:#fff;border-radius:6px;overflow:hidden}"
       ".ph img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:block;transform:scale(1.25);opacity:0;transition:opacity .35s}"
       ".ph img.on{opacity:1}.ph i{display:block;width:100%;height:100%;background:var(--foam)}"
       ".dots{position:absolute;left:0;right:0;bottom:6px;display:flex;justify-content:center;gap:5px}"
       ".dots u{width:6px;height:6px;border-radius:50%;background:var(--line);text-decoration:none}.dots u.on{background:var(--ink)}"
       ".np .tg{display:block}.np .nm strong{font-weight:500;font-size:.95rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}"
       ".np .price{color:var(--brass)}.np .insc{align-self:flex-start;margin-top:auto;font-size:.85rem}"
       ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:.8rem}"
       ".dia{margin:0 0 2rem}.dia h2{font:500 1.4rem/1.1 var(--display);text-transform:uppercase;letter-spacing:.03em;margin:0 0 .6rem;display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap}"
       ".dia h2 small{font:400 .85rem var(--mono);color:var(--muted);letter-spacing:.04em}"
       ".lede a{color:var(--hd-ink)}.f .ic{font-size:1.25rem;line-height:1}.flt{margin:0 0 1.6rem}.help{margin:0 0 1.6rem}"
       ".hid{display:none!important}.subs{margin-top:2.5rem}"
       ".guia h2 .ic{margin-right:.35rem}.guia .ver{margin:.8rem 0 0}"
       "@media (max-width:640px){.f{flex-direction:column;gap:.1rem;height:3.5rem;line-height:1.1;text-align:center}.f .ic{font-size:1.05rem}}"
       "@media (max-width:480px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem}.np{padding:.55rem}}")

JS_FOTOS = ("document.querySelectorAll('.ph.sl').forEach(ph=>{const im=[...ph.querySelectorAll('img')],dt=[...ph.querySelectorAll('.dots u')];let i=0,t=null,x=null,sw=false;"
            "const ir=n=>{i=(n+im.length)%im.length;im.forEach((m,k)=>m.classList.toggle('on',k===i));dt.forEach((m,k)=>m.classList.toggle('on',k===i))};ir(0);"
            "const card=ph.closest('.np');card.addEventListener('mouseenter',()=>{ir(1);t=setInterval(()=>ir(i+1),1100)});card.addEventListener('mouseleave',()=>{clearInterval(t);ir(0)});"
            "ph.addEventListener('touchstart',e=>{x=e.touches[0].clientX;sw=false},{passive:true});"
            "ph.addEventListener('touchend',e=>{const d=e.changedTouches[0].clientX-x;if(Math.abs(d)>30){sw=true;ir(i+(d<0?1:-1))}});"
            "ph.closest('a').addEventListener('click',e=>{if(sw){e.preventDefault();sw=false}})});")
JS_FILTROS = ("const fb=[...document.querySelectorAll('.f')],box=document.querySelector('.filters');"
              "const apl=()=>{const sel=fb.filter(b=>b.dataset.t!=='all'&&b.getAttribute('aria-pressed')==='true').map(b=>b.dataset.t);"
              "fb.find(b=>b.dataset.t==='all')?.setAttribute('aria-pressed',sel.length?'false':'true');box&&box.classList.toggle('sel',sel.length>0);"
              "document.querySelectorAll('.np').forEach(c=>c.classList.toggle('hid',sel.length>0&&!sel.includes(c.dataset.t)));"
              "document.querySelectorAll('.dia').forEach(s=>s.classList.toggle('hid',!s.querySelector('.np:not(.hid)')))};"
              "fb.forEach(b=>b.onclick=()=>{if(b.dataset.t==='all')fb.forEach(x=>x.setAttribute('aria-pressed','false'));"
              "else b.setAttribute('aria-pressed',b.getAttribute('aria-pressed')==='true'?'false':'true');apl()});"
              "const h=decodeURIComponent(location.hash.slice(1));const hb=fb.find(b=>b.dataset.t===h);if(hb){hb.setAttribute('aria-pressed','true');apl()}")


def casca(titulo, desc, url, cabecalho, corpo, ld=None, og="", js=""):
    ld_txt = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n' if ld else ""
    rodape = (f'<footer>\n  <div class="wrap">\n'
              f'    <p class="close">Tens dúvidas? Vê a página da <a href="/primeira-compra/">primeira compra</a>, a <a href="{CA}"{NOVA}>Central de Ajuda</a> '
              f'ou junta-te à nossa comunidade no <a href="{CONVITE}"{NOVA}>Discord</a>! 👾</p>\n'
              f'    <p class="close">Preferes ver ao vivo? Temos uma <a href="{loja_ld().get("hasMap", "")}"{NOVA}>loja inteira ao teu dispor</a> em Évora — vem visitar-nos ☁️</p>\n'
              f'  {ler("horario.html", HORARIO_PADRAO).strip()}</div>\n</footer>')
    og_tag = f'<meta property="og:image" content="{html.escape(og)}">\n' if og else ""
    return f"""<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(titulo)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="Novidades Weatherlight" href="{BASE}/feed.xml">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="theme-color" content="#ffffff">
<meta name="apple-mobile-web-app-title" content="Novidades WL">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_PT"><meta property="og:site_name" content="Weatherlight Games &amp; Collectibles">
<meta property="og:title" content="{html.escape(titulo.split(' | ')[0])}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}">
{og_tag}{ld_txt}{concha().strip()}
<style>{CSS}</style>
</head>
<body>
{cabecalho}
<main>
  <div class="wrap">
{corpo}
  </div>
</main>
{rodape}
<script>{js}</script>
</body>
</html>
"""


def cab_pagina(titulo, sub, nome):
    return (f'<header>\n  <div class="wrap">\n    <span class="crumbs"><a href="/">Novidades Weatherlight</a> › {nome}</span>\n'
            f'    <h1>{titulo}</h1>\n    <p class="sub">{sub}</p>\n  </div>\n</header>')


def escrever(rel, txt):
    f = os.path.join(RAIZ, rel); os.makedirs(os.path.dirname(f), exist_ok=True); open(f, "w").write(txt)


def faq(itens):
    return "<dl>" + "".join(f"<dt>{p}</dt><dd>{r}</dd>" for p, r in itens) + "</dl>"


def ancora(chave):
    return re.sub(r"[^a-z]", "", chave.lower())


# ---------------- página: primeira compra ----------------
def primeira_compra(ld_loja):
    url = f"{BASE}/primeira-compra/"
    mapa = ld_loja.get("hasMap", "")
    c = contacto()
    passos = [
        ("Escolhe os produtos", f'Encontras tudo na nossa <a href="{LOJA}/"{NOVA}>loja online</a>: junta ao carrinho o que quiseres. Não encontras o que procuras? Fala connosco: sempre que possível, tentamos encomendá-lo junto dos nossos distribuidores.'),
        ("Escolhe como recebes", "Podes receber em casa, por <strong>DHL</strong>, em Portugal Continental, ou escolher <strong>Levantamento em Loja</strong> e vir buscar a tua encomenda a Évora, sem pagar portes. Os portes de envio aparecem no segundo passo do carrinho e dependem do destino, do peso ou valor da encomenda e do método escolhido."),
        ("Paga como preferires", "Aceitamos <strong>cartão de crédito, Multibanco, MB WAY, PayPal, carteira digital e transferência bancária</strong>. Tens um código de desconto? Depois de escolheres o método de pagamento, escreve-o em <strong>Cupão de Desconto</strong>."),
        ("Recebe a confirmação", "Depois de validado o pagamento, recebes um e-mail com a confirmação de que a encomenda está paga e a respetiva fatura."),
        ("Acompanha a entrega", "Quando a encomenda é expedida, recebes um e-mail com o código de tracking. A entrega é feita nos primeiros dois dias úteis seguintes à expedição. Se escolheste levantar na loja, aparece dentro do nosso horário de funcionamento."),
    ]
    corpo = (
        '<section class="sec"><h2>Como comprar online</h2><ol class="passos">'
        + "".join(f"<li><strong>{a}</strong><p>{b}</p></li>" for a, b in passos) + "</ol></section>\n"
        '<section class="box"><h2>Envios e levantamento</h2><ul class="dates">'
        '<li><span>Transportadora</span><span>DHL</span></li>'
        '<li><span>Para onde enviamos</span><span>Portugal Continental (não enviamos para as ilhas)</span></li>'
        '<li><span>Prazo de entrega</span><span>Até 2 dias úteis depois da expedição</span></li>'
        '<li><span>Levantamento em Loja</span><span>Grátis, na loja em Évora, dentro do horário</span></li></ul>'
        f'<p class="m small">{html.escape(ld_loja.get("address", {}).get("streetAddress", ""))}, Évora · <a href="{mapa}"{NOVA}>Ver no mapa</a> · {TELEFONE}</p></section>\n'
        '<section class="box faq"><h2>Perguntas frequentes</h2>' + faq([
            ("É para oferecer. Chega a tempo?", "Fazemos os possíveis para dar prioridade às encomendas que sabemos que são para oferta, mas não conseguimos garantir uma data se a encomenda for feita com pouca antecedência. Se for para um dia específico, avisa-nos."),
            ("Posso cancelar uma encomenda?", f"Sim, enquanto estiver em processamento: avisa-nos por e-mail ({c}). Se já tiver sido expedida, segue para entrega e podes recusar recebê-la."),
            ("Posso devolver um produto?", f"Sim. Tens 14 dias a partir do dia em que recebes a encomenda para a devolver, sem precisares de indicar o motivo. Os produtos têm de estar nas mesmas condições em que foram entregues, na embalagem original e sem sinais de uso. Pede o formulário de livre resolução ou escreve-nos ({c}). O reembolso, incluindo os portes pagos inicialmente, é feito pelo mesmo método de pagamento. Os detalhes estão na <a href=\"{LOJA}/page/politica-de-devolucao\"{NOVA}>Política de Devolução</a>."),
            ("E se o produto chegar com defeito?", f"Aceitamos trocas quando a encomenda chega com defeito, incompleta, incorreta ou com danos da entrega: escreve-nos ({c}). Se o artigo foi oferecido, a troca é feita com o talão de oferta."),
            ("Não encontro um produto. Conseguem encomendá-lo?", "Sempre que possível, sim. Fala connosco e verificamos a disponibilidade junto dos nossos distribuidores e as alternativas que existem."),
            ("Fazem pré-encomendas de figuras?", "De momento não temos um sistema de pré-encomendas para figuras. Se procuras uma figura específica, fala connosco: analisamos a disponibilidade e se há forma de a encomendar."),
            ("Vendem cartas soltas (Singles) ou compram coleções?", "Não. De momento não vendemos Singles, nem na loja nem online, e não compramos cartas individuais nem coleções."),
            ("Podem ajudar-me a escolher?", "Claro! Seja o teu primeiro TCG, a tua primeira figura ou um presente, ajudamos de acordo com o teu orçamento e os teus gostos. Passa pela loja ou fala connosco."),
            ("Ainda tenho dúvidas. Como vos contacto?", f"Escreve-nos ({c}), liga para o {TELEFONE} ou fala connosco no <a href=\"{CONVITE}\"{NOVA}>Discord</a>."),
        ]) + f'<p class="m small">Lê também a <a href="{LOJA}/page/politica-de-entrega"{NOVA}>Política de Entrega</a>, a <a href="{LOJA}/page/politica-de-devolucao"{NOVA}>Política de Devolução</a> e os <a href="{LOJA}/page/termos-e-condicoes"{NOVA}>Termos e Condições</a>.</p></section>')
    desc = ("Como comprar na Weatherlight, loja de hobby em Évora (Alentejo, Portugal): métodos de pagamento, envios por DHL para "
            "Portugal Continental, levantamento grátis na loja, devoluções e trocas.")
    perguntas = [("Quais são os métodos de pagamento?", "Cartão de crédito, Multibanco, MB WAY, PayPal, carteira digital e transferência bancária."),
                 ("Enviam para todo o país?", "Enviamos por DHL para Portugal Continental, com entrega até 2 dias úteis depois da expedição. Não enviamos para as ilhas."),
                 ("Posso levantar a encomenda na loja?", "Sim. Escolhe Levantamento em Loja: não pagas portes e levantas na loja em Évora, dentro do horário.")]
    ld = {"@context": "https://schema.org", "@graph": [ld_loja, {"@type": "FAQPage", "url": url, "inLanguage": "pt-PT",
          "mainEntity": [{"@type": "Question", "name": p, "acceptedAnswer": {"@type": "Answer", "text": r}} for p, r in perguntas]}]}
    escrever("primeira-compra/index.html", casca("Primeira compra na Weatherlight | Évora, Alentejo, Portugal", desc, url,
             cab_pagina("Primeira compra na Weatherlight", "Pagamentos, envios, levantamento em Évora e devoluções", "Primeira compra"), corpo, ld))
    return url


# ---------------- página: guia de produtos ----------------
GUIA = [
    ("TCG", "Trading Card Games", [
        ("Booster", "Embalagem selada com cartas de uma coleção. O conteúdo é aleatório e pode trazer cartas comuns, raras e versões especiais."),
        ("Booster Box / Display", "Caixa com vários Boosters da mesma coleção. Boa escolha para quem acompanha cada expansão ou quer mais hipóteses de encontrar cartas especiais."),
        ("Bundle", "Reúne vários Boosters numa só embalagem. A composição varia consoante o jogo e a coleção."),
        ("Starter Deck / Precon", "Deck pré-construído e pronto a jogar: a forma mais simples de começar um TCG sem construir um deck de raiz."),
        ("Promo", "Carta promocional distribuída em produtos especiais, eventos ou campanhas, muitas vezes com arte ou acabamento diferentes."),
    ], "Não precisas de saber jogar para colecionar: muita gente começa pelas ilustrações ou pelas personagens favoritas. E se quiseres jogar, os nossos eventos semanais são o sítio ideal para aprender."),
    ("Acessórios", "Acessórios", [
        ("Sleeves", "Capas que protegem cada carta. A maioria dos TCGs usa <strong>Standard Size</strong>; Yu-Gi-Oh! e outros jogos de cartas mais pequenas usam <strong>Japanese Size</strong>."),
        ("Inner Sleeves e Double Sleeving", "Uma sleeve fina (Perfect Fit) por baixo da sleeve normal, para uma proteção extra."),
        ("Outer Sleeves", "Protegem sleeves ilustradas oficiais, prolongando a sua vida durante o jogo."),
        ("Toploader e Magnetic Case", "Proteções rígidas para guardar e expor cartas mais valiosas. A carta entra primeiro numa sleeve."),
        ("Deckbox, Binder e Playmat", "Para transportar o deck, organizar a coleção em álbum e jogar sobre uma superfície que protege as cartas."),
    ], "Usa sempre sleeves iguais em todo o deck: sleeves diferentes podem tornar algumas cartas identificáveis durante o jogo."),
    ("Figuras", "Figuras de Anime", [
        ("Figuras oficiais", "Todas as figuras da Weatherlight são produtos oficiais, licenciados e de fabricantes autorizados."),
        ("Prize Figure", "Criadas originalmente como prémio nas máquinas japonesas. Ótima relação entre qualidade e preço, ideais para começar uma coleção."),
        ("Scale Figure", "Seguem uma escala definida (1/7, 1/8…), com mais detalhe e acabamentos mais elaborados."),
        ("Statue e figura articulada", "Uma statue é estática, feita para expor; uma figura articulada pode mudar de pose."),
        ("Vêm montadas?", "A maioria chega praticamente pronta a expor. Às vezes basta encaixar a base ou pequenas peças, sem ferramentas nem cola."),
    ], "Não fazemos pré-encomendas de figuras, mas se procuras uma em específico fala connosco: vemos se é possível encomendá-la."),
    ("Model Kits", "Model Kits", [
        ("Gunpla", "Os Model Kits de Gundam (Gundam + Plastic Model)."),
        ("EG, HG, RG e MG", "<strong>EG</strong> (Entry Grade) é ideal para começar; <strong>HG</strong> (High Grade) equilibra simplicidade e detalhe; <strong>RG</strong> (Real Grade) tem mais detalhe e é mais exigente; <strong>MG</strong> (Master Grade) são modelos maiores e mais complexos."),
        ("Snap-Fit", "Na maioria dos kits da Bandai as peças encaixam por pressão: não precisas de cola nem de pintar."),
        ("Ferramentas", "Para começar basta um alicate de corte (Nipper) para separar as peças e uma lima ou esponja abrasiva para as pequenas marcas."),
        ("Action Base", "Base articulada para expor o modelo em poses mais dinâmicas."),
    ], "Alguns kits fazem-se em cerca de uma hora; os mais detalhados podem levar várias sessões."),
    ("Miniaturas", "Miniaturas", [
        ("Gundam Assemble", "Jogo de miniaturas oficial do universo Gundam, da Bandai: cada jogador monta, pinta e comanda as suas unidades em batalhas táticas. Cada miniatura tem cerca de 5 cm."),
        ("Starter Set", "O produto de entrada, com tudo o que precisas para começar a jogar partidas de 3 contra 3."),
        ("Expansion Pack", "Três miniaturas e as respetivas cartas, para alargar a coleção e as opções de jogo."),
        ("Paint Pack", "Três miniaturas, um pincel e tintas, para quem quer começar a pintar."),
        ("Deluxe Set", "Para batalhas de 5 contra 5, com mais miniaturas, cenários com objetivos e unidades maiores, como naves de guerra."),
    ], "As miniaturas vêm por pintar (Unpainted), para as personalizares à tua maneira."),
    ("TTRPGs", "TTRPGs (Jogos Narrativos)", [
        ("TTRPG", "Jogo em que os participantes criam personagens e constroem uma história em conjunto, com regras e, muitas vezes, dados."),
        ("Dice Set", "Conjunto de dados poliédricos: d4, d6, d8, d10, d12 e d20 (o número é o de faces)."),
        ("One-Shot", "Aventura que começa e acaba numa só sessão: a melhor forma de experimentar um sistema novo."),
        ("Ficha de Personagem", "Onde registas as características, capacidades e equipamento da tua personagem."),
    ], "Nunca jogaste? Não precisas de decorar as regras: vê as sessões no calendário de eventos e aparece."),
    ("Blind Boxes", "Blind Boxes", [
        ("Blind Box", "Caixa fechada: só descobres que figura te saiu depois de a abrir. Não dá para escolher e podem sair repetidas."),
        ("Secret / Chase", "Figura mais rara que algumas coleções incluem no lugar de uma das regulares. Nem todas as séries têm."),
        ("Caixa completa (Display)", "Algumas trazem um conjunto das figuras regulares sem repetidos, outras continuam aleatórias. A Secret normalmente não é garantida."),
        ("Mini-Figure", "Refere-se ao tipo e tamanho da figura; Blind Box é a forma como é vendida."),
    ], "Vendemos as Blind Boxes seladas e não as abrimos, pesamos ou tentamos identificar antes da venda: a surpresa é igual para todos."),
    ("Bilhetes", "Bilhetes", [
        ("Bilhetes para eventos", "Alguns eventos especiais, como os Live Plays, têm bilhete à venda na loja online. Os detalhes de cada evento estão no calendário."),
    ], ""),
]


def guia(ld_loja):
    url = f"{BASE}/guia/"
    secs = []
    for chave, titulo, termos, nota in GUIA:
        ic, cor = ESTILO_TIPO.get(chave, ("", "var(--sea-2)"))
        extra = f'<p class="m small">{nota}</p>' if nota else ""
        curto = titulo.split(" (")[0]
        link = (f'<p class="ver"><a class="insc" href="{EVENTOS}/"{NOVA}>📅 Ver o calendário de eventos <span>↗</span></a></p>' if chave in ("Bilhetes", "TTRPGs")
                else f'<p class="ver"><a class="insc" href="/#{html.escape(chave)}">Ver as novidades de {curto} →</a></p>')
        secs.append(f'<section class="box faq guia" id="{ancora(chave)}"><h2><span class="ic" aria-hidden="true">{ic}</span>'
                    f'<span style="color:{cor}">{titulo}</span></h2>{faq(termos)}{extra}{link}</section>')
    indice = ('<nav class="help" aria-label="Categorias">' + "".join(
        f'<a href="#{ancora(c)}"><strong>{ESTILO_TIPO.get(c, ("",))[0]} {t.split(" (")[0]}</strong><span>{", ".join(x[0] for x in termos[:3])}</span></a>'
        for c, t, termos, _ in GUIA) + "</nav>")
    corpo = (indice + "\n" + "\n".join(secs) +
             f'\n<p class="m small">Falta algum termo? Vê o <a href="{GL}"{NOVA}>Glossário</a> ou a <a href="{CA}"{NOVA}>Central de Ajuda</a>, ou pergunta-nos na loja.</p>')
    desc = ("Guia de produtos da Weatherlight, em Évora (Alentejo, Portugal): Boosters e Displays, sleeves, Prize e Scale Figures, "
            "Gunpla HG, RG e MG, Gundam Assemble, TTRPGs e Blind Boxes explicados de forma simples.")
    ld = {"@context": "https://schema.org", "@graph": [ld_loja, {"@type": "WebPage", "name": "Guia de produtos — Weatherlight", "url": url,
          "inLanguage": "pt-PT", "about": {"@id": ld_loja["@id"]}}]}
    escrever("guia/index.html", casca("Guia de produtos: o que estou a comprar? | Weatherlight, Évora", desc, url,
             cab_pagina("O que estou a comprar?", "Os produtos da Weatherlight explicados por categoria", "Guia de produtos"), corpo, ld))
    return url


# ---------------- página principal ----------------
def gerar():
    dados = carregar()
    for d in dados: d["tipo"] = tipo(d["nome"])  # regras novas aplicam-se também aos produtos antigos
    limite = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DIAS_PAGINA)
    vis = [d for d in dados if dt.datetime.fromisoformat(d["data"]).astimezone(dt.timezone.utc) >= limite]
    grupos, ordem = {}, []
    for d in vis:
        k = lisboa(d["data"]).date()
        if k not in grupos: grupos[k] = []; ordem.append(k)
        grupos[k].append(d)
    presentes = [t for t in ORDEM if any(d["tipo"] == t for d in vis)]
    filtros = ('<div class="flt"><p class="flt-t">Filtra por categoria <span>· podes escolher várias</span></p>'
               '<div class="filters" role="group" aria-label="Filtrar por categoria (podes escolher várias)">'
               '<button type="button" class="f f-all" data-t="all" aria-pressed="true"><img src="/logos/wl.webp" alt="" width="139" height="160">Todas</button>'
               + "".join(f'<button type="button" class="f" data-t="{html.escape(t)}" aria-pressed="false" style="--gc:{ESTILO_TIPO[t][1]}">'
                         f'<span class="ic" aria-hidden="true">{ESTILO_TIPO[t][0]}</span>{html.escape(t)}</button>' for t in presentes)
               + '</div></div>')

    def card(d):
        fs = fotos(d); alt = html.escape(d["nome"]); u = html.escape(d["url"])
        img = "".join(f'<img src="{html.escape(quadrado(x))}" alt="{alt if i == 0 else ""}" loading="lazy"{" class=on" if i == 0 else ""}>'
                      for i, x in enumerate(fs)) or '<i></i>'
        if len(fs) > 1: img += '<b class="dots">' + "<u></u>" * len(fs) + "</b>"
        cor = ESTILO_TIPO.get(d["tipo"], ("", "var(--muted)"))[1]
        return (f'<article class="np" data-t="{html.escape(d["tipo"])}">'
                f'<a class="phl" href="{u}"{NOVA} tabindex="-1" aria-hidden="true"><span class="ph{" sl" if len(fs) > 1 else ""}">{img}</span></a>'
                f'<span class="tg"><span class="chip" style="color:{cor}">{html.escape(d["tipo"])}</span></span>'
                f'<a class="nm" href="{u}"{NOVA}><strong>{alt}</strong></a>'
                f'<span class="price">{preco(d.get("preco"))}</span>'
                f'<a class="insc" href="{u}"{NOVA}>Ver na loja <span>↗</span></a></article>')

    blocos = "".join(
        f'<section class="dia"><h2><span>{SEM[k.weekday()].capitalize()}</span> <small>{k.day} de {MES[k.month - 1]}</small></h2>'
        f'<div class="grid">{"".join(card(d) for d in grupos[k])}</div></section>' for k in ordem)
    if not blocos:
        blocos = '<section class="box"><p class="m">As novidades aparecem aqui assim que chegam à loja online.</p></section>'
    url = f"{BASE}/"
    ld_loja = loja_ld(); ld_loja["@id"] = LOJA + "/#loja"
    end = ld_loja.get("address", {})
    desc = ("Novidades da Weatherlight, loja de hobby em Évora (Alentejo, Portugal): Trading Card Games, acessórios, figuras de anime, "
            "Model Kits, miniaturas, TTRPGs, blind boxes e peluches acabados de chegar. Atualizado de hora a hora.")
    og = next((quadrado(fotos(d)[0]) for d in vis if fotos(d)), "")

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
    cab = (f'<header class="home">\n  <div class="wrap">\n    <span class="eyebrow">Atualizado de hora a hora · Évora</span>\n'
           f'    <h1>Novidades <em>Weatherlight</em></h1>\n'
           f'    <p class="sub">Os produtos novos da Weatherlight, a tua loja de hobby em Évora, no Alentejo</p>\n'
           f'    <p class="lede">Trading Card Games, Acessórios, Figuras de Anime, Model Kits, Miniaturas, TTRPGs, Blind Boxes e Peluches: tudo o que chega à Weatherlight aparece agora aqui, no próprio dia. Encontras na nossa <a href="{LOJA}/"{NOVA}>loja online</a> e na loja física em Évora.</p>\n'
           f'    <div class="info"><span>{html.escape(end.get("streetAddress", ""))}, {html.escape(end.get("postalCode", ""))} Évora</span><span>{TELEFONE}</span>'
           f'<a href="{LOJA}/"{NOVA}>Loja online</a><a href="{INSTAGRAM}"{NOVA}>Instagram</a><a href="{TIKTOK}"{NOVA}>TikTok</a>'
           f'<a href="{DISCORD}"{NOVA}>🔔 Alertas no Discord</a><a href="{EVENTOS}/"{NOVA}>📅 Eventos</a></div>\n  </div>\n</header>')
    ajuda = (f'<nav class="help" aria-label="Ajuda para as primeiras compras">\n'
             f'      <a href="/primeira-compra/"><strong>Primeira compra online?</strong><span>Pagamentos, envios, levantamento em Évora e devoluções</span></a>\n'
             f'      <a href="/guia/"><strong>O que estou a comprar?</strong><span>Booster, Display, Prize Figure, HG ou RG… explicado por categoria</span></a>\n'
             f'      <a href="{GL}"{NOVA}><strong>Não conheces algum termo?</strong><span>Sleeves, Secret, Snap-Fit, Grading… está tudo no Glossário</span></a>\n'
             f'    </nav>')
    subs = (f'<section class="subs" id="alertas"><div class="subs-c">\n'
            f'      <img class="subs-aqua" src="/img/ola.webp" alt="" width="351" height="360">\n'
            f'      <div class="subs-t"><h2>Sabe primeiro o que chega</h2>\n'
            f'      <p>Ativa as notificações do canal ✨│novidades-wl no nosso Discord: cada produto novo é anunciado assim que chega à loja online.</p>\n'
            f'      <p class="subs-l"><a href="{DISCORD}"{NOVA}>🔔 Canal de novidades no Discord</a><a href="{INSTAGRAM}"{NOVA}>📸 Instagram</a><a href="{url}feed.xml">RSS</a></p></div></div></section>')
    corpo = f"    {ajuda}\n    {filtros}\n    {blocos}\n    {subs}"
    open(os.path.join(RAIZ, "index.html"), "w").write(
        casca("Novidades Weatherlight | Évora, Alentejo, Portugal", desc, url, cab, corpo, ld, og, JS_FOTOS + JS_FILTROS))
    urls = [url, primeira_compra(ld_loja), guia(ld_loja)]
    json.dump({"name": "Novidades Weatherlight", "short_name": "Novidades WL", "start_url": "/", "display": "standalone",
               "background_color": "#ffffff", "theme_color": "#ffffff", "lang": "pt-PT",
               "icons": [{"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"}]},
              open(os.path.join(RAIZ, "manifest.webmanifest"), "w"), ensure_ascii=False, indent=1)
    itens = "".join(
        f"<item><title>{html.escape(d['nome'])}</title><link>{html.escape(d['url'])}</link><guid>{html.escape(d['url'])}</guid>"
        f"<pubDate>{format_datetime(dt.datetime.fromisoformat(d['data']).astimezone(dt.timezone.utc))}</pubDate>"
        f"<category>{html.escape(d['tipo'])}</category>"
        f"<description>{html.escape(preco(d.get('preco')) + (('<br><img src=' + chr(34) + d['imagem'] + chr(34) + '>') if d.get('imagem') else ''))}</description></item>"
        for d in dados[:60])
    open(os.path.join(RAIZ, "feed.xml"), "w").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Novidades Weatherlight</title>'
        f"<link>{url}</link><description>{html.escape(desc)}</description><language>pt-PT</language>{itens}</channel></rss>\n")
    hoje = dt.date.today().isoformat()
    open(os.path.join(RAIZ, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{hoje}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(RAIZ, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    open(os.path.join(RAIZ, "llms.txt"), "w").write(
        f"# Novidades Weatherlight\n\n> Produtos que acabaram de chegar à Weatherlight Games & Collectibles, loja de hobby em Évora "
        f"(Alentejo, Portugal): Trading Card Games, acessórios, figuras de anime, Model Kits, miniaturas, TTRPGs, blind boxes e peluches. Atualizado de hora a hora.\n\n"
        f"- [Novidades Weatherlight]({url})\n- [Primeira compra: pagamentos, envios, levantamento e devoluções]({BASE}/primeira-compra/)\n"
        f"- [Guia de produtos por categoria]({BASE}/guia/)\n- [Feed RSS]({url}feed.xml)\n- [Loja online]({LOJA}/)\n- [Calendário de eventos]({EVENTOS}/)\n\n"
        "## Últimas novidades\n\n" + "".join(f"- [{d['nome']}]({d['url']}) · {preco(d.get('preco'))}\n" for d in vis[:40]))
    return url


if __name__ == "__main__":
    import sys
    if "--sincronizar" in sys.argv: sincronizar()
    print(gerar())
