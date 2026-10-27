# -*- coding: utf-8 -*-
"""
G20 Fundos · ROBÔ DE MEDIÇÃO (Fase 0)
Só baixa e mede os dados abertos da CVM. Não grava nada no repositório.
O resultado aparece no resumo da execução (aba Actions) e num arquivo para baixar.

Mede:
  1. Cadastro (registro_fundo_classe.zip): colunas reais de cada arquivo, contagens
     e valores das colunas de categoria (situação, classe, tributação, previdência...).
  2. Informe diário dos últimos 13 meses: linhas, fundos/subclasses, tamanho comprimido
     simulado no formato que a plataforma usaria (fragmentos por prefixo de CNPJ).
  3. Um ano antigo (pacote HIST) para estimar o histórico de fim de mês desde 2010.
  4. Procura alguns fundos de teste pelo nome (ex.: Alaska).
"""
import csv, gzip, io, json, os, re, sys, time, urllib.request, zipfile
from collections import Counter, defaultdict
from datetime import date

BASE = 'https://dados.cvm.gov.br/dados/FI'
URL_CAD = BASE + '/CAD/DADOS/registro_fundo_classe.zip'
URL_CAD_ANTIGO = BASE + '/CAD/DADOS/cad_fi.csv'
URL_DIA = BASE + '/DOC/INF_DIARIO/DADOS/inf_diario_fi_{ym}.zip'
URL_LISTA_DIA = BASE + '/DOC/INF_DIARIO/DADOS/'
URL_LISTA_HIST = BASE + '/DOC/INF_DIARIO/DADOS/HIST/'
ANO_HIST = os.environ.get('ANO_HIST', '2015')
BUSCAS = ['ALASKA', 'VERDE', 'SPX', 'DYNAMO', 'KAPITALO', 'ITAU PRIVILEGE', 'TREND DI']

csv.field_size_limit(10**9)
saida = []
def p(t=''):
    print(t, flush=True); saida.append(t)

def baixar(url, tentativas=4):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'G20-Fundos-medicao/1.0'})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:
            if i == tentativas - 1:
                raise
            time.sleep(5 * (i + 1))

def mb(n): return '%.1f MB' % (n / 1048576.0)
def kb(n): return '%.0f KB' % (n / 1024.0)

def ler_csv(bruto):
    for enc in ('utf-8-sig', 'latin-1'):
        try:
            txt = bruto.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    return list(csv.reader(io.StringIO(txt), delimiter=';'))

def tabela_valores(cab, linhas, limite_distintos=40, top=15):
    for i, col in enumerate(cab):
        c = Counter((l[i].strip() if i < len(l) else '') for l in linhas)
        if 1 < len(c) <= limite_distintos:
            p('  - **%s** (%d valores): %s' % (col, len(c), ' · '.join('%s=%d' % (k or '(vazio)', v) for k, v in c.most_common(top))))

def listar_pasta(url):
    try:
        html = baixar(url).decode('latin-1')
    except Exception as e:
        p('  (não consegui listar %s: %s)' % (url, e)); return
    itens = re.findall(r'href="([^"]+\.zip)"[^\n]*?(\d{2}-\w{3}-\d{4} \d{2}:\d{2})?\s+([\d.]+[KMG]?)\s*$', html, re.M)
    if not itens:
        nomes = re.findall(r'href="([^"]+\.zip)"', html)
        p('  %d arquivos .zip: %s ... %s' % (len(nomes), ', '.join(nomes[:3]), ', '.join(nomes[-3:])))
    else:
        p('  %d arquivos .zip (nome · tamanho):' % len(itens))
        for n, _, t in itens[-30:]:
            p('    %s · %s' % (n, t))

