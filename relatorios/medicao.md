# Medição dos dados abertos da CVM · 2026-10-27
## 1. Cadastro (registro_fundo_classe.zip)
Tamanho do zip: 6.6 MB

### registro_classe.csv · 37018 linhas · 15.6 MB descomprimido
Colunas: `ID_Registro_Fundo`, `ID_Registro_Classe`, `CNPJ_Classe`, `Codigo_CVM`, `Data_Registro`, `Data_Constituicao`, `Data_Inicio`, `Tipo_Classe`, `Denominacao_Social`, `Situacao`, `Data_Inicio_Situacao`, `Classificacao`, `Indicador_Desempenho`, `Classe_Cotas`, `Classificacao_Anbima`, `Tributacao_Longo_Prazo`, `Entidade_Investimento`, `Permitido_Aplicacao_CemPorCento_Exterior`, `Classe_ESG`, `Forma_Condominio`, `Exclusivo`, `Publico_Alvo`, `Patrimonio_Liquido`, `Data_Patrimonio_Liquido`, `CNPJ_Auditor`, `Auditor`, `CNPJ_Custodiante`, `Custodiante`, `CNPJ_Controlador`, `Controlador`
  - **Tipo_Classe** (10 valores): Classes de Cotas de Fundos FIF=26782 · Classes de Cotas de Fundos FIDC=5445 · Classes de Cotas de Fundos FIP=2546 · Classes de Cotas de Fundos FII=1554 · Classes de Cotas de Fundos FIAGRO=395 · Classes de Cotas de Fundos FIIM=273 · Classes de Cotas de Fundos FIF (FAPI)=13 · Classes de Cotas de Fundos Funcine=8 · Classes de Cotas de Fundos FIP (FMIEE)=1 · Classes de Cotas de Fundos FICART=1
  - **Situacao** (4 valores): Em Funcionamento Normal=33801 · Fase Pré-Operacional=2382 · Em Liquidação=798 · Cancelado=37
  - **Classificacao** (6 valores): Multimercado=14415 · (vazio)=10248 · Renda Fixa=7906 · Ações=4288 · FMP-FGTS=93 · Cambial=68
  - **Indicador_Desempenho** (33 valores): (vazio)=11284 · DI de um dia=10740 · Não se aplica=8712 · OUTROS=3260 · Ibovespa=1303 · Índice de Mercado Andima todas NTN-B=601 · Índice de Preços ao Consumidor Amplo (IPCA/IBGE)=394 · Índice de Mercado Andima NTN-B até 5 anos=177 · IBrX=112 · Índice Geral de Preços-Mercado (IGP-M)=106 · Taxa Selic=61 · Índice de Mercado Andima NTN-B mais de 5 anos=55 · Dólar comercial=53 · IRF-M=53 · Índice de Mercado Andima Geral=30
  - **Classe_Cotas** (3 valores): N=16844 · (vazio)=10279 · S=9895
  - **Tributacao_Longo_Prazo** (4 valores): N/A=21062 · (vazio)=11410 · S=3088 · N=1458
  - **Entidade_Investimento** (3 valores): (vazio)=26972 · N=8331 · S=1715
  - **Permitido_Aplicacao_CemPorCento_Exterior** (3 valores): N=18948 · (vazio)=10277 · S=7793
  - **Classe_ESG** (3 valores): N=36048 · S=579 · (vazio)=391
  - **Forma_Condominio** (3 valores): Aberto=23282 · Fechado=9850 · (vazio)=3886
  - **Exclusivo** (3 valores): N=15208 · S=13518 · (vazio)=8292
  - **Publico_Alvo** (4 valores): Profissional=16907 · (vazio)=10815 · Público Geral=5585 · Qualificado=3711

