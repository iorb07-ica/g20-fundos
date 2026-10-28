# -*- coding: utf-8 -*-
"""
G20 Fundos · VERIFICAÇÃO RÁPIDA (a cada 2 horas, das 8h às 22h de Brasília)
Só pergunta ao Firebase se algum aluno cadastrou fundo novo desde a última rodada.
Sem novidade: termina em segundos, sem baixar nada da CVM nem publicar nada.
Com fundo novo ainda sem histórico: avisa o workflow para rodar a atualização completa,
que monta o histórico diário desse fundo.
Grava em GITHUB_OUTPUT: tem_novos=sim|nao
"""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
import atualizar_fundos as A

REPO = os.environ.get('GITHUB_REPOSITORY', 'iorb07-ica/g20-fundos')
GH = os.environ.get('GITHUB_TOKEN', '')

def gh(url):
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + GH, 'User-Agent': 'G20-Fundos/1.0', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def saida(v):
    print('tem_novos=' + v)
    o = os.environ.get('GITHUB_OUTPUT')
    if o: open(o, 'a').write('tem_novos=' + v + '\n')

def principal():
    try:
        meta = json.loads(gh('https://raw.githubusercontent.com/%s/dados/meta.json' % REPO))
    except Exception:
        meta = {}
    tok = A.token_firebase()
    if not tok:
        print('Sem a chave do Firebase'); return saida('nao')
    novos, ate = A.ler_fs_desde(tok, meta.get('fs_ate', ''))
    print('Cadastrados desde %s: %d' % (meta.get('fs_ate', '') or 'o início', len(novos)))
    if not novos: return saida('nao')
    try:
        raiz = json.loads(gh('https://api.github.com/repos/%s/git/trees/dados' % REPO))
        sha = [t['sha'] for t in raiz.get('tree', []) if t['path'] == 'historico'][0]
        arv = json.loads(gh('https://api.github.com/repos/%s/git/trees/%s' % (REPO, sha)))
        ja = {t['path'][:-5] for t in arv.get('tree', []) if t['path'].endswith('.json')}
    except Exception as e:
        print('Não li a lista de históricos: %r' % e); ja = set()
    faltam = sorted(k for k in novos if k not in ja)
    print('Sem histórico ainda: %s' % (', '.join(faltam) or 'nenhum'))
    saida('sim' if faltam else 'nao')

if __name__ == '__main__':
    principal()
