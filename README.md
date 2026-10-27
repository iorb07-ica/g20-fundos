# G20 Fundos

Dados públicos de fundos de investimento (cotas e cadastro, dados abertos da CVM) usados pelo G20 Hub.
Só dados públicos de mercado: nenhum dado de usuário fica aqui.

Site com os dados: https://iorb07-ica.github.io/g20-fundos/

| Rotina | O que faz |
|---|---|
| `fundos-diario.yml` | Todo dia útil (09:30 e 20:30, Brasília): cadastro, últimas cotas, 13 meses diários, histórico mensal desde 2010 e histórico diário dos fundos acompanhados |
| `medicao.yml` | Fase 0: mede tamanho e formato dos dados da CVM (não altera os dados) |

| Arquivo publicado | Conteúdo |
|---|---|
| `meta.json` | Data da atualização e contagens |
| `ultimas.json` | Última cota de todos os fundos: data, cota, PL, cotistas, captação líquida 12m |
| `indice.json` / `indice-encerrados.json` | Busca de fundos (ativos / encerrados) |
| `diario/{3 primeiros do CNPJ}.json` | Cotas diárias dos últimos 13 meses |
| `mensal/{3 primeiros do CNPJ}.json` | Cota de fim de mês desde 2010 |
| `historico/{chave}.json` | Diário completo desde 2000 dos fundos acompanhados |
| `eventos.json` | Saltos anormais de cota e fundos acompanhados sem cota recente |

`acompanhar.txt`: fundos com histórico diário completo além dos cadastrados pelos alunos.
