# -*- coding: utf-8 -*-
"""
G20 Fundos · LOGOS DAS GESTORAS (out/2026)
Baixa uma vez o ícone oficial do site de cada gestora e guarda em OUT/logos/,
para o G20 Hub mostrar o logo no selo do fundo sem chamar nenhum site de fora.
Bancos (Itaú, Bradesco, BB, Caixa, Santander, BTG, XP, Inter, Nubank, Safra...)
não entram aqui: a plataforma já tem os logos deles em assets/bancos/.

Ordem de busca por gestora: apple-touch-icon do site, ícones declarados na
página inicial (o maior), favicon.ico, e por último o serviço de ícones do
Google (só o endereço da gestora vai no pedido). Fica o que tiver 64 px ou mais.
Saída: logos/{chave}.png (128x128, fundo transparente) e logos/indice.json:
  { "chave": { "n": "Nome", "termos": ["TEXTO DO GESTOR NA CVM", ...], "fundo": "claro"|"escuro" } }
"""
import io, json, os, re, sys, time, urllib.request, urllib.parse
from PIL import Image

OUT = os.environ.get('OUT', 'pub')
PASTA = os.path.join(OUT, 'logos')
UA = 'Mozilla/5.0 (G20 Fundos; logos)'

# chave: (nome, site, [termos que aparecem no nome do gestor na CVM])
GESTORAS = {
  'alaska': ('Alaska', 'alaska-asset.com.br', ['ALASKA']),
  'verde': ('Verde Asset', 'www.verdeasset.com.br', ['VERDE ASSET']),
  'spx': ('SPX', 'spxcapital.com.br', ['SPX ']),
  'kapitalo': ('Kapitalo', 'kapitalo.com.br', ['KAPITALO']),
  'dynamo': ('Dynamo', 'dynamo.com.br', ['DYNAMO']),
  'kinea': ('Kinea', 'kinea.com.br', ['KINEA']),
  'arx': ('ARX', 'arxinvestimentos.com.br', ['ARX INVEST']),
  'azquest': ('AZ Quest', 'azquest.com.br', ['AZ QUEST']),
  'absolute': ('Absolute', 'absoluteinvestimentos.com.br', ['ABSOLUTE ']),
  'ibiuna': ('Ibiuna', 'ibiuna.com.br', ['IBIUNA']),
  'legacy': ('Legacy', 'legacycapital.com.br', ['LEGACY CAPITAL']),
  'jgp': ('JGP', 'jgp.com.br', ['JGP ']),
  'vinci': ('Vinci', 'vincipartners.com', ['VINCI ']),
  'patria': ('Patria', 'patria.com', ['PATRIA ', 'PÁTRIA ']),
  'sparta': ('Sparta', 'sparta.com.br', ['SPARTA']),
  'hashdex': ('Hashdex', 'hashdex.com', ['HASHDEX']),
  'franklin': ('Franklin Templeton', 'franklintempleton.com.br', ['FRANKLIN TEMPLETON']),
  'bnpparibas': ('BNP Paribas', 'bnpparibas-am.com', ['BNP PARIBAS']),
  'mapfre': ('Mapfre', 'mapfre.com.br', ['MAPFRE']),
  'sulamerica': ('SulAmérica', 'sulamericainvestimentos.com.br', ['SUL AMÉRICA', 'SUL AMERICA', 'SULAMÉRICA', 'SULAMERICA']),
  'portoseguro': ('Porto Seguro', 'portoseguro.com.br', ['PORTO SEGURO', 'PORTO ASSET']),
  'icatu': ('Icatu', 'icatu.com.br', ['ICATU']),
  'brasilprev': ('Brasilprev', 'brasilprev.com.br', ['BRASILPREV']),
  'empiricus': ('Empiricus', 'empiricus.com.br', ['EMPIRICUS']),
  'artesanal': ('Artesanal', 'artesanalinvestimentos.com.br', ['ARTESANAL']),
  'riza': ('Riza', 'rizaasset.com.br', ['RIZA ']),
  'v8': ('V8 Capital', 'v8capital.com.br', ['V8 CAPITAL']),
  'plural': ('Plural', 'plural.com.br', ['PLURAL ']),
  'realinvestor': ('Real Investor', 'realinvestor.com.br', ['REAL INVESTOR']),
  'tivio': ('Tivio', 'tivio.com.br', ['TIVIO']),
  'capitania': ('Capitânia', 'capitaniainvestimentos.com.br', ['CAPITÂNIA', 'CAPITANIA']),
  'trigono': ('Trígono', 'trigonocapital.com', ['TRÍGONO', 'TRIGONO']),
  'bocaina': ('Bocaina', 'bocainacapital.com.br', ['BOCAINA']),
  'genial': ('Genial', 'genialinvestimentos.com.br', ['GENIAL ']),
  'warren': ('Warren', 'warren.com.br', ['WARREN ']),
  'orama': ('Órama', 'orama.com.br', ['ÓRAMA', 'ORAMA ']),
  'guepardo': ('Guepardo', 'guepardoinvestimentos.com.br', ['GUEPARDO']),
  'atmos': ('Atmos', 'atmoscapital.com.br', ['ATMOS ']),
  'dahlia': ('Dahlia', 'dahliacapital.com.br', ['DAHLIA']),
  'truxt': ('Truxt', 'truxt.com.br', ['TRUXT']),
  'oceana': ('Oceana', 'oceanainvestimentos.com.br', ['OCEANA']),
  'squadra': ('Squadra', 'squadrainvest.com.br', ['SQUADRA']),
  'stk': ('STK Capital', 'stkcapital.com.br', ['STK CAPITAL']),
  'quantitas': ('Quantitas', 'quantitas.com.br', ['QUANTITAS']),
  'gavea': ('Gávea', 'gaveainvest.com.br', ['GÁVEA', 'GAVEA ']),
  'bahia': ('Bahia Asset', 'bahiaasset.com.br', ['BAHIA AM', 'BAHIA ASSET']),
  'armor': ('Armor Capital', 'armorcapital.com.br', ['ARMOR CAPITAL']),
  'adam': ('Adam Capital', 'adamcapital.com.br', ['ADAM CAPITAL']),
  'asa': ('ASA', 'asa.com.br', ['ASA HEDGE', 'ASA INVEST', 'ASA ASSET']),
  'canvas': ('Canvas', 'canvascapital.com.br', ['CANVAS CAPITAL']),
  'garde': ('Garde', 'gardeasset.com.br', ['GARDE ']),
  'navi': ('Navi', 'navi.com.br', ['NAVI CAPITAL']),
  'opportunity': ('Opportunity', 'opportunity.com.br', ['OPPORTUNITY']),
  'sharp': ('Sharp Capital', 'sharpcapital.com.br', ['SHARP CAPITAL']),
  'rps': ('RPS Capital', 'rpscapital.com.br', ['RPS CAPITAL']),
  'ipcapital': ('IP Capital', 'ipcapitalpartners.com', ['IP CAPITAL', 'IP GESTÃO', 'IP GESTAO']),
  'moat': ('Moat', 'moatcapital.com.br', ['MOAT CAPITAL']),
  'constellation': ('Constellation', 'constellation.com.br', ['CONSTELLATION']),
  'occam': ('Occam', 'occambrasil.com.br', ['OCCAM']),
  'carbon': ('Carbon', 'carbonasset.com.br', ['CARBON ASSET']),
  'amw': ('AMW', 'amw.com.br', ['AMW ASSET']),
  'leto': ('Leto', 'letoasset.com', ['LETO ']),
  'zurich': ('Zurich', 'zurich.com.br', ['ZURICH']),
  'prudential': ('Prudential', 'prudential.com.br', ['PRUDENTIAL']),
  'western': ('Western Asset', 'westernasset.com.br', ['WESTERN ASSET']),
  'jpmorgan': ('J.P. Morgan', 'jpmorgan.com', ['J.P. MORGAN', 'JP MORGAN', 'JPMORGAN']),
  'blackrock': ('BlackRock', 'blackrock.com', ['BLACKROCK']),
  'schroder': ('Schroders', 'schroders.com', ['SCHRODER']),
  'credit_suisse': ('UBS', 'ubs.com', ['CREDIT SUISSE', 'UBS ']),
  'bnb': ('Banco do Nordeste', 'bnb.gov.br', ['BANCO DO NORDESTE']),
  'banestes': ('Banestes', 'banestes.com.br', ['BANESTES']),
  'btg_pactual_digital': ('Nu Asset', 'nuasset.com.br', ['NU ASSET']),
  'rio_bravo': ('Rio Bravo', 'riobravo.com.br', ['RIO BRAVO']),
  'tork': ('Tork', 'torkcapital.com.br', ['TORK CAPITAL']),
  'neo': ('Neo Investimentos', 'neoinvestimentos.com.br', ['NEO GEST', 'NEO INVEST']),
  'polo': ('Polo Capital', 'polocapital.com', ['POLO CAPITAL']),
  'vokin': ('Vokin', 'vokin.com.br', ['VOKIN']),
  'mauá': ('Mauá Capital', 'mauacapital.com', ['MAUÁ CAPITAL', 'MAUA CAPITAL']),
}

