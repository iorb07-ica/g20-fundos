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
def token_firebase():
    """Token da conta de serviço do Firebase (segredo FIREBASE_SERVICE_ACCOUNT do repositório).
    Com ele o robô lê fundosAcompanhados, que pelas regras ninguém lê pelo site."""
    sa = os.environ.get('FIREBASE_SERVICE_ACCOUNT', '').strip()
    if not sa: return None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        cred = service_account.Credentials.from_service_account_info(json.loads(sa), scopes=['https://www.googleapis.com/auth/datastore'])
        cred.refresh(Request())
        return cred.token
    except Exception as e:
        log('Conta de serviço do Firebase não funcionou: %r' % e)
        return None

ESTADO_FS = {'situacao': 'não tentou', 'novos_lidos': 0, 'ate': ''}
RUNQUERY = ('https://firestore.googleapis.com/v1/projects/g20-masterclass/databases/(default)/documents:runQuery')

def ler_fs_desde(tok, desde):
    """Só os fundos cadastrados (ou renovados) depois de 'desde'. Cada documento devolvido conta
    1 leitura no Firestore; sem novidade, a consulta custa 1 leitura só."""
    q = {'structuredQuery': {'from': [{'collectionId': 'fundosAcompanhados'}], 'select': {'fields': [{'fieldPath': 'em'}]},
         'orderBy': [{'field': {'fieldPath': 'em'}, 'direction': 'ASCENDING'}], 'limit': 5000}}
    if desde:
        q['structuredQuery']['where'] = {'fieldFilter': {'field': {'fieldPath': 'em'}, 'op': 'GREATER_THAN', 'value': {'timestampValue': desde}}}
    req = urllib.request.Request(RUNQUERY, data=json.dumps(q).encode(), method='POST',
                                 headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json', 'User-Agent': 'G20-Fundos/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.loads(r.read() or b'[]')
    ks, ate = set(), desde or ''
    for item in res:
        d = item.get('document')
        if not d: continue
        k = re.sub(r'[^0-9A-Za-z_]', '', d['name'].rsplit('/', 1)[-1]).upper()
        em = ((d.get('fields') or {}).get('em') or {}).get('timestampValue', '')
        if k: ks.add(k)
        if em > ate: ate = em
    return ks, ate

def acompanhados(desde=''):
    """Fundos para guardar o histórico diário completo: os do acompanhar.txt e os que os alunos
    cadastraram desde a última rodada (os já guardados continuam sendo atualizados pelo que
    já existe em historico/)."""
    ks = set()
    try:
        for l in open('acompanhar.txt', encoding='utf-8'):
            l = l.split('#')[0].strip()
            if l:
                partes = l.split()[0].split('_')
                ks.add(chave(partes[0], partes[1] if len(partes) > 1 else ''))
    except FileNotFoundError:
        pass
    tok = token_firebase()
    ESTADO_FS['ate'] = desde or ''
    if not tok:
        log('Sem a conta de serviço do Firebase: seguindo só com acompanhar.txt')
        ESTADO_FS['situacao'] = 'sem a chave do Firebase'
    else:
        try:
            novos, ate = ler_fs_desde(tok, desde)
            ks |= novos
            ESTADO_FS.update({'situacao': 'ok', 'novos_lidos': len(novos), 'ate': ate})
            log('Fundos cadastrados pelos alunos desde %s: %d' % (desde or 'o início', len(novos)))
        except Exception as e:
            log('Não li fundosAcompanhados: %r' % e)
            ESTADO_FS['situacao'] = 'erro: ' + str(e)[:120]
    ks.discard('')
    return ks

# ───────────────────────── fundos com cota mensal (FII, FIAGRO, FIDC) ─────────────────────────
# out/2026: FII, FIAGRO e FIDC não mandam o Informe Diário; a cota deles vem dos informes mensais.
# Só entram os que NÃO têm ticker na B3 (os com ticker o aluno cadastra pela Renda Variável).
# Ticker = ISIN com as 4 letras do código (BRFVPQCTF015 → FVPQ11). A marcação "negociado em bolsa"
# que o próprio fundo declara não serve: o XP Logístico Prime Yield II diz "S" e não tem ticker.
URL_FII = 'https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/inf_mensal_fii_{y}.zip'
URL_FIAGRO = 'https://dados.cvm.gov.br/dados/FIAGRO/DOC/INF_MENSAL/DADOS/inf_mensal_fiagro_{ym}.zip'
URL_FIDC = 'https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS/inf_mensal_fidc_{ym}.zip'
URL_FIDC_ANO = 'https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/DADOS/HIST/inf_mensal_fidc_{y}.zip'
FII_DESDE = 2016              # primeiro ano do informe mensal de FII
FIDC_DESDE = 2013             # primeiro ano do informe mensal de FIDC
FIDC_MES_DESDE = (2025, 1)    # antes disso a CVM publica o FIDC por ano (pasta HIST)
FIAGRO_DESDE = (2025, 5)      # informe próprio do FIAGRO; antes ele vinha no informe de FII
VERSAO_MENSAIS = 1            # subir para refazer o histórico mensal na próxima rodada
TICKER = re.compile(r'^BR[A-Z]{4}CTF')

def fim_mes(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    prox = date(y + (m == 12), m % 12 + 1, 1)
    return (prox - timedelta(days=1)).isoformat()

def csvs(bruto, padrao):
    """Linhas (dict) dos CSVs do zip cujo nome bate com a expressão 'padrao'."""
    z = zipfile.ZipFile(io.BytesIO(bruto))
    for info in z.infolist():
        nome = info.filename.lower().rsplit('/', 1)[-1]
        if nome.endswith('.csv') and re.search(padrao, nome):
            texto = ler_texto(z.read(info.filename)).splitlines()
            if not texto: continue
            cab = texto[0].split(';')
            for l in texto[1:]:
                if l: yield dict(zip(cab, l.split(';')))

def campo(r, *nomes):
    for n in nomes:
        v = r.get(n)
        if v not in (None, ''): return v
    return ''

def serie_fidc(txt):
    """Código estável da série do FIDC a partir do texto da CVM: 'Subclasse Senior Série 1' → SEN1,
    'Subclasse Subordinada Mezanino 2 | Série 3' → MEZ2S3, 'Subclasse Subordinada  |' → SUB."""
    import unicodedata
    t = unicodedata.normalize('NFKD', txt or '').encode('ascii', 'ignore').decode().upper()
    tipo = 'MEZ' if 'MEZANINO' in t else 'SUB' if 'SUBORD' in t else 'SEN' if re.search(r'S.?NIOR', t) else 'U'
    return tipo + 'S'.join(re.findall(r'\d+', t))

NOME_SERIE = {'SEN': 'Sênior', 'MEZ': 'Mezanino', 'SUB': 'Subordinada', 'U': 'Série'}
def nome_serie(cod):
    m = re.match(r'([A-Z]+?)(\d.*)?$', cod)
    tipo, resto = (m.group(1), m.group(2) or '') if m else (cod, '')
    partes = resto.split('S') if resto else []
    txt = NOME_SERIE.get(tipo, tipo) + (' ' + partes[0] if partes else '')
    return txt + (' Série ' + partes[1] if len(partes) > 1 else '')

def ler_mensais(desde):
    """desde = (ano, mês). Devolve serie {chave: {"AAAA-MM": [cota, pl, cotistas, dy%]}} e
    info {chave: {"isin", "serie"}} dos FII, FIAGRO e FIDC (todos, com ou sem ticker)."""
    hoje = date.today()
    atual = (hoje.year, hoje.month)
    lim_imutavel = mes_menos(atual, 3)
    serie = defaultdict(dict)
    info = defaultdict(dict)
    versao = {}                 # (chave, mês) -> versão já gravada (a CVM republica com versão maior)

    def guardar(k, ym, v, cota, pl, nc, dy):
        if not k or (k, ym) in versao and versao[(k, ym)] > v: return
        versao[(k, ym)] = v
        serie[k][ym] = [cota, pl, nc, dy]

    # FII: um arquivo por ano; complemento = cota, PL, cotistas e DY; geral = ISIN
    for y in range(max(FII_DESDE, desde[0]), atual[0] + 1):
        bruto = obter(URL_FII.format(y=y), 'fii_%d.zip' % y, y <= atual[0] - 2)
        if not bruto: continue
        isin = {}
        for r in csvs(bruto, r'_geral_'):
            k = chave(campo(r, 'CNPJ_Fundo_Classe', 'CNPJ_Fundo'))
            ym = campo(r, 'Data_Referencia')[:7]
            if k and ym >= isin.get(k, ('', ''))[0]: isin[k] = (ym, campo(r, 'Codigo_ISIN').strip().upper())
        n = 0
        for r in csvs(bruto, r'_complemento_'):
            k = chave(campo(r, 'CNPJ_Fundo_Classe', 'CNPJ_Fundo')); ym = campo(r, 'Data_Referencia')[:7]
            if not ym[:4].isdigit() or (int(ym[:4]), int(ym[5:7])) < desde: continue
            q = cota_txt(campo(r, 'Valor_Patrimonial_Cotas'))
            if not q or (num(q) or 0) <= 0: continue
            dy = num(campo(r, 'Percentual_Dividend_Yield_Mes'))
            guardar(k, ym, inteiro(campo(r, 'Versao')) or 0, q, inteiro(campo(r, 'Patrimonio_Liquido')),
                    inteiro(campo(r, 'Total_Numero_Cotistas')), round(dy * 100, 4) if dy is not None else None)
            n += 1
        for k, (ym, i) in isin.items():
            if ym >= info[k].get('_ym', ''): info[k].update({'isin': i, '_ym': ym})
        log('  FII %d: %d linhas' % (y, n))

    # FIAGRO: um arquivo por mês desde mai/2025 (o DY já vem em %)
    for y, m in meses(max(FIAGRO_DESDE, desde), atual):
        ym = '%04d%02d' % (y, m)
        bruto = obter(URL_FIAGRO.format(ym=ym), 'fiagro_%s.zip' % ym, (y, m) <= lim_imutavel)
        if not bruto: continue
        n = 0
        for r in csvs(bruto, r'^inf_mensal_fiagro_\d{6}\.csv$'):
            k = chave(campo(r, 'CNPJ_Classe')); ref = campo(r, 'Data_Referencia')[:7]
            q = cota_txt(campo(r, 'Valor_Patrimonial_Cotas'))
            if not k or not q or (num(q) or 0) <= 0: continue
            guardar(k, ref, inteiro(campo(r, 'Versao')) or 0, q, inteiro(campo(r, 'Patrimonio_Liquido')),
                    inteiro(campo(r, 'Numero_Cotistas')), num(campo(r, 'Dividend_Yield_Mes')))
            if ref >= info[k].get('_ym', ''): info[k].update({'isin': campo(r, 'Codigo_ISIN').strip().upper(), '_ym': ref})
            n += 1
        log('  FIAGRO %s: %d linhas' % (ym, n))

    # FIDC: cota por série (tab X_2) e cotistas por série (tab X_1). Junta por código da série.
    bruto_fidc = defaultdict(lambda: defaultdict(dict))   # cnpj -> mês -> código -> [cota, pl, nc]
    nc_fidc = defaultdict(lambda: defaultdict(int))       # cnpj -> mês -> cotistas de todas as séries
    arqs = [(URL_FIDC_ANO.format(y=y), 'fidc_%d.zip' % y, True) for y in range(max(FIDC_DESDE, desde[0]), FIDC_MES_DESDE[0])]
    arqs += [(URL_FIDC.format(ym='%04d%02d' % ym), 'fidc_%04d%02d.zip' % ym, ym <= lim_imutavel) for ym in meses(max(FIDC_MES_DESDE, desde), atual)]
    for url, nome, imut in arqs:
        bruto = obter(url, nome, imut)
        if not bruto: continue
        n = 0
        for r in csvs(bruto, r'_tab_x_2_\d{4,6}\.csv$'):
            cn = cnpj(campo(r, 'CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO')); ym = campo(r, 'DT_COMPTC')[:7]
            if not cn or not ym[:4].isdigit() or (int(ym[:4]), int(ym[5:7])) < desde: continue
            q = cota_txt(campo(r, 'TAB_X_VL_COTA'))
            if not q or (num(q) or 0) <= 0: continue
            qt = num(campo(r, 'TAB_X_QT_COTA')) or 0
            bruto_fidc[cn][ym][serie_fidc(campo(r, 'TAB_X_CLASSE_SERIE'))] = [q, int(round(qt * num(q))) or None, None]
            n += 1
        for r in csvs(bruto, r'_tab_x_1_\d{4,6}\.csv$'):
            cn = cnpj(campo(r, 'CNPJ_FUNDO_CLASSE', 'CNPJ_FUNDO')); ym = campo(r, 'DT_COMPTC')[:7]
            nc = inteiro(campo(r, 'TAB_X_NR_COTST')) or 0
            if cn and ym: nc_fidc[cn][ym] += nc
            s = bruto_fidc.get(cn, {}).get(ym, {}).get(serie_fidc(campo(r, 'TAB_X_CLASSE_SERIE')))
            if s is not None: s[2] = (s[2] or 0) + nc
        log('  %s: %d séries' % (nome, n))
    # Uma série com cota no último mês: a chave é o CNPJ. Várias: CNPJ_SÉRIE (ex.: ..._SEN1).
    for cn, por_mes in bruto_fidc.items():
        ult = por_mes[max(por_mes)]
        ativas = sorted(ult)
        if len(ativas) <= 1:
            pref = ativas[0] if ativas else None
            for ym, s in por_mes.items():
                v = s.get(pref) if pref in s else (next(iter(s.values())) if len(s) == 1 else None)
                # com uma série só, os cotistas às vezes vêm na linha de outra série (sem cota): soma todas
                if v: serie[cn][ym] = [v[0], v[1], nc_fidc[cn].get(ym) or v[2], None]
        else:
            for cod in ativas:
                k = cn + '_' + cod
                info[k]['serie'] = nome_serie(cod)
                for ym, s in por_mes.items():
                    if cod in s: serie[k][ym] = [s[cod][0], s[cod][1], s[cod][2], None]
    log('Informes mensais (FII, FIAGRO, FIDC): %d fundos/séries' % len(serie))
    return serie, info

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
    hist_dir = os.path.join(OUT, 'historico')
    os.makedirs(hist_dir, exist_ok=True)
    ja_tem = {f[:-5] for f in os.listdir(hist_dir) if f.endswith('.json')}
    # out/2026: FII, FIAGRO e FIDC sem ticker (cota mensal). Na primeira rodada com eles, busca o histórico todo.
    mens_completo = completo or meta_ant.get('mensais') != VERSAO_MENSAIS
    serie_m, info_m = ler_mensais((FIDC_DESDE, 1) if mens_completo else ini_janela)
    com_ticker = {k for k, i in info_m.items() if TICKER.match(i.get('isin', ''))}
    so_mensal = {k for k in serie_m if k not in com_ticker and (k in cad or k.split('_')[0] in cad)}
    log('Cota mensal: %d sem ticker entram · %d com ticker ficam na Renda Variável' % (len(so_mensal), len(com_ticker & set(serie_m))))
    seguir = {k for k in acompanhados(meta_ant.get('fs_ate', '')) if k in cad or k.split('_')[0] in cad} | ja_tem
    seguir -= so_mensal - ja_tem               # cota mensal não tem histórico diário para buscar
    novos_hist = seguir - ja_tem
    log('Modo %s · histórico novo para %d fundos' % ('COMPLETO' if completo else 'normal', len(novos_hist)))

    # mensal: {chave: {"AAAA-MM": [data, cota, pl, cotistas, dy%]}} (dy só nos de cota mensal)
    mensal = defaultdict(dict)
    if not completo:
        pasta = os.path.join(OUT, 'mensal')
        for f in os.listdir(pasta):
            for k, serie in (carregar('mensal/' + f, {}) or {}).items():
                for item in serie:
                    if (int(item[0][:4]), int(item[0][5:7])) < ini_janela:
                        mensal[k][item[0]] = ['', item[1], item[2] if len(item) > 2 else None, item[3] if len(item) > 3 else None, item[4] if len(item) > 4 else None]

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

    # ── cota mensal: entra no mensal e, se ainda reporta (últimos 4 meses), vira "cota recente"
    #    Fundo que também manda o Informe Diário fica com a cota diária.
    diarios = {k.split('_')[0] for k in ultima}
    for k in com_ticker: mensal.pop(k, None)
    mensais = set()
    lim_recente = '%04d-%02d' % mes_menos(atual, 4)
    for k in so_mensal:
        if k.split('_')[0] in diarios: continue
        for ym, (q, pl, nc, dy) in serie_m[k].items():
            mensal[k][ym] = [fim_mes(ym), q, pl, nc, dy]
        ym = max(serie_m[k])
        if ym >= lim_recente:
            q, pl, nc, dy = serie_m[k][ym]
            ultima[k] = [fim_mes(ym), q, pl, nc]
            mensais.add(k)

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
        shards[prefixo(k)][k] = [[m, v[1], v[2], v[3]] + ([v[4]] if len(v) > 4 and v[4] is not None else []) for m, v in sorted(por_mes.items())]
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
        if k in so_mensal and k.split('_')[0] not in diarios:
            e['fr'] = 'M'                                  # cota mensal (FII, FIAGRO, FIDC sem ticker)
            if info_m.get(k, {}).get('serie'): e['n'] = (e.get('n') or '') + ' · ' + info_m[k]['serie']
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
        'cota_mensal': len(mensais),
        'mensais': VERSAO_MENSAIS,
        'lista_dos_alunos': {'situacao': ESTADO_FS['situacao'], 'novos_nesta_rodada': ESTADO_FS['novos_lidos']},
        'fs_ate': ESTADO_FS['ate'],
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