### registro_fundo.csv · 90859 linhas · 25.9 MB descomprimido
Colunas: `ID_Registro_Fundo`, `CNPJ_Fundo`, `Codigo_CVM`, `Data_Registro`, `Data_Constituicao`, `Tipo_Fundo`, `Denominacao_Social`, `Data_Cancelamento`, `Situacao`, `Data_Inicio_Situacao`, `Data_Adaptacao_RCVM175`, `Data_Inicio_Exercicio_Social`, `Data_Fim_Exercicio_Social`, `Patrimonio_Liquido`, `Data_Patrimonio_Liquido`, `Diretor`, `CNPJ_Administrador`, `Administrador`, `Tipo_Pessoa_Gestor`, `CPF_CNPJ_Gestor`, `Gestor`
  - **Tipo_Fundo** (19 valores): FI=62565 · FIDC=8205 · FIF=5229 · FACFIF=5211 · FIP=4499 · FII=2293 · FITVM=842 · FMIA-CL=775 · FIAGRO=419 · FIIM=340 · FMIA=229 · FMP-FGTS=118 · FMIEE=49 · FUNCINE=32 · FAPI=32
  - **Situacao** (7 valores): Cancelado=52977 · Em Funcionamento Normal=34492 · Fase Pré-Operacional=2457 · Em Liquidação=918 · Incorporação=9 · Em Situação Especial=5 · Em Análise=1
  - **Tipo_Pessoa_Gestor** (3 valores): PJ=64177 · (vazio)=26457 · PF=225

### registro_subclasse.csv · 11518 linhas · 1.7 MB descomprimido
Colunas: `ID_Registro_Classe`, `ID_Subclasse`, `Codigo_CVM`, `Data_Constituicao`, `Data_Inicio`, `Denominacao_Social`, `Situacao`, `Data_Inicio_Situacao`, `Forma_Condominio`, `Exclusivo`, `Publico_Alvo`, `Previdenciario`, `Exclusivo_INR`, `Exclusivo_Previdencia_Complementar`
  - **Situacao** (5 valores): Em Funcionamento Normal=6346 · Fase Pré-Operacional=4734 · Em Liquidação=250 · Em Análise=187 · Cancelado=1
  - **Forma_Condominio** (2 valores): Fechado=8765 · Aberto=2753
  - **Exclusivo** (3 valores): N=10542 · S=974 · (vazio)=2
  - **Publico_Alvo** (4 valores): Profissional=7248 · Qualificado=3189 · Público Geral=607 · (vazio)=474
  - **Previdenciario** (3 valores): N=10934 · (vazio)=537 · S=47
  - **Exclusivo_INR** (3 valores): N=11013 · (vazio)=474 · S=31
  - **Exclusivo_Previdencia_Complementar** (3 valores): N=10976 · (vazio)=537 · S=5