def baixar(url, limite=3_000_000):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=12) as r:
        return r.read(limite), r.headers.get('Content-Type', ''), r.geturl()

def imagem(dados):
    try:
        im = Image.open(io.BytesIO(dados))
        if getattr(im, 'n_frames', 1) > 1 or im.format == 'ICO':
            try:
                tamanhos = sorted(im.info.get('sizes', []) or [im.size], key=lambda s: s[0] * s[1])
                im.size = tamanhos[-1]
            except Exception:
                pass
        im.load()
        return im.convert('RGBA')
    except Exception:
        return None

def candidatos(site):
    base = 'https://' + site
    out = [base + '/apple-touch-icon.png', base + '/apple-touch-icon-precomposed.png']
    try:
        try:
            html, _, final = baixar(base + '/', 800_000)
        except Exception:
            html, _, final = baixar('https://' + (site[4:] if site.startswith('www.') else 'www.' + site) + '/', 800_000)
        html = html.decode('utf-8', 'ignore')
        links = re.findall(r'<link[^>]+>', html, re.I)
        achados = []
        for l in links:
            rel = re.search(r'rel=["\']([^"\']+)', l, re.I)
            href = re.search(r'href=["\']([^"\']+)', l, re.I)
            if not rel or not href or 'icon' not in rel.group(1).lower(): continue
            tam = re.search(r'sizes=["\'](\d+)x\d+', l, re.I)
            achados.append((int(tam.group(1)) if tam else (180 if 'apple' in rel.group(1).lower() else 32), urllib.parse.urljoin(final, href.group(1))))
        achados.sort(reverse=True)
        out = [u for _, u in achados if not u.lower().endswith('.svg')] + out
    except Exception as e:
        print('   página inicial falhou:', e)
    nu = site[4:] if site.startswith('www.') else 'www.' + site
    out += [base + '/favicon.ico', 'https://' + nu + '/apple-touch-icon.png', 'https://' + nu + '/favicon.ico',
            'https://www.google.com/s2/favicons?domain=' + site + '&sz=256', 'https://icons.duckduckgo.com/ip3/' + site.replace('www.', '') + '.ico']
    vistos, lim = set(), []
    for u in out:
        if u not in vistos: vistos.add(u); lim.append(u)
    return lim

