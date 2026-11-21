# novidades.weatherlightgames.pt

Site "Novidades Weatherlight" da Weatherlight Games & Collectibles (Évora, Alentejo, Portugal) e bot que anuncia os produtos novos no Discord.

## Como funciona
- De hora a hora (ao minuto 17) o workflow **Novidades** (`.github/workflows/novidades.yml`) corre `bot/novidades.py`:
  lê o sitemap da loja (www.weatherlightgames.pt), compara com `bot/vistos.json` e, se houver produtos novos,
  anuncia-os no canal ✨│novidades-wl do Discord (segredo `DISCORD_WEBHOOK`) e junta-os a `dados.json`.
- Depois `bot/pagina.py` gera o site: `index.html`, `feed.xml` (RSS), `sitemap.xml`, `robots.txt` e `llms.txt`.
  O workflow faz commit para `main` e o GitHub Pages publica sozinho.
- A página mostra as últimas 6 semanas, por dia de chegada, com filtros por tipo (o tipo sai do nome do produto:
  lista `TIPOS` em `bot/pagina.py`). Fotos: a 1.ª do site primeiro; as outras passam com o cursor (computador) ou com o dedo (telemóvel).

## À mão (Actions → Novidades → Run workflow)
- `teste`: URLs de produtos para anunciar já no Discord (e juntar ao site).
- `adicionar`: URLs para juntar só ao site, sem anunciar.

## Ficheiros fixos
- `CNAME` (`novidades.weatherlightgames.pt`) e `.nojekyll`: têm de ficar sempre.
- `bot/estilo.html`: fontes e estilos copiados do calendário de eventos (repositório `calendario`). Se o visual do calendário mudar, copiar de novo.
- `bot/loja.json`: dados da loja para o Google (morada, telefone, horário, redes). Atualizar se algum destes mudar.
- `nuvens.jpg`, `favicon-32.png`, `apple-touch-icon.png`: imagens do cabeçalho e ícones.