### Fundos de teste encontrados (primeiras colunas)
  - [registro_classe.csv] SPX: 1436 | 35369 | 43010543000100 | 6904 | 2025-06-10 | 2025-06-10 | 2025-06-10 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] VERDE: 1669 | 35524 | 51392366000194 | 11991 | 2025-04-14 | 2025-04-14 | 2025-04-14 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] SPX: 1870 | 35663 | 55074554000125 | 1546 | 2024-05-09 | 2024-05-09 | 2024-05-09 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] SPX: 1887 | 35675 | 55431577000140 | 1848 | 2024-06-06 | 2024-06-06 | 2024-06-06 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] SPX: 1893 | 35679 | 55611150000123 | 1899 | 2024-06-20 | 2024-06-20 | 2024-06-20 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] SPX: 1956 | 35726 | 57378678000120 | 2542 | 2024-09-20 | 2024-09-20 | 2024-09-20 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] SPX: 2003 | 35760 | 58290688000171 | 3166 | 2024-11-29 | 2024-11-29 | 2024-11-29 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] VERDE: 2071 | 35814 | 60079651000140 | 4464 | 2025-03-25 | 2025-03-25 | 2025-03-25 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] VERDE: 2201 | 35929 | 62603586000136 | 13072 | 2025-09-08 | 2025-09-08 | 2025-09-08 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] VERDE: 2361 | 36081 | 65326215000142 | 15113 | 2026-02-25 | 2026-02-25 | 2026-02-25 | Classes de Cotas de Fundos FII
  - [registro_classe.csv] VERDE: 4994 | 27669 | 40980983000194 | 16195 | 2025-06-25 | 2025-06-25 | 2025-06-25 | Classes de Cotas de Fundos FIP
  - [registro_classe.csv] VERDE: 5447 | 27987 | 46268214000144 | 25542 | 2024-10-01 | 2024-10-01 | 2024-10-01 | Classes de Cotas de Fundos FIP
  - [registro_classe.csv] KAPITALO: 5666 | 28138 | 49896537000170 | 12203 | 2025-06-10 | 2025-06-10 | 2025-06-10 | Classes de Cotas de Fundos FIP
  - [registro_classe.csv] ALASKA: 32633 | 1231 | 05775774000108 | 187038 | 2025-05-12 | 2025-05-12 | 2025-05-12 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] KAPITALO: 41762 | 2917 | 11377282000167 | 196363 | 2025-05-13 | 2025-05-13 | 2025-05-13 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] KAPITALO: 41938 | 2979 | 11447014000174 | 222046 | 2025-06-17 | 2025-06-17 | 2025-06-17 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] ALASKA: 42741 | 3162 | 12055107000116 | 130737 | 2025-03-19 | 2010-06-02 | 2025-03-19 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] KAPITALO: 42827 | 3174 | 12083748000184 | 222178 | 2025-06-20 | 2025-06-20 | 2025-06-20 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] KAPITALO: 42849 | 3182 | 12105940000124 | 196380 | 2025-05-30 | 2025-05-30 | 2025-05-30 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] KAPITALO: 42852 | 3184 | 12105992000109 | 196398 | 2025-05-30 | 2025-05-30 | 2025-05-30 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] ALASKA: 43760 | 3394 | 12987743000186 | 187321 | 2025-05-21 | 2025-05-21 | 2025-05-21 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] ALASKA: 43816 | 3406 | 13001211000190 | 193003 | 2025-05-26 | 2025-05-26 | 2025-05-26 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] ALASKA: 55259 | 6906 | 26648868000196 | 151629 | 2025-04-11 | 2025-04-11 | 2025-04-11 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] ALASKA: 55277 | 6912 | 26673556000132 | 207462 | 2025-06-06 | 2025-06-06 | 2025-06-06 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] TREND DI: 60706 | 9242 | 32893503000120 | 100366 | 2024-10-28 | 2019-10-03 | 2024-10-28 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] DYNAMO: 65690 | 11674 | 37916879000126 | 227374 | 2025-05-02 | 2025-05-02 | 2025-05-02 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] TREND DI: 73891 | 15510 | 45278833000157 | 143685 | 2025-03-24 | 2022-08-16 | 2025-03-24 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] TREND DI: 81571 | 20183 | 55630600000125 | 45470 | 2024-06-21 | 2024-06-20 | 2024-06-21 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] DYNAMO: 82783 | 21104 | 57719534000190 | 72893 | 2024-10-16 | 2024-10-16 | 2024-10-16 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] DYNAMO: 85197 | 23081 | 62034290000141 | 277908 | 2025-08-01 | 2025-08-01 | 2025-08-01 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] TREND DI: 86728 | 24443 | 64127321000134 | 295213 | 2025-12-19 | 2025-12-19 | 2025-12-19 | Classes de Cotas de Fundos FIF
  - [registro_classe.csv] DYNAMO: 89156 | 26742 | 73232530000139 | 228478 | 2025-05-02 | 2025-05-02 | 2025-05-02 | Classes de Cotas de Fundos FIF
  - [registro_fundo.csv] DYNAMO: 2670 | 06635469000183 | 104008 | 2004-09-20 | 2004-09-20 | FIP | DYNAMO PUMA II FIP | 2010-08-27
  - [registro_fundo.csv] DYNAMO: 2819 | 09250736000192 | 107082 | 2007-12-18 | 2007-12-18 | FIP | DYNAMO BRASIL FIP | 2014-02-18
  - [registro_fundo.csv] TREND DI: 60706 | 32893503000120 | 339210 | 2019-10-04 | 2019-10-03 | FI | TREND DI SIMPLES FUNDO DE INVESTIMENTO EM RENDA FIXA SIMPLES RESPONSABILIDADE LIMITADA | 
  - [registro_fundo.csv] TREND DI: 73891 | 45278833000157 | 469980 | 2022-08-16 | 2022-08-16 | FI | TREND DI FUNDO DE INVESTIMENTO EM COTAS RENDA FIXA SIMPLES RESPONSABILIDADE LIMITADA | 
  - ALASKA: 62 linhas no total
  - VERDE: 646 linhas no total
  - SPX: 695 linhas no total
  - DYNAMO: 18 linhas no total
  - KAPITALO: 422 linhas no total
  - ITAU PRIVILEGE: 0 linhas no total
  - TREND DI: 8 linhas no total