def luminancia(im):
    px = [p for p in im.resize((32, 32)).getdata() if p[3] > 40]
    if not px: return 0.5
    return sum((0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 for r, g, b, a in px) / len(px)

def principal():
    os.makedirs(PASTA, exist_ok=True)
    ind_path = os.path.join(PASTA, 'indice.json')
    try: indice = json.load(open(ind_path, encoding='utf-8'))
    except Exception: indice = {}
    refazer = os.environ.get('REFAZER') == '1'
    # gestora cujo site não entregou ícone: tenta de novo só depois de 7 dias (o robô roda todo dia)
    fal_path = os.path.join(PASTA, 'falhas.json')
    try: falhas = json.load(open(fal_path, encoding='utf-8'))
    except Exception: falhas = {}
    hoje = time.strftime('%Y-%m-%d')
    def recente(d):
        try: return (time.mktime(time.strptime(hoje, '%Y-%m-%d')) - time.mktime(time.strptime(d, '%Y-%m-%d'))) < 7 * 86400
        except Exception: return False
    ok = falhou = 0
    for chave, (nome, site, termos) in GESTORAS.items():
        arq = os.path.join(PASTA, chave + '.png')
        if not refazer and chave in indice and os.path.exists(arq):
            indice[chave]['termos'] = termos; indice[chave]['n'] = nome
            continue
        if not refazer and chave in falhas and recente(falhas[chave]):
            continue
        melhor = None
        for u in candidatos(site):
            if 'wp-includes' in u or 'w-logo' in u: continue
            try:
                dados, tipo, _ = baixar(u)
            except Exception:
                continue
            im = imagem(dados)
            if not im or min(im.size) < 48: continue
            if not melhor or im.size[0] > melhor[0].size[0]:
                melhor = (im, u)
            if im.size[0] >= 128: break
        if not melhor:
            print('✗', chave, site); falhou += 1; indice.pop(chave, None); falhas[chave] = hoje; continue
        im, u = melhor
        im = im.resize((128, 128), Image.LANCZOS)
        im.save(arq, 'PNG', optimize=True)
        lum = luminancia(im)
        indice[chave] = { 'n': nome, 'termos': termos, 'fundo': 'escuro' if lum > 0.62 else 'claro', 'fonte': u.split('/')[2] }
        print('✓', chave, im.size, u, round(lum, 2)); ok += 1
        time.sleep(0.3)
    for k in list(indice.keys()):
        if k not in GESTORAS:
            indice.pop(k, None)
            try: os.remove(os.path.join(PASTA, k + '.png'))
            except OSError: pass
    json.dump(indice, open(ind_path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    json.dump({k: v for k, v in falhas.items() if k in GESTORAS and k not in indice}, open(fal_path, 'w', encoding='utf-8'))
    print('logos novos: %d, falharam: %d, no índice: %d' % (ok, falhou, len(indice)))

if __name__ == '__main__':
    principal()
