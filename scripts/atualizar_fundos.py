# -*- coding: utf-8 -*-
"""
G20 Fundos · ROBÔ DIÁRIO (Fase 1)
Baixa os dados abertos da CVM e publica arquivos leves para o G20 Hub.

Saídas (pasta OUT, publicada no GitHub Pages do g20-fundos):
  meta.json                 data da atualização, última data de cota, contagens
  ultimas.json              última cota de todos os fundos: {chave: [data, cota, pl, cotistas, captacao_liquida_12m]}
  indice.json               busca: fundos com cota nos últimos 13 meses
  indice-encerrados.json    busca: fundos sem cota recente (encerrados, incorporados), com histórico mensal
  diario/{p}.json           cotas diárias dos últimos 13 meses, por prefixo de 3 caracteres do CNPJ
                            {"b": "AAAA-MM-DD", "f": {chave: [[dias_desde_b, "cota"], ...]}}
  mensal/{p}.json           fim de cada mês desde 2010: {chave: [["AAAA-MM", "cota", pl, cotistas], ...]}
  historico/{chave}.json    diário completo (desde 2000) só dos fundos acompanhados
                            {"k": chave, "b": "2000-01-01", "q": [[dias_desde_b, "cota"], ...]}
  eventos.json              saltos anormais de cota e fundos acompanhados encerrados (para revisão no admin)

Chave do fundo: CNPJ só com letras e números (preparado para o CNPJ alfanumérico),
mais "_" + ID da subclasse quando houver. Ex.: 12987743000186 ou 12987743000186_ABC12.
Cotas sempre como texto, para não perder casas decimais (a CVM informa 12).

Modos:
  normal    (horário)  13 meses recentes; histórico mensal antigo reaproveitado do que já está publicado
  completo  (botão, ou automático na primeira vez)  refaz o histórico mensal desde 2010
"""
import io, json, os, re, sys, time, urllib.request, urllib.error, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

BASE = 'https://dados.cvm.gov.br/dados/FI'
URL_CAD = BASE + '/CAD/DADOS/registro_fundo_classe.zip'
URL_CAD_ANTIGO = BASE + '/CAD/DADOS/cad_fi.csv'
URL_MES = BASE + '/DOC/INF_DIARIO/DADOS/inf_diario_fi_{ym}.zip'
URL_ANO = BASE + '/DOC/INF_DIARIO/DADOS/HIST/inf_diario_fi_{y}.zip'
FIRESTORE = ('https://firestore.googleapis.com/v1/projects/g20-masterclass/databases/(default)'
             '/documents/fundosAcompanhados?pageSize=300')

OUT = os.environ.get('OUT', 'pub')
CACHE = os.environ.get('CACHE', 'cache')
MODO = os.environ.get('MODO', 'normal')
if MODO == 'logos': MODO = 'normal'
ANO_MENSAL = 2010          # histórico mensal de todos os fundos começa aqui
ANO_HIST_INI = 2000        # histórico diário dos acompanhados começa aqui
PRIMEIRO_MES_DADOS = (2021, 1)  # antes disso a CVM publica por ano (pasta HIST)
BASE_HIST = date(2000, 1, 1)
BRT = timezone(timedelta(hours=-3))

def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)

# ───────────────────────── utilidades ─────────────────────────
def baixar(url, tentativas=4):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'G20-Fundos/1.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == tentativas - 1: raise
        except Exception:
            if i == tentativas - 1: raise
        time.sleep(5 * (i + 1))

def obter(url, nome, imutavel):
    """Arquivos que não mudam mais (anos antigos, meses fechados) ficam em cache entre as execuções."""
    caminho = os.path.join(CACHE, nome)
    if imutavel and os.path.exists(caminho):
        return open(caminho, 'rb').read()
    dados = baixar(url)
    if dados is not None and imutavel:
        os.makedirs(CACHE, exist_ok=True)
        open(caminho, 'wb').write(dados)
    return dados

def cnpj(s):
    return re.sub(r'[^0-9A-Za-z]', '', s or '').upper()

def chave(cn, sub=''):
    c = cnpj(cn)
    s = re.sub(r'[^0-9A-Za-z]', '', sub or '').upper()
    return c + ('_' + s if s else '') if c else ''

def prefixo(k):
    return (k[:3] or 'xxx').upper()

def cota_txt(v):
    v = (v or '').strip().replace(',', '.')
    if not v: return ''
    if '.' in v: v = v.rstrip('0').rstrip('.')
    return v

def num(v):
    try: return float((v or '').strip().replace(',', '.'))
    except ValueError: return None