### Cadastro antigo (não adaptados à CVM 175)
cad_fi.csv: 17.1 MB, 46806 linhas
Colunas: `TP_FUNDO`, `CNPJ_FUNDO`, `DENOM_SOCIAL`, `DT_REG`, `DT_CONST`, `CD_CVM`, `DT_CANCEL`, `SIT`, `DT_INI_SIT`, `DT_INI_ATIV`, `DT_INI_EXERC`, `DT_FIM_EXERC`, `CLASSE`, `DT_INI_CLASSE`, `RENTAB_FUNDO`, `CONDOM`, `FUNDO_COTAS`, `FUNDO_EXCLUSIVO`, `TRIB_LPRAZO`, `PUBLICO_ALVO`, `ENTID_INVEST`, `TAXA_PERFM`, `INF_TAXA_PERFM`, `TAXA_ADM`, `INF_TAXA_ADM`, `VL_PATRIM_LIQ`, `DT_PATRIM_LIQ`, `DIRETOR`, `CNPJ_ADMIN`, `ADMIN`, `PF_PJ_GESTOR`, `CPF_CNPJ_GESTOR`, `GESTOR`, `CNPJ_AUDITOR`, `AUDITOR`, `CNPJ_CUSTODIANTE`, `CUSTODIANTE`, `CNPJ_CONTROLADOR`, `CONTROLADOR`, `INVEST_CEMPR_EXTER`, `CLASSE_ANBIMA`
  - **TP_FUNDO** (27 valores): FI=29537 · FIF=5228 · FACFIF=5211 · FIDC=1891 · FIP=1631 · FITVM=842 · FMIA-CL=775 · FII=518 · FMIA=229 · FIEX=206 · FIC-FITVM=187 · FIQ-FMIA=115 · FMP-FGTS=101 · FICE=92 · FMIEE=48
  - **SIT** (7 valores): CANCELADA=46581 · LIQUIDAÇÃO=104 · FASE PRÉ-OPERACIONAL=78 · EM FUNCIONAMENTO NORMAL=21 · INCORPORAÇÃO=10 · EM ANÁLISE=7 · EM SITUAÇÃO ESPECIAL=5
  - **CLASSE** (27 valores): Multimercado=20013 · (vazio)=13162 · Ações=4547 · Renda Fixa=3987 · FIDC=1172 · FIP=839 · Referenciado=638 · FIP Multi=619 · FIDC-NP=524 · FII=511 · Curto Prazo=147 · FIC FIDC=136 · Cambial=102 · Dívida Externa=84 · FIC FIP=71
  - **RENTAB_FUNDO** (30 valores): (vazio)=21037 · DI de um dia=15586 · OUTROS=4004 · Não se aplica=2645 · Ibovespa=1956 · Índice de Preços ao Consumidor Amplo (IPCA/IBGE)=323 · IBrX=260 · Taxa Selic=259 · Índice Geral de Preços-Mercado (IGP-M)=131 · Dólar comercial=110 · Índice de Mercado Andima todas NTN-B=79 · IBrX-50=76 · Índice de Mercado Andima Geral=75 · Índice de Mercado Andima NTN-B até 5 anos=53 · Taxa de juro prefixada=42
  - **CONDOM** (3 valores): Aberto=25629 · (vazio)=13477 · Fechado=7700
  - **FUNDO_COTAS** (3 valores): N=19311 · S=14338 · (vazio)=13157
  - **FUNDO_EXCLUSIVO** (3 valores): N=23629 · (vazio)=17269 · S=5908
  - **TRIB_LPRAZO** (4 valores): (vazio)=21026 · S=13591 · N/A=7021 · N=5168
  - **PUBLICO_ALVO** (4 valores): (vazio)=32988 · Profissional=6246 · Qualificado=5788 · Público Geral=1784
  - **ENTID_INVEST** (3 valores): (vazio)=42694 · N=3475 · S=637
  - **PF_PJ_GESTOR** (3 valores): (vazio)=27040 · PJ=19719 · PF=47
  - **INVEST_CEMPR_EXTER** (3 valores): N=23404 · (vazio)=17269 · S=6133

