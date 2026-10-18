"""Genera workflow.json: la plantilla de n8n «Tendencias de la semana».

Cada lunes a las 8:30 lee GitHub (repos nuevos con más estrellas), Hacker News (lo más votado), Hugging Face (modelos en
tendencia) y varios blogs por RSS; un modelo de OpenAI elige las 5 tendencias más relevantes y te las manda por Telegram
con un resumen en español. Solo nodos oficiales de n8n.

Uso: python generate_workflow.py   (escribe workflow.json; impórtalo en n8n con «Import from file»)
Para cambiar fuentes, horario, modelo o idioma, edita las constantes de abajo y vuelve a generarlo.
"""
import json
import pathlib
import uuid

HORARIO = '30 8 * * 1'                       # cron: lunes a las 8:30
ZONA = 'Europe/Madrid'
MODELO = 'gpt-5.4-mini'                      # cualquier modelo de chat de OpenAI
CHAT_ID = 'TU_CHAT_ID'                       # tu chat de Telegram (habla con @userinfobot para saberlo)
TEMAS = 'inteligencia artificial, automatización, marketing digital, desarrollo web y apps'
RSS = [
    ('OpenAI', 'https://openai.com/news/rss.xml'),
    ('Hugging Face blog', 'https://huggingface.co/blog/feed.xml'),
    ('GitHub blog', 'https://github.blog/feed/'),
    ('TechCrunch IA', 'https://techcrunch.com/category/artificial-intelligence/feed/'),
    ('Search Engine Journal', 'https://www.searchenginejournal.com/feed/'),
]
UA = 'n8n-weekly-trends'


class Flujo:
    def __init__(self, nombre):
        self.nombre, self.nodos, self.conns = nombre, [], {}

    def nodo(self, nombre, tipo, version, params, pos, **extra):
        n = {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, f'n8n-weekly-trends/{nombre}')), 'name': nombre, 'type': tipo,
             'typeVersion': version, 'position': pos, 'parameters': params, **extra}
        self.nodos.append(n)
        return nombre

    def unir(self, a, b, salida=0, tipo='main', entrada=0):
        c = self.conns.setdefault(a, {}).setdefault(tipo, [])
        while len(c) <= salida:
            c.append([])
        c[salida].append({'node': b, 'type': tipo, 'index': entrada})

    def http(self, nombre, url, pos, cabeceras=None):
        h = {'User-Agent': UA, **(cabeceras or {})}
        return self.nodo(nombre, 'n8n-nodes-base.httpRequest', 4.2, {
            'url': url, 'sendHeaders': True,
            'headerParameters': {'parameters': [{'name': k, 'value': v} for k, v in h.items()]},
            'options': {'timeout': 30000}}, pos, onError='continueRegularOutput', alwaysOutputData=True)


NORMALIZAR = r"""// Todas las fuentes al mismo formato: { fuente, titulo, enlace, senal, puntos, resumen }. Solo los últimos 8 días.
const limite = Date.now() - 8 * 86400000;
const host = u => (String(u || '').match(/^https?:\/\/([^\/?#]+)/i) || [])[1] || '';
const salida = [];
const push = o => { if (o.titulo && o.enlace) salida.push({ json: o }); };
for (const it of $input.all()) {
  const j = it.json || {};
  if (Array.isArray(j.hits)) {
    for (const h of j.hits) push({ fuente: 'Hacker News', titulo: h.title, enlace: h.url || `https://news.ycombinator.com/item?id=${h.objectID}`,
      senal: `${h.points} puntos en Hacker News`, puntos: Number(h.points) || 0, resumen: '' });
  } else if (Array.isArray(j.items) && j.total_count !== undefined) {
    for (const r of j.items) push({ fuente: 'GitHub', titulo: `${r.full_name}: ${r.description || ''}`.slice(0, 200), enlace: r.html_url,
      senal: `${r.stargazers_count} estrellas en GitHub`, puntos: Math.round((Number(r.stargazers_count) || 0) / 10), resumen: r.language || '' });
  } else if (j.id && j.likes !== undefined && j.downloads !== undefined) {
    push({ fuente: 'Hugging Face', titulo: `Modelo ${j.id} (${j.pipeline_tag || 'IA'})`, enlace: `https://huggingface.co/${j.id}`,
      senal: `${j.likes} me gusta en Hugging Face`, puntos: Number(j.trendingScore) || 0, resumen: '' });
  } else if (j.link && j.title) {
    const fecha = new Date(j.isoDate || j.pubDate || 0);
    if (isNaN(fecha) || fecha.getTime() < limite) continue;
    push({ fuente: host(j.link).replace(/^www\./, ''), titulo: String(j.title).trim(), enlace: j.link, senal: '', puntos: 30,
      resumen: String(j.contentSnippet || '').replace(/\s+/g, ' ').slice(0, 250) });
  }
}
return salida;"""