def inteiro(v):
    x = num(v)
    return int(round(x)) if x is not None else None

def ler_texto(bruto):
    for enc in ('utf-8-sig', 'latin-1'):
        try: return bruto.decode(enc)
        except UnicodeDecodeError: pass
    return bruto.decode('latin-1', 'replace')

def linhas_csv(texto):
    it = iter(texto.splitlines())
    cab = next(it).split(';')
    for l in it:
        if l: yield cab, l.split(';')

def salvar(rel, obj):
    caminho = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(caminho) or OUT, exist_ok=True)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))

def carregar(rel, padrao=None):
    caminho = os.path.join(OUT, rel)
    try:
        with open(caminho, encoding='utf-8') as f: return json.load(f)
    except Exception: return padrao

def meses(de, ate):
    y, m = de
    while (y, m) <= ate:
        yield y, m
        m += 1
        if m == 13: y += 1; m = 1

def mes_menos(ym, n):
    y, m = ym
    for _ in range(n):
        m -= 1
        if m == 0: y -= 1; m = 12
    return (y, m)

# ───────────────────────── informe diário ─────────────────────────
def ler_informe(bruto):
    """Gera (chave, data, cota, pl, cotistas, captacao_dia, resgate_dia) de todos os CSVs do zip.
    Funciona com os layouts antigo (CNPJ_FUNDO) e novo (CNPJ_FUNDO_CLASSE + ID_SUBCLASSE)."""
    z = zipfile.ZipFile(io.BytesIO(bruto))
    for info in z.infolist():
        if not info.filename.lower().endswith('.csv'): continue
        with z.open(info.filename) as f:
            texto = io.TextIOWrapper(f, encoding='latin-1')
            cab = texto.readline().rstrip('\r\n').split(';')
            ix = {c: i for i, c in enumerate(cab)}
            iC = ix.get('CNPJ_FUNDO_CLASSE', ix.get('CNPJ_FUNDO'))
            iS = ix.get('ID_SUBCLASSE'); iD = ix.get('DT_COMPTC'); iQ = ix.get('VL_QUOTA')
            iP = ix.get('VL_PATRIM_LIQ'); iN = ix.get('NR_COTST')
            iA = ix.get('CAPTC_DIA'); iR = ix.get('RESG_DIA')
            if iC is None or iD is None or iQ is None: continue
            n = len(cab)
            for linha in texto:
                l = linha.rstrip('\r\n').split(';')
                if len(l) < n: continue
                q = cota_txt(l[iQ])
                if not q or q == '0': continue
                k = chave(l[iC], l[iS] if iS is not None else '')
                if not k: continue
                yield (k, l[iD][:10], q,
                       l[iP] if iP is not None else '', l[iN] if iN is not None else '',
                       l[iA] if iA is not None else '', l[iR] if iR is not None else '')

def arquivos_ate_hoje(desde_ano):
    """Lista (url, nome_cache, imutavel) de todos os informes desde desde_ano, em ordem."""
    hoje = date.today()
    atual = (hoje.year, hoje.month)
    lim_imutavel = mes_menos(atual, 3)
    out = []
    for y in range(desde_ano, PRIMEIRO_MES_DADOS[0]):
        out.append((URL_ANO.format(y=y), 'ano_%d.zip' % y, True))
    for y, m in meses(PRIMEIRO_MES_DADOS, atual):
        ym = '%04d%02d' % (y, m)
        out.append((URL_MES.format(ym=ym), 'mes_%s.zip' % ym, (y, m) <= lim_imutavel))
    return out