## 2. Informe diário: últimos 13 meses
Arquivos disponíveis na pasta DADOS:
  70 arquivos .zip (nome · tamanho):
    inf_diario_fi_202405.zip · 11M
    inf_diario_fi_202406.zip · 10M
    inf_diario_fi_202407.zip · 12M
    inf_diario_fi_202408.zip · 11M
    inf_diario_fi_202409.zip · 11M
    inf_diario_fi_202410.zip · 12M
    inf_diario_fi_202411.zip · 10M
    inf_diario_fi_202412.zip · 11M
    inf_diario_fi_202501.zip · 11M
    inf_diario_fi_202502.zip · 10M
    inf_diario_fi_202503.zip · 10M
    inf_diario_fi_202504.zip · 10M
    inf_diario_fi_202505.zip · 11M
    inf_diario_fi_202506.zip · 10M
    inf_diario_fi_202507.zip · 12M
    inf_diario_fi_202508.zip · 11M
    inf_diario_fi_202509.zip · 11M
    inf_diario_fi_202510.zip · 12M
    inf_diario_fi_202511.zip · 10M
    inf_diario_fi_202512.zip · 11M
    inf_diario_fi_202601.zip · 11M
    inf_diario_fi_202602.zip · 9M
    inf_diario_fi_202603.zip · 12M
    inf_diario_fi_202604.zip · 11M
    inf_diario_fi_202605.zip · 11M
    inf_diario_fi_202606.zip · 11M
    inf_diario_fi_202607.zip · 12M
    inf_diario_fi_202608.zip · 11M
    inf_diario_fi_202609.zip · 11M
    inf_diario_fi_202610.zip · 9M
  202610: zip 8.5 MB · 407159 linhas · 25843 fundos/subclasses · publicado 2.7 MB em 699 fragmentos (maior 18 KB)
  202609: zip 11.1 MB · 538204 linhas · 26004 fundos/subclasses · publicado 3.5 MB em 696 fragmentos (maior 23 KB)
  202608: zip 11.1 MB · 538192 linhas · 25977 fundos/subclasses · publicado 3.5 MB em 693 fragmentos (maior 23 KB)
  202607: zip 12.1 MB · 589255 linhas · 25967 fundos/subclasses · publicado 3.8 MB em 689 fragmentos (maior 25 KB)
  202606: zip 11.1 MB · 538538 linhas · 25947 fundos/subclasses · publicado 3.5 MB em 686 fragmentos (maior 23 KB)
  202605: zip 10.6 MB · 511730 linhas · 25894 fundos/subclasses · publicado 3.4 MB em 678 fragmentos (maior 22 KB)
  202604: zip 10.6 MB · 512012 linhas · 25864 fundos/subclasses · publicado 3.3 MB em 674 fragmentos (maior 22 KB)
  202603: zip 11.6 MB · 562018 linhas · 25862 fundos/subclasses · publicado 3.7 MB em 669 fragmentos (maior 25 KB)
  202602: zip 9.5 MB · 457714 linhas · 25722 fundos/subclasses · publicado 3.0 MB em 663 fragmentos (maior 21 KB)
  202601: zip 10.9 MB · 532602 linhas · 25675 fundos/subclasses · publicado 3.5 MB em 658 fragmentos (maior 24 KB)
  202512: zip 11.4 MB · 556400 linhas · 25707 fundos/subclasses · publicado 3.6 MB em 653 fragmentos (maior 25 KB)
  202511: zip 9.9 MB · 478449 linhas · 25509 fundos/subclasses · publicado 3.1 MB em 649 fragmentos (maior 22 KB)
  202510: zip 11.8 MB · 577167 linhas · 25469 fundos/subclasses · publicado 3.7 MB em 645 fragmentos (maior 26 KB)