LISTA = r"""// Las mejores de cada fuente en un solo texto numerado (una única llamada al modelo).
const porFuente = {};
for (const x of $input.all().map(i => i.json)) (porFuente[x.fuente] = porFuente[x.fuente] || []).push(x);
const lista = [];
for (const f of Object.keys(porFuente)) lista.push(...porFuente[f].sort((a, b) => b.puntos - a.puntos).slice(0, 12));
if (!lista.length) return [];
const texto = lista.map((n, i) => `${i}. [${n.fuente}${n.senal ? ' · ' + n.senal : ''}] ${n.titulo} — ${n.enlace}${n.resumen ? ' — ' + n.resumen : ''}`).join('\n');
return [{ json: { texto } }];"""


def generar():
    f = Flujo('Tendencias de la semana')
    f.nodo('Nota', 'n8n-nodes-base.stickyNote', 1, {'width': 620, 'height': 260, 'content':
        '## Tendencias de la semana\nCada lunes lee GitHub, Hacker News, Hugging Face y varios blogs, y un modelo de OpenAI elige '
        'las 5 tendencias más relevantes y te las manda por Telegram.\n\n**Antes de activarlo:**\n1. Credencial **OpenAI** en «Modelo».\n'
        '2. Credencial **Telegram** en «Enviar a Telegram» y tu **chat ID** en el campo Chat ID.\n3. Pulsa «Probar a mano».'},
           [-320, -460])
    f.nodo('Cada lunes', 'n8n-nodes-base.scheduleTrigger', 1.2, {'rule': {'interval': [{'field': 'cronExpression', 'expression': HORARIO}]}}, [0, 200])
    f.nodo('Probar a mano', 'n8n-nodes-base.manualTrigger', 1, {}, [0, 400])
    fuentes = [
        f.http('Hacker News', "=https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=60&numericFilters=points%3E120,created_at_i%3E{{ Math.floor(Date.now() / 1000) - 7 * 86400 }}", [260, -120]),
        f.http('GitHub', "=https://api.github.com/search/repositories?q=created:%3E{{ new Date(Date.now() - 14 * 86400000).toISOString().slice(0, 10) }}&sort=stars&order=desc&per_page=30", [260, 0], {'Accept': 'application/vnd.github+json'}),
        f.http('Hugging Face', 'https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=25', [260, 120]),
    ]
    for i, (nombre, url) in enumerate(RSS):
        fuentes.append(f.nodo(f'RSS {nombre}', 'n8n-nodes-base.rssFeedRead', 1.2, {'url': url, 'options': {}}, [260, 240 + i * 110],
                              onError='continueRegularOutput', alwaysOutputData=True))
    f.nodo('Unir fuentes', 'n8n-nodes-base.merge', 3.2, {'mode': 'append', 'numberInputs': len(fuentes)}, [560, 200])
    for i, n in enumerate(fuentes):
        f.unir('Cada lunes', n)
        f.unir('Probar a mano', n)
        f.unir(n, 'Unir fuentes', 0, 'main', i)
    f.nodo('Normalizar', 'n8n-nodes-base.code', 2, {'jsCode': NORMALIZAR}, [780, 200])
    f.nodo('Preparar lista', 'n8n-nodes-base.code', 2, {'jsCode': LISTA}, [1000, 200])
    f.nodo('Elegir tendencias', '@n8n/n8n-nodes-langchain.chainLlm', 1.7, {
        'promptType': 'define', 'text': '={{ $json.texto }}', 'hasOutputParser': False,
        'messages': {'messageValues': [{'type': 'SystemMessagePromptTemplate', 'message':
            f'Eres un editor que sigue de cerca {TEMAS}. De la lista numerada de esta semana, elige las 5 tendencias más relevantes '
            'y útiles (prefiere lanzamientos, herramientas nuevas y proyectos que se puedan usar; descarta rumores, finanzas y '
            'polémicas). Escribe en español, en texto plano para Telegram (sin Markdown ni emojis), con este formato para cada una:\n'
            '1. Título claro\nPor qué importa, en 2 frases, sin inventar nada que no esté en la lista.\nEnlace\n\n'
            'Termina con una línea: «La que más me interesa esta semana: …» y por qué, en una frase.'}]}}, [1220, 200])
    f.nodo('Modelo', '@n8n/n8n-nodes-langchain.lmChatOpenAi', 1.2, {
        'model': {'__rl': True, 'mode': 'id', 'value': MODELO}, 'options': {'maxTokens': 1500}}, [1220, 420])
    f.unir('Modelo', 'Elegir tendencias', 0, 'ai_languageModel')
    f.nodo('Enviar a Telegram', 'n8n-nodes-base.telegram', 1.2, {
        'chatId': CHAT_ID, 'text': "={{ 'Tendencias de la semana\\n\\n' + $json.text }}",
        'additionalFields': {'appendAttribution': False, 'disable_web_page_preview': True}}, [1440, 200])
    f.unir('Unir fuentes', 'Normalizar')
    f.unir('Normalizar', 'Preparar lista')
    f.unir('Preparar lista', 'Elegir tendencias')
    f.unir('Elegir tendencias', 'Enviar a Telegram')
    return {'name': f.nombre, 'nodes': f.nodos, 'connections': f.conns, 'active': False,
            'settings': {'executionOrder': 'v1', 'timezone': ZONA}, 'pinData': {}}


if __name__ == '__main__':
    destino = pathlib.Path(__file__).with_name('workflow.json')
    destino.write_text(json.dumps(generar(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Escrito {destino.name}')