# ───────────────────────── cadastro ─────────────────────────
def ler_cadastro():
    log('Cadastro: baixando')
    cad = {}            # chave -> dict
    por_cnpj = {}       # cnpj -> dict (para herdar dados na subclasse e no cadastro antigo)
    bruto = baixar(URL_CAD)
    z = zipfile.ZipFile(io.BytesIO(bruto))
    def tabela(nome):
        for info in z.infolist():
            if info.filename.lower().startswith(nome):
                return [dict(zip(cab, l)) for cab, l in linhas_csv(ler_texto(z.read(info.filename)))]
        return []
    fundos = {r.get('ID_Registro_Fundo'): r for r in tabela('registro_fundo')}
    classes = {}
    for r in tabela('registro_classe'):
        f = fundos.get(r.get('ID_Registro_Fundo'), {})
        k = chave(r.get('CNPJ_Classe'))
        if not k: continue
        e = {
            'n': (r.get('Denominacao_Social') or f.get('Denominacao_Social') or '').strip(),
            'fn': (f.get('Denominacao_Social') or '').strip(),
            'ti': (r.get('Tipo_Classe') or '').replace('Classes de Cotas de Fundos', '').strip(),
            'c': (r.get('Classificacao') or '').strip(),
            'a': (r.get('Classificacao_Anbima') or '').strip(),
            'bm': (r.get('Indicador_Desempenho') or '').strip(),
            't': (r.get('Tributacao_Longo_Prazo') or '').strip(),
            'p': (r.get('Publico_Alvo') or '').strip(),
            'x': (r.get('Exclusivo') or '').strip(),
            'o': (r.get('Forma_Condominio') or '').strip(),
            'cc': (r.get('Classe_Cotas') or '').strip(),
            'ex': (r.get('Permitido_Aplicacao_CemPorCento_Exterior') or '').strip(),
            's': (r.get('Situacao') or '').strip(),
            'g': (f.get('Gestor') or '').strip(),
            'ad': (f.get('Administrador') or '').strip(),
            'ini': (r.get('Data_Inicio') or '').strip(),
        }
        cad[k] = e; por_cnpj[k] = e
        classes[r.get('ID_Registro_Classe')] = k
    for r in tabela('registro_subclasse'):
        kc = classes.get(r.get('ID_Registro_Classe'))
        if not kc: continue
        k = chave(kc, r.get('ID_Subclasse'))
        e = dict(por_cnpj[kc])
        e.update({
            'n': (r.get('Denominacao_Social') or e['n']).strip(),
            'p': (r.get('Publico_Alvo') or e['p']).strip(),
            'x': (r.get('Exclusivo') or e['x']).strip(),
            'o': (r.get('Forma_Condominio') or e['o']).strip(),
            's': (r.get('Situacao') or e['s']).strip(),
            'pv': (r.get('Previdenciario') or '').strip(),
        })
        cad[k] = e
    log('Cadastro novo: %d classes/subclasses' % len(cad))

    # cadastro antigo: fundos não adaptados, cancelados e taxas de administração/performance
    bruto = baixar(URL_CAD_ANTIGO)
    n_novos = 0
    if bruto:
        for cab, l in linhas_csv(ler_texto(bruto)):
            r = dict(zip(cab, l))
            k = chave(r.get('CNPJ_FUNDO'))
            if not k: continue
            tx = cota_txt(r.get('TAXA_ADM')); tp = cota_txt(r.get('TAXA_PERFM'))
            if k in por_cnpj:
                e = por_cnpj[k]
                if tx and 'tx' not in e: e['tx'] = tx
                if tp and 'tp' not in e: e['tp'] = tp
                if not e.get('a') and r.get('CLASSE_ANBIMA'): e['a'] = r['CLASSE_ANBIMA'].strip()
                continue
            if k in cad: continue
            e = {
                'n': (r.get('DENOM_SOCIAL') or '').strip(), 'ti': (r.get('TP_FUNDO') or '').strip(),
                'c': (r.get('CLASSE') or '').strip(), 'a': (r.get('CLASSE_ANBIMA') or '').strip(),
                'bm': (r.get('RENTAB_FUNDO') or '').strip(), 't': (r.get('TRIB_LPRAZO') or '').strip(),
                'p': (r.get('PUBLICO_ALVO') or '').strip(), 'x': (r.get('FUNDO_EXCLUSIVO') or '').strip(),
                'o': (r.get('CONDOM') or '').strip(), 'cc': (r.get('FUNDO_COTAS') or '').strip(),
                'ex': (r.get('INVEST_CEMPR_EXTER') or '').strip(), 's': (r.get('SIT') or '').strip(),
                'g': (r.get('GESTOR') or '').strip(), 'ad': (r.get('ADMIN') or '').strip(),
                'ini': (r.get('DT_INI_ATIV') or '').strip(), 'fim': (r.get('DT_CANCEL') or '').strip(),
                'antigo': 'S',
            }
            if tx: e['tx'] = tx
            if tp: e['tp'] = tp
            cad[k] = e; por_cnpj[k] = e; n_novos += 1
    log('Cadastro antigo: +%d fundos' % n_novos)
    # remove campos vazios para deixar o arquivo leve
    for k, e in cad.items():
        for c in [c for c, v in e.items() if v in ('', None)]: del e[c]
    return cad