Colunas do informe: `TP_FUNDO_CLASSE`, `CNPJ_FUNDO_CLASSE`, `ID_SUBCLASSE`, `DT_COMPTC`, `VL_TOTAL`, `VL_QUOTA`, `VL_PATRIM_LIQ`, `CAPTC_DIA`, `RESG_DIA`, `NR_COTST`
**Total 13 meses:** zips da CVM 140.0 MB · 6799440 linhas · 28731 fundos/subclasses distintos (1128 com subclasse) · **publicado 44.4 MB**
Tipos (TP_FUNDO_CLASSE): CLASSES - FIF=6790283 · FI=5686 · CLASSE FIF/FAPI=3471
**ultimas.json (última cota de todos):** 0.3 MB comprimido

## 3. Histórico antigo (pacote HIST, ano 2015)
Arquivos disponíveis na pasta HIST:
  21 arquivos .zip (nome · tamanho):
    inf_diario_fi_2000.zip · 3513
    inf_diario_fi_2001.zip · 3477
    inf_diario_fi_2002.zip · 2M
    inf_diario_fi_2003.zip · 2M
    inf_diario_fi_2004.zip · 23M
    inf_diario_fi_2005.zip · 29M
    inf_diario_fi_2006.zip · 30M
    inf_diario_fi_2007.zip · 34M
    inf_diario_fi_2008.zip · 40M
    inf_diario_fi_2009.zip · 40M
    inf_diario_fi_2010.zip · 44M
    inf_diario_fi_2011.zip · 49M
    inf_diario_fi_2012.zip · 53M
    inf_diario_fi_2013.zip · 59M
    inf_diario_fi_2014.zip · 62M
    inf_diario_fi_2015.zip · 62M
    inf_diario_fi_2016.zip · 63M
    inf_diario_fi_2017.zip · 65M
    inf_diario_fi_2018.zip · 70M
    inf_diario_fi_2019.zip · 77M
    inf_diario_fi_2020.zip · 89M
zip 61.8 MB · 3247495 linhas · 14492 fundos
**Fim de mês de 2015 publicado:** 1.0 MB → estimativa 2010 até hoje (≈17 anos): 17.7 MB
**Diário completo de 2015, todos os fundos:** 21.2 MB → 17 anos ≈ 360.5 MB (referência: por que NÃO guardar tudo)
**Diário de 1 fundo por ano:** ≈ 1 KB → 1.000 fundos acompanhados × 17 anos ≈ 24.9 MB

Tempo total: 63 s