# ───────────────────────── 1. CADASTRO ─────────────────────────
def medir_cadastro():
    p('## 1. Cadastro (registro_fundo_classe.zip)')
    bruto = baixar(URL_CAD)
    p('Tamanho do zip: %s' % mb(len(bruto)))
    z = zipfile.ZipFile(io.BytesIO(bruto))
    nomes_teste = []
    for info in z.infolist():
        linhas = ler_csv(z.read(info.filename))
        if not linhas: continue
        cab, dados = linhas[0], linhas[1:]
        p('')
        p('### %s · %d linhas · %s descomprimido' % (info.filename, len(dados), mb(info.file_size)))
        p('Colunas: `' + '`, `'.join(cab) + '`')
        tabela_valores(cab, dados)
        # fundos de teste pelo nome
        idx_nome = [i for i, c in enumerate(cab) if 'denom' in c.lower() or c.lower().startswith('nome')]
        for l in dados:
            txt = ' '.join(l[i] for i in idx_nome if i < len(l)).upper()
            for b in BUSCAS:
                if b in txt:
                    nomes_teste.append((info.filename, b, ' | '.join(l[:8])))
    p('')
    p('### Fundos de teste encontrados (primeiras colunas)')
    vistos = Counter()
    for arq, b, linha in nomes_teste:
        vistos[b] += 1
        if vistos[b] <= 6:
            p('  - [%s] %s: %s' % (arq, b, linha[:260]))
    for b in BUSCAS:
        p('  - %s: %d linhas no total' % (b, vistos[b]))

    p('')
    p('### Cadastro antigo (não adaptados à CVM 175)')
    try:
        b2 = baixar(URL_CAD_ANTIGO)
        l2 = ler_csv(b2)
        p('cad_fi.csv: %s, %d linhas' % (mb(len(b2)), len(l2) - 1))
        p('Colunas: `' + '`, `'.join(l2[0]) + '`')
        tabela_valores(l2[0], l2[1:])
    except Exception as e:
        p('Não consegui baixar %s: %s' % (URL_CAD_ANTIGO, e))

# ───────────────────── 2. INFORME DIÁRIO ─────────────────────
def meses_recentes(n):
    hoje = date.today(); y, m = hoje.year, hoje.month; out = []
    for _ in range(n):
        out.append('%04d%02d' % (y, m)); m -= 1
        if m == 0: y -= 1; m = 12
    return out

def cota_curta(v):
    v = v.strip().replace(',', '.')
    if '.' in v: v = v.rstrip('0').rstrip('.')
    return v

def ler_informe(bruto):
    """Gera (chave, data, cota, tipo) de todos os CSVs do zip."""
    z = zipfile.ZipFile(io.BytesIO(bruto))
    for info in z.infolist():
        if not info.filename.lower().endswith('.csv'): continue
        with z.open(info.filename) as f:
            rd = csv.reader(io.TextIOWrapper(f, encoding='latin-1'), delimiter=';')
            cab = next(rd)
            ix = {c: i for i, c in enumerate(cab)}
            iC = ix.get('CNPJ_FUNDO_CLASSE', ix.get('CNPJ_FUNDO'))
            iS = ix.get('ID_SUBCLASSE'); iD = ix['DT_COMPTC']; iQ = ix['VL_QUOTA']
            iT = ix.get('TP_FUNDO_CLASSE', ix.get('TP_FUNDO'))
            for l in rd:
                if len(l) <= iQ: continue
                sub = l[iS].strip() if iS is not None and iS < len(l) else ''
                yield (l[iC].strip() + ('#' + sub if sub else ''), l[iD], cota_curta(l[iQ]),
                       l[iT].strip() if iT is not None and iT < len(l) else '', cab)

def fragmentos_gz(por_chave):
    """Simula o arquivo publicado: um JSON por prefixo de 3 dígitos do CNPJ, comprimido."""
    shards = defaultdict(dict)
    for k, serie in por_chave.items():
        pref = re.sub(r'\D', '', k)[:3] or 'xxx'
        shards[pref][k] = serie
    total = 0; maior = 0
    for pref, d in shards.items():
        n = len(gzip.compress(json.dumps(d, separators=(',', ':')).encode(), 9))
        total += n; maior = max(maior, n)
    return total, len(shards), maior