# ───────────────────────── fundos acompanhados ─────────────────────────
def acompanhados():
    ks = set()
    try:
        for l in open('acompanhar.txt', encoding='utf-8'):
            l = l.split('#')[0].strip()
            if l:
                partes = l.split()[0].split('_')
                ks.add(chave(partes[0], partes[1] if len(partes) > 1 else ''))
    except FileNotFoundError:
        pass
    url = FIRESTORE; n = 0
    try:
        while url:
            d = json.loads(baixar(url) or b'{}')
            for doc in d.get('documents', []):
                k = doc['name'].rsplit('/', 1)[-1]
                k = re.sub(r'[^0-9A-Za-z_]', '', k).upper()
                if k: ks.add(k); n += 1
            tok = d.get('nextPageToken')
            url = FIRESTORE + '&pageToken=' + tok if tok else None
    except Exception as e:
        log('Firestore (fundosAcompanhados) indisponível, seguindo só com acompanhar.txt: %r' % e)
    ks.discard('')
    log('Acompanhados: %d (Firestore: %d)' % (len(ks), n))
    return ks

# ───────────────────────── principal ─────────────────────────
def principal():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    hoje = date.today()
    atual = (hoje.year, hoje.month)
    ini_janela = mes_menos(atual, 12)
    base_janela = date(ini_janela[0], ini_janela[1], 1)
    meta_ant = carregar('meta.json', {}) or {}
    completo = MODO == 'completo' or not os.path.isdir(os.path.join(OUT, 'mensal')) or meta_ant.get('mensal_desde') != ANO_MENSAL

    cad = ler_cadastro()
    seguir = acompanhados()
    hist_dir = os.path.join(OUT, 'historico')
    os.makedirs(hist_dir, exist_ok=True)
    ja_tem = {f[:-5] for f in os.listdir(hist_dir) if f.endswith('.json')}
    novos_hist = seguir - ja_tem
    log('Modo %s · histórico novo para %d fundos' % ('COMPLETO' if completo else 'normal', len(novos_hist)))

    # mensal: {chave: {"AAAA-MM": [data, cota, pl, cotistas]}}
    mensal = defaultdict(dict)
    if not completo:
        pasta = os.path.join(OUT, 'mensal')
        for f in os.listdir(pasta):
            for k, serie in (carregar('mensal/' + f, {}) or {}).items():
                for item in serie:
                    if (int(item[0][:4]), int(item[0][5:7])) < ini_janela:
                        mensal[k][item[0]] = ['', item[1], item[2] if len(item) > 2 else None, item[3] if len(item) > 3 else None]

    diario = defaultdict(list)          # janela de 13 meses
    ultima = {}                         # chave -> [data, cota, pl, cotistas]
    capt = defaultdict(float)           # captação líquida nos últimos 12 meses
    hist_novo = defaultdict(dict)       # chave -> {data: cota} (backfill)
    lim_capt = (hoje - timedelta(days=365)).isoformat()

    # quais arquivos ler
    desde = ANO_HIST_INI if novos_hist else (ANO_MENSAL if completo else None)
    lista = arquivos_ate_hoje(desde) if desde else []
    janela = {(URL_MES.format(ym='%04d%02d' % ym), 'mes_%04d%02d.zip' % ym) for ym in meses(ini_janela, atual)}
    lim_imutavel = mes_menos(atual, 3)
    for ym in meses(ini_janela, atual):
        u = URL_MES.format(ym='%04d%02d' % ym); n = 'mes_%04d%02d.zip' % ym
        if (u, n, ym <= lim_imutavel) not in lista:
            lista.append((u, n, ym <= lim_imutavel))

    total = 0
    for url, nome, imut in lista:
        bruto = obter(url, nome, imut)
        if not bruto:
            log('  %s: não existe (ainda)' % nome); continue
        na_janela = (url, nome) in janela
        ano_arq = int(re.findall(r'\d{4}', nome)[0])
        usa_mensal = na_janela or (completo and ano_arq >= ANO_MENSAL)
        usa_hist = bool(novos_hist)
        n = 0
        for k, d, q, pl, nc, ca, re_ in ler_informe(bruto):
            n += 1
            if usa_hist and k in novos_hist:
                hist_novo[k][d] = q
            if usa_mensal and d[:4].isdigit():
                mes = d[:7]
                atual_m = mensal[k].get(mes)
                if atual_m is None or d >= atual_m[0]:
                    mensal[k][mes] = [d, q, inteiro(pl), inteiro(nc)]
            if na_janela:
                try: dd = date(int(d[:4]), int(d[5:7]), int(d[8:10]))
                except ValueError: continue
                diario[k].append(((dd - base_janela).days, q))
                u = ultima.get(k)
                if u is None or d >= u[0]:
                    ultima[k] = [d, q, inteiro(pl), inteiro(nc)]
                if d > lim_capt:
                    capt[k] += (num(ca) or 0) - (num(re_) or 0)
        total += n
        log('  %s: %d linhas%s' % (nome, n, ' (janela)' if na_janela else ''))
    log('Linhas lidas: %d' % total)

    # ── diário (13 meses), por prefixo
    import shutil
    for pasta in ('diario', 'mensal'):
        shutil.rmtree(os.path.join(OUT, pasta), ignore_errors=True)
    shards = defaultdict(dict)
    eventos = []
    for k, serie in diario.items():
        serie = sorted(dict(serie).items())
        shards[prefixo(k)][k] = [[o, q] for o, q in serie]
        # saltos anormais de cota (incorporação, desdobramento, erro de informe)
        for (o1, q1), (o2, q2) in zip(serie, serie[1:]):
            a, b = num(q1), num(q2)
            if a and b and (b / a > 1.5 or b / a < 0.6):
                eventos.append({'k': k, 'tipo': 'salto_cota', 'data': (base_janela + timedelta(days=o2)).isoformat(),
                                'de': q1, 'para': q2, 'fator': round(b / a, 6)})
    for p, d in shards.items():
        salvar('diario/%s.json' % p, {'b': base_janela.isoformat(), 'f': d})

    # ── mensal, por prefixo
    shards = defaultdict(dict)
    for k, por_mes in mensal.items():
        shards[prefixo(k)][k] = [[m, v[1], v[2], v[3]] for m, v in sorted(por_mes.items())]
    for p, d in shards.items():
        salvar('mensal/%s.json' % p, d)

    # ── histórico diário dos acompanhados
    for k in seguir:
        arq = 'historico/%s.json' % k
        ant = carregar(arq) or {}
        serie = {}
        b = date.fromisoformat(ant.get('b', BASE_HIST.isoformat()))
        for o, q in ant.get('q', []):
            serie[(b + timedelta(days=o)).isoformat()] = q
        serie.update(hist_novo.get(k, {}))
        for o, q in diario.get(k, []):
            serie[(base_janela + timedelta(days=o)).isoformat()] = q
        # grava mesmo vazio: marca que o histórico já foi procurado e evita refazer a busca completa todo dia
        salvar(arq, {'k': k, 'b': BASE_HIST.isoformat(),
                     'q': [[(date.fromisoformat(d) - BASE_HIST).days, q] for d, q in sorted(serie.items())]})
        e = cad.get(k) or cad.get(k.split('_')[0]) or {}
        if k not in ultima:
            eventos.append({'k': k, 'tipo': 'acompanhado_sem_cota_recente', 'situacao': e.get('s', '')})

    # ── últimas cotas
    ult_out = {k: v + [int(round(capt.get(k, 0)))] for k, v in ultima.items()}
    salvar('ultimas.json', ult_out)

    # ── índices de busca
    def entrada(k, origem):
        e = dict(cad.get(k) or cad.get(k.split('_')[0]) or {'n': ''})
        e['k'] = k
        u = origem.get(k)
        if u: e['q'] = u[0]; e['pl'] = u[2]; e['nc'] = u[3]
        return {c: v for c, v in e.items() if v not in ('', None)}
    indice = [entrada(k, ultima) for k in sorted(ultima)]
    salvar('indice.json', indice)
    ultimo_mes = {}
    for k, por_mes in mensal.items():
        if k in ultima: continue
        m = max(por_mes)
        ultimo_mes[k] = [por_mes[m][0] or m, None, por_mes[m][2], por_mes[m][3]]
    encerrados = [entrada(k, ultimo_mes) for k in sorted(ultimo_mes) if (cad.get(k) or cad.get(k.split('_')[0]))]
    salvar('indice-encerrados.json', encerrados)
    salvar('eventos.json', eventos[:5000])

    ultima_data = max((v[0] for v in ultima.values()), default='')
    meta = {
        'atualizado': datetime.now(BRT).strftime('%Y-%m-%d %H:%M'),
        'ultima_data_cota': ultima_data,
        'janela_diario_desde': base_janela.isoformat(),
        'mensal_desde': ANO_MENSAL,
        'fundos_com_cota_recente': len(ultima),
        'fundos_encerrados_no_indice': len(encerrados),
        'acompanhados': len(seguir),
        'eventos': len(eventos),
        'modo': 'completo' if completo else 'normal',
        'segundos': int(time.time() - t0),
        'fonte': 'Dados abertos da CVM (dados.cvm.gov.br)',
        'versao': 1,
    }
    salvar('meta.json', meta)
    log('Pronto: %s' % json.dumps(meta, ensure_ascii=False))

if __name__ == '__main__':
    principal()