def medir_informe():
    p(''); p('## 2. Informe diário: últimos 13 meses')
    p('Arquivos disponíveis na pasta DADOS:'); listar_pasta(URL_LISTA_DIA)
    tot_zip = tot_linhas = tot_gz = 0
    chaves_all = set(); com_sub = set(); tipos = Counter(); ultima = {}; colunas = None
    for ym in meses_recentes(13):
        try:
            bruto = baixar(URL_DIA.format(ym=ym))
        except Exception as e:
            p('  %s: não baixou (%s)' % (ym, e)); continue
        por_chave = defaultdict(list); n = 0
        for k, d, q, t, cab in ler_informe(bruto):
            colunas = cab
            dia = int(d[8:10]) if len(d) >= 10 else 0
            por_chave[k].append([dia, q]); n += 1
            tipos[t] += 1; chaves_all.add(k)
            if '#' in k: com_sub.add(k)
            if k not in ultima or d > ultima[k][0]: ultima[k] = (d, q)
        gz, nsh, maior = fragmentos_gz(por_chave)
        tot_zip += len(bruto); tot_linhas += n; tot_gz += gz
        p('  %s: zip %s · %d linhas · %d fundos/subclasses · publicado %s em %d fragmentos (maior %s)'
          % (ym, mb(len(bruto)), n, len(por_chave), mb(gz), nsh, kb(maior)))
    p('')
    p('Colunas do informe: `' + '`, `'.join(colunas or []) + '`')
    p('**Total 13 meses:** zips da CVM %s · %d linhas · %d fundos/subclasses distintos (%d com subclasse) · **publicado %s**'
      % (mb(tot_zip), tot_linhas, len(chaves_all), len(com_sub), mb(tot_gz)))
    p('Tipos (TP_FUNDO_CLASSE): ' + ' · '.join('%s=%d' % (k or '(vazio)', v) for k, v in tipos.most_common(15)))
    ult = {k: v for k, v in ultima.items()}
    n_ult = len(gzip.compress(json.dumps(ult, separators=(',', ':')).encode(), 9))
    p('**ultimas.json (última cota de todos):** %s comprimido' % mb(n_ult))
    return len(chaves_all)

# ───────────────────── 3. HISTÓRICO ANTIGO ─────────────────────
def medir_hist():
    p(''); p('## 3. Histórico antigo (pacote HIST, ano %s)' % ANO_HIST)
    p('Arquivos disponíveis na pasta HIST:'); listar_pasta(URL_LISTA_HIST)
    url = URL_LISTA_HIST + 'inf_diario_fi_%s.zip' % ANO_HIST
    try:
        bruto = baixar(url)
    except Exception as e:
        p('Não baixou %s: %s' % (url, e)); return
    fim_mes = {}; diario = defaultdict(list); n = 0
    for k, d, q, t, cab in ler_informe(bruto):
        n += 1
        mes = d[:7]
        if (k, mes) not in fim_mes or d > fim_mes[(k, mes)][0]: fim_mes[(k, mes)] = (d, q)
        diario[k].append([d[5:], q])
    por_chave = defaultdict(list)
    for (k, mes), (d, q) in fim_mes.items(): por_chave[k].append([mes[5:], q])
    gz_mes, _, _ = fragmentos_gz(por_chave)
    gz_dia, _, _ = fragmentos_gz(diario)
    p('zip %s · %d linhas · %d fundos' % (mb(len(bruto)), n, len(diario)))
    p('**Fim de mês de %s publicado:** %s → estimativa 2010 até hoje (≈17 anos): %s'
      % (ANO_HIST, mb(gz_mes), mb(gz_mes * 17)))
    p('**Diário completo de %s, todos os fundos:** %s → 17 anos ≈ %s (referência: por que NÃO guardar tudo)'
      % (ANO_HIST, mb(gz_dia), mb(gz_dia * 17)))
    media = gz_dia / max(1, len(diario))
    p('**Diário de 1 fundo por ano:** ≈ %s → 1.000 fundos acompanhados × 17 anos ≈ %s'
      % (kb(media), mb(media * 1000 * 17)))

if __name__ == '__main__':
    t0 = time.time()
    p('# Medição dos dados abertos da CVM · %s' % date.today().isoformat())
    for etapa in (medir_cadastro, medir_informe, medir_hist):
        try:
            etapa()
        except Exception as e:
            p(''); p('**Erro em %s:** %r' % (etapa.__name__, e))
    p(''); p('Tempo total: %.0f s' % (time.time() - t0))
    txt = '\n'.join(saida) + '\n'
    open('relatorio-medicao.md', 'w', encoding='utf-8').write(txt)
    resumo = os.environ.get('GITHUB_STEP_SUMMARY')
    if resumo:
        open(resumo, 'a', encoding='utf-8').write(txt[:1000000])
