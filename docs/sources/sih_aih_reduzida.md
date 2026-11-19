# SIH · AIH reduzida (`sih_aih_reduzida`)

## Em uma frase

Autorizações de Internação Hospitalar (AIH) do Sistema de Informações Hospitalares do
SUS (SIH/SUS), nos arquivos RD que o DATASUS publica um por UF e mês de processamento.

## O que um registro representa

- O dicionário da biblioteca descreve a base como "SIHSUS — AIH Reduzida (RD)" e não
  declara chave primária (`src/omnisus/data/dicionarios/sih_aih_reduzida.yaml`,
  `title`, sem `primaryKey`).
- O documento oficial descreve o layout dos arquivos `RD*.dbf` para janeiro de 2008 em
  diante (Informe SIH 2016-03, p. 1).
- Cada linha traz o número da AIH em `n_aih`, com 13 caracteres, e o tipo da AIH em
  `ident` (Informe SIH 2016-03, p. 1).
- O documento não lista os códigos de `ident` (Informe SIH 2016-03, p. 1); os rótulos
  vêm do pacote oficial `TAB_SIH.zip`, `RD2008.DEF` → `IDENT.CNV`: 1 = Normal,
  5 = Longa permanência, e a faixa `0-9` dá "Outras/ignorado" a qualquer outro código,
  como o 3, que não tem rótulo próprio na tabela
  (`src/omnisus/data/dicionarios/sources/cnv/vinculos.json`).
- `seq_aih5` é o sequencial de longa permanência, da AIH tipo 5
  (Informe SIH 2016-03, p. 3).
- O layout RD não traz o número do Cartão Nacional de Saúde do paciente
  (Informe SIH 2016-03, p. 1–4); `aud_just` e `sis_just` guardam a justificativa para
  aceitar a AIH sem esse número (p. 3).
- `homonimo` indica se o paciente da AIH é homônimo do paciente de outra AIH
  (Informe SIH 2016-03, p. 3). Nenhum documento do RD de 2008 em diante dá os códigos de `homonimo`
  nem de `gestor_tp`, e nenhum DEF empacotado cita os dois campos: eles ficam sem
  rótulo. O RD publica `homonimo` `0` e `2`, e o RJ `0` e `1`; não suponha que `2`
  e `1` querem dizer a mesma coisa (issues `homonimo-sem-fonte` e
  `gestor_tp-sem-fonte`, #10). Dois documentos registrados dão `0` não e `1` sim
  para a marca de homônimo: o layout dos arquivos RD de 2006-04 a 2007-12
  (`Layout_REDUZIDA.pdf`, p. 2) e o dicionário de dados das tabelas `TB_AIH` e `TB_HAIH`
  (`dicionario_de_dados_AIH.pdf`, pp. 8-9). Os arquivos lidos publicam `0` e `2` em
  todos os anos de 2006 a 2026, inclusive os 21 de Roraima dos meses do layout que diz 0
  e 1, e `1` só em `RDAP2607` (34 registros); por isso a lista dos dois documentos não virou mapa
  (`evidence/2026-11-18-sih-codigos-em-outros-documentos/`,
  `evidence/2026-11-18-rd-medidas/`).
- `diag_princ` é o código do diagnóstico principal pela CID-10, com 4 caracteres
  (Informe SIH 2016-03, p. 2), e o dicionário o liga à tabela `aux_cid10`
  (`src/omnisus/data/dicionarios/sih_aih_reduzida.yaml`).
- `val_tot` é o valor total da AIH (Informe SIH 2016-03, p. 2).
- A importação grava as colunas do arquivo com nomes em minúsculas e acrescenta `ano`,
  `uf`, `mes` e `_source_release` a cada linha
  (`src/omnisus/sources/datasus_ftp/staging.py`, `dbc_bytes_to_parquet`;
  `src/omnisus/sources/datasus_ftp/_runner.py`, `ingest_raw`).

## Datas e geografia

- `ano_cmpt` e `mes_cmpt` são o ano e o mês de processamento da AIH
  (Informe SIH 2016-03, p. 1), e a data de internação é outro campo (p. 2).
- A data de internação está em `dt_inter` e a data de saída em `dt_saida`, ambas no
  formato aaaammdd no recorte; o Informe SIH 2016-03, p. 2, declara char(8), mas
  grafa o primeiro campo `DI_INTER` e seu formato `aaammdd`, inconsistências
  documentais preservadas na auditoria.
- `nasc` é a data de nascimento do paciente, no formato aaaammdd
  (Informe SIH 2016-03, p. 1).
- `gestor_dt` é a data da autorização dada pelo gestor, no formato aaaammdd
  (Informe SIH 2016-03, p. 3).
- As colunas `ano`, `uf` e `mes` vêm do nome do arquivo (`RDSP2401.dbc` → SP, 2024,
  mês 1) (`tests/unit/sources/datasus_ftp/test_filenames_golden.py`;
  `src/omnisus/sources/datasus_ftp/staging.py`).
- `munic_res` é o município de residência do paciente, com 6 caracteres
  (Informe SIH 2016-03, p. 1).
- `munic_mov` é o município do estabelecimento, com 6 caracteres
  (Informe SIH 2016-03, p. 2).
- `uf_zi` é o gestor da AIH, com 6 caracteres, apesar do nome: o DEF o chama de
  "Município gestor" e o informe de "Município Gestor." (`RD2008.DEF`, linhas 175-176;
  Informe SIH 2016-03, p. 1), mas o código nem sempre é de município. A tabela que o DEF
  liga ao campo, `CNV/br_municgestor.cnv` do `TAB_SIH.zip`, tem para cada um dos 26
  estados uma linha "Gestão estadual" com o código da UF seguido de `0000` (`140000`,
  "140000 Roraima - Gestão estadual"). Em RDRR2401 são 2.920 das 3.714 AIHs com `140000`
  e 794 com `140010` (Boa Vista), e `gestao` vale `2` nas primeiras e `1` nas outras. Os
  rótulos vêm dessa tabela, no RD e no RJ (`RJ2008.DEF`, linhas 177-178). Cada rótulo
  começa pelo código da linha da tabela, e uma chave listada como segundo código ou
  dentro de uma faixa mostra o código da linha: `149999` é "140000 Roraima - Gestão
  estadual" e `530010` (Brasília) é "530000 Distrito Federal". Das 15.731 chaves, 10.087
  vêm de três linhas que escrevem faixas (Rio de Janeiro, São Paulo e Distrito Federal),
  forma que o TabWin.pdf (pp. 90-91) só documenta para códigos de até 4 caracteres; a
  issue `uf_zi-faixa-em-codigo-longo` do campo diz isso, e está resolvida: o mapa segue a
  tabela como publicada e expande as faixas (#182). Uma delas é publicada: `530000`
  está em todos os 76.276 registros dos cinco arquivos `RDDF` lidos (janeiro de 2008,
  2012, 2016, 2020 e 2024, `evidence/2026-11-18-rd-medidas/`), e a tabela só chega a ela
  pela faixa `530000-530009`. Nenhum arquivo `RJ` do Distrito Federal foi lido. O campo não tem referência a `aux_municipios`: lá `140000` é "Município
  ignorado - RR", e a tabela do DEF o chama de "Roraima - Gestão estadual".
- `cnes` é o código CNES do hospital, com 7 caracteres (Informe SIH 2016-03, p. 3).
- O dicionário liga `munic_res` e `munic_mov` a `aux_municipios.codigo_6`; `diag_secun`, `cid_asso` e `cid_morte` gravam `0000` quando não há causa ([vocabulários](vocabularios.md)).
  A importação preserva o comprimento dos códigos publicados; não aplica
  preenchimento de zeros guiado pelo YAML.

## Cobertura e modalidade

Arquivos mensais por UF, de janeiro de 2008 em diante, no diretório
`/dissemin/publicos/SIHSUS/200801_/Dados`, sem diretório preliminar; veja
[Bases e argumentos](../datasets.md#onde-fica-no-servidor). O arquivo `SP`, que o mesmo
documento descreve (Informe SIH 2016-03, p. 4–5), e os arquivos `RJ` e `ER`, que ele não
descreve (o sumário, p. 1, lista só `RD` e `SP`), são linhas próprias; veja abaixo.

### Outras linhas do SIH

| Linha | Prefixo | Diretório | Cobertura |
| --- | --- | --- | --- |
| `sih_aih_rejeitada` | `RJ` | `SIHSUS/200801_/Dados` | 2008-01 em diante |
| `sih_servicos_profissionais` | `SP` | `SIHSUS/200801_/Dados` | 2008-01 em diante |
| `sih_aih_rejeitada_erro` | `ER` | `SIHSUS/200801_/Dados` | 2011-01 em diante |
| `sih_aih_reduzida_1992_2007` | `RD` | `SIHSUS/199201_200712/Dados` | 1992-01 a 2007-12; o diretório `Doc` dessa era está vazio no servidor |

Os dicionários dessas linhas partem do inventário físico do descritor DBF de uma fixture real (`scripts/gen_dicionario.py`); o de `sih_aih_reduzida_1992_2007`, dos descritores de quatro fixtures e do censo de layouts descrito abaixo. Os rótulos de categoria vêm do CNV do TabWin quando o DEF liga o campo e todo valor não branco da fixture é chave do mapa (`sources/cnv/vinculos.json`); calendários, cadastros e faixas não são copiados. Fica sem rótulos `sih_aih_rejeitada_erro` (o DEF só liga ano e mês). Em `sih_aih_reduzida_1992_2007`, `ident`, `sexo`, `morte`, `natureza`, `gestao`, `semiplen`, `instru` e `vincprev` têm os rótulos dos CNV que o `RD.DEF` liga a eles nos três pacotes da era em `SIHSUS/200801_/Auxiliar/` (`TAB_SIH_199201-199712.zip`, `TAB_SIH_199801-200307.zip` e `TAB_SIH_200308-200712.zip`), idênticos byte a byte; os SHA-256 estão em `evidence/2026-09-29-tab-sih-rd-eras/`. Os outros campos categóricos que o `RD.DEF` liga, como `espec`, `car_int`, `cobranca` e `marca_uti`, seguem sem rótulo nessa linha. `CH` e `CM` (nacionais, desde 2019) e as eras antigas de `RJ` e `SP` não têm linha em [Bases e argumentos](../datasets.md#sih).

De 1992-01 a 2007-12, os arquivos `RD` lidos (um de RR por mês, AP onde RR falta, e SP e MG nos meses de troca) têm 19 layouts DBF, e o dicionário de `sih_aih_reduzida_1992_2007` declara os 89 campos que aparecem em algum deles. Colunas aparecem e somem: `us_sh`, `us_sp`, `us_sadt`, `us_ortp` e `us_sangue` existem até 1997-12 (`us_rn`, de 1994-01 a 1997-12); `uti_total`, até 1999-12; `cod_arq` e `cont`, até 2006-03, menos em 2001; `semiplen`, de 1995-01 a 1997-12; `diag_sec`, só em 1997; `val_sang`, só em 1994-12, mês que não tem `val_sangue`; `cgc_mant`, só em 2004-07; `cod_seg`, de 2004-07 a 2006-03. Numa tabela com vários meses, a coluna que falta num mês fica NULL nas linhas desse mês. O `RD.DEF` dos três pacotes liga `semiplen` ("Gestão (95-97)") a `GESTAO.CNV`, de onde vêm os rótulos, e `diag_sec` a tabelas CID-9; `diag_sec` fica sem rótulo, como `diag_princ`. `num_proc` é numérico (N) de 1996-01 a 1996-07, e `insc_pn` e `seq_aih5`, de 2004-07 a 2006-03; nos outros meses em que existem são texto (C), o tipo que o dicionário declara. A importação grava os meses N como texto, com o número como está no arquivo e sem completar com zeros ([issue #40](https://github.com/raphaelfh/omnisus/issues/40)): em `RDRR0407`, `insc_pn` e `seq_aih5` saem `0`, e em `RDRR0712`, `0000000000` e `000`. Quem quiser unir as duas formas faz isso na consulta. Um lake em que uma dessas colunas já é número, porque começou por um mês N numa versão anterior, recusa os meses seguintes com `UnsafeSchemaError` e precisa ter a tabela refeita. Os arquivos lidos, com data, tamanho, SHA-256 e layout, estão em `evidence/2026-10-01-rd-1992-2007-layouts/`. O cabeçalho DBF dos 5.165 arquivos `RD` do diretório, lido em 2026-11-19 (`evidence/2026-11-19-sih-cabecalhos/`), tem os mesmos 19 layouts e nenhum outro, em todas as UFs; `num_proc` é N nos 188 arquivos de 1996-01 a 1996-07, e `insc_pn` e `seq_aih5`, nos 567 de 2004-07 a 2006-03.

De 2008-01 em diante, os arquivos `RD` lidos (um de RR por mês, AP onde RR falta, e SP e MG nos meses de troca) têm 6 layouts (`evidence/2026-10-06-rd-2008-layouts/`). O cabeçalho DBF dos 6.072 arquivos `RD` que o servidor listava em 2026-11-19 (`evidence/2026-11-19-sih-cabecalhos/`) tem um desses 6 layouts em 6.071; o outro é `RDAC0909.dbc` (ver "Em aberto"). O layout 6, de 2025-03 em diante, acrescenta `fonte_orc` (C(2)). O `RD2008.DEF` liga o campo a `CNV/fonterem.CNV`, e os rótulos vêm dele: `01` a `04` (também escritos `1` e ` 1`) e a chave literal `  -zz`, "Branco Ignorado" (#24). No excerto de RDRR2503 (`sih_rd_rr_2025_03_excerpt`, 30 registros) ele vale `00` em todas as linhas, e `00` não é chave da tabela: fica sem rótulo, e a issue `fonte_orc-00-sem-fonte` do campo diz isso.

Os arquivos `SP` e `RJ` ganham `FONTE_ORC` (C(2)) no mesmo mês: é o último campo do cabeçalho DBF dos 510 arquivos de cada prefixo, de 2025-03 a 2026-09, e de nenhum anterior (`evidence/2026-11-19-sih-cabecalhos/`, o cabeçalho de todo arquivo `SP` e `RJ` que o servidor listava em 2026-11-19, lido sem nenhum registro). `sih_servicos_profissionais` e `sih_aih_rejeitada` declaram `fonte_orc` sem rótulo e sem mapa: o `SP2008.DEF` e o `RJ2008.DEF` não citam o campo, e a linha do `RD2008.DEF` é do RD. Nos 18 arquivos `RJRR` de 2025-03 a 2026-08, o campo vale `00` nos 1.270 registros, o mesmo valor que o RD publica; dos arquivos `SP`, só o cabeçalho foi lido para este registro. A issue `fonte_orc-sem-def` do campo diz isso.

Em `sih_aih_reduzida` e `sih_aih_rejeitada`, `CONTRAC.CNV` (`contracep1` e `contracep2`) e `motbloqueio.cnv` (`st_mot_blo`, só em `RJ`) abrem com a faixa `00-99`, que rotula qualquer código de dois dígitos: um código fora da tabela recebe "Ignorado/não se aplica" ou "NÃO ESPECIFICADO", e não fica sem rótulo. Do mesmo jeito, `etnia.cnv` (`etnia`) lista os códigos `0001` a `0264` e abre com a faixa `0000-9999`: qualquer outro código de quatro dígitos, `0000` inclusive, recebe "NÃO INFORMADO" só pela faixa (issue `etnia-nao-informado-pela-faixa` no campo). Código que não é dígito fica fora da faixa e sem rótulo: RDRR2501 (RR, 2025-01) publica `X389` em 2 AIHs e `X401` em 3, todas com `raca_cor` 05, e a issue `etnia-x389-x401-sem-fonte` do campo diz isso; o excerto `sih_rd_rr_2025_01_excerpt` traz as duas AIHs com `X389`.

## Armadilhas

- Em `etnia`, o `0000` das fixtures do RD e do RJ (RR 2024-01 e excertos SP de 2022 e
  2023) marca AIH de paciente não indígena, e não etnia desconhecida: nelas, toda linha
  com `0000` tem `raca_cor` de 01 a 04, e toda linha com `raca_cor` 05 (indígena) tem um
  código de `0001` a `0264`. O `etnia.cnv` rotula o `0000` "NÃO INFORMADO" só pela faixa
  `0000-9999`; em RR 2024-01 são 3.303 das 3.714 AIHs do RD. Para contar pacientes
  indígenas, filtre por `raca_cor`.
- Há AIH de tipos diferentes em `ident` (Informe SIH 2016-03, p. 1) e um sequencial
  próprio para a AIH de longa permanência (p. 3).
- A consulta `aih_distintas` do notebook compara o número de linhas com o número de
  valores distintos de `n_aih` antes de qualquer contagem
  (`notebooks/sih_aih_reduzida.py`).
- Agregar por `mes_cmpt` conta AIH processadas no mês (Informe SIH 2016-03, p. 1); para
  contar internações por mês de ocorrência, use `dt_inter` (p. 2).
- `morte` "indica óbito", com 1 algarismo, e o documento não lista os códigos
  (Informe SIH 2016-03, p. 2); os códigos e rótulos vêm do pacote oficial
  `TAB_SIH.zip`, republicado pelo DATASUS em 2026-09-15, `RD2008.DEF` →
  `MORTES.CNV` (`src/omnisus/data/dicionarios/sources/cnv/vinculos.json`).
- `cid_morte` é a CID da morte (Informe SIH 2016-03, p. 3), e `cobranca` é o motivo de
  saída ou permanência (p. 2); os códigos e rótulos de `cobranca` vêm do mesmo pacote
  `TAB_SIH.zip`, `RD2008.DEF` → `SAIDAPERM.CNV` — por exemplo, 26 = permanência por
  mudança de procedimento e 31 = transferência para outro estabelecimento
  (`src/omnisus/data/dicionarios/sources/cnv/vinculos.json`).
- Os complementos federal e do gestor de serviços hospitalares e profissionais
  (`val_sh_fed`, `val_sp_fed`, `val_sh_ges`, `val_sp_ges`) estão incluídos no valor
  total da AIH (Informe SIH 2016-03, p. 4).
- `us_tot` é o valor total em dólar, não em reais (Informe SIH 2016-03, p. 2).
- Vários campos de valor vêm zerados: `val_sadt`, `val_rn`, `val_acomp`, `val_ortp`,
  `val_sangue`, `val_sadtsr`, `val_transp`, `val_obsang` e `val_ped1ac`
  (Informe SIH 2016-03, p. 2).
- Também vêm zerados `uti_mes_in`, `uti_mes_an`, `uti_mes_al`, `uti_int_in`,
  `uti_int_an` e `uti_int_al` (Informe SIH 2016-03, p. 1); a quantidade de dias de UTI
  no mês está em `uti_mes_to` (p. 1).
- `diag_secun` vem preenchido com zeros a partir de 201501
  (Informe SIH 2016-03, p. 2); os diagnósticos secundários estão em `diagsec1` a
  `diagsec9` (p. 4), e o dicionário liga `diagsec1` a `diagsec8` à tabela `aux_cid10`,
  como o `diag_princ` (`RD2008.DEF`, linhas 389-406, relaciona `DIAGSEC1` a `DIAGSEC9` a
  `DBF/CID10.DBF`). O `diagsec9` fica sem a ligação: a p. 4 dá `char (4)`, mas os 157
  arquivos RD lidos de 2014-01 a 2026-07 (um de RR ou AP por mês, mais SP e MG nos meses
  de troca de layout) publicam o campo com 1 caractere, curto demais para um código da
  CID-10 (censo em `evidence/2026-10-06-rd-2008-layouts/`). A `aux_cid10` vem do
  `CID10.DBF` do SIM (ver [Vocabulários](vocabularios.md)), não do `DBF/cid10.dbf` de
  `TAB_SIH.zip`, que o repositório não empacota. O tipo de cada um, em `tpdisec1` a
  `tpdisec9`, vem de `RD2008.DEF` → `TP_DIAGSEC.CNV`: 1 = preexistente, 2 = adquirido. O
  `0` que os arquivos publicam não está na tabela e fica sem rótulo. Dois documentos de
  outro arquivo dizem que `0` é o diagnóstico secundário não preenchido: o layout da
  interface texto do SISAIH01 de 09/2015 (p. 7) e o dicionário de dados das tabelas
  `TB_AIH` e `TB_HAIH` (p. 4). Nenhum DEF liga `tpdisec1` a `tpdisec9` a eles, e por
  decisão do mantenedor (#182) o `0` segue sem rótulo
  (`evidence/2026-11-18-sih-codigos-em-outros-documentos/`). Nos arquivos lidos
  (`evidence/2026-11-18-rd-medidas/`), os 12 de 2014, todos de Roraima, publicam
  `tpdisec1` a `tpdisec9` em branco, e os 148 de 2015-01 em diante publicam `0` só com o
  diagnóstico do mesmo número em branco e `1` ou `2` só com ele preenchido (`tpdisec8` e
  `tpdisec9` só trazem `0`). A contagem diz o que os arquivos trazem, não o que o `0`
  quer dizer.
- Em `sih_aih_reduzida_1992_2007`, `diag_princ` grava CID-9 (6 algarismos, `065099`) de
  1992-01 a 1997-12 e CID-10 (`O800`) de 1998-01 a 2007-12, na mesma coluna: um filtro
  como `LIKE 'I21%'` sobre 1992–2007 perde 1992–1997. Separe por `ano` antes de juntar à
  `aux_cid10`. Em 2007-12, `cid_morte` e `cid_asso` gravam categorias com um `0` antes
  (`0I64`), que não juntam. O dicionário traz as duas armadilhas como issues abertas
  (`diag-princ-cid9-ate-1997`, `cid-zero-a-esquerda`); as evidências estão em
  [Vocabulários](vocabularios.md#cid-9-e-cid-10-nos-sistemas-do-sus).
- `natureza` tem conteúdo só até maio de 2012; a natureza jurídica pela CONCLA está em
  `nat_jur` (Informe SIH 2016-03, p. 2).
- `idade` depende de `cod_idade` (Informe SIH 2016-03, p. 2). O pacote oficial
  `TAB_SIH.zip`, `CNV/IDADEDET.CNV`, confirma dias, meses, anos e unidade 5 com
  deslocamento de 100 anos no domínio detalhado. Os códigos compostos `000` e
  `999` são classificados como inválidos; isso não define uma sentinela global
  para o campo bruto `idade`.
- O rótulo de `cod_idade` (no RD e no RJ) foi medido, não lido: o `RD2008.DEF` e o
  `RJ2008.DEF` ligam o campo a tabelas que leem 3 caracteres (unidade e idade), e
  nenhuma rotula a unidade sozinha. `2` é "Dias", `3` "Meses", `4` "Anos" e `5`
  "Anos (somar 100)", porque `IDADEDET.CNV` lê 500 a 530 como 100 a 130 anos. `0`
  fica sem rótulo: nenhuma fonte o chama de "Ignorada", e no CNV `000` é "Idade
  inválida". O dicionário registra isso na issue `cod_idade-sem-tabela` (#6).
- `sexo` tem 1 caractere (Informe SIH 2016-03, p. 1). A tabela oficial
  `CNV/SEXO.CNV` define 1 masculino e 2/3 feminino. A aplicação dessas regras
  exige os escopos e hashes confirmados no contrato; códigos não documentados
  permanecem desconhecidos.
- Os códigos ficam no lake como publicados: o dicionário decodifica rótulos, datas e
  idade na exibição, não na importação (`src/omnisus/transforms/dictionaries.py`,
  docstring do módulo; `src/omnisus/sources/datasus_ftp/staging.py`, que não
  decodifica).
- O texto é lido como `latin-1`: cada byte vira o caractere de mesmo valor, e
  `valor.encode("latin-1")` devolve os bytes do arquivo. Com `cp1252`,
  um único byte 0x90 em `aud_just` derrubava a importação de `RDSP2308`
  (SHA-256 `eb5d97e8…f3ebb`).
- Em `aud_just` de RD SP de 2022-12 a 2023-12 (13 arquivos, 1.056 valores), os únicos
  bytes de 0x80 a 0x9F são 0x80, 0x87 e 0x90, que em CP850 são Ç, ç e É:
  `DOA\x80AO` é "DOAÇAO", `INFORMA\x87oES` é "INFORMAçoES", `REC\x90M` é "RECÉM".
  Nenhum outro campo desses arquivos tem byte nessa faixa. Para ler em CP850:
  `valor.encode("latin-1").decode("cp850")`. A biblioteca não converte: o dicionário
  declara uma codificação por arquivo, não por campo.

### Em aberto

- O que uma linha representa: o documento traz o número da AIH (`n_aih`,
  Informe SIH 2016-03, p. 1), mas não diz que cada linha é uma AIH distinta, e o layout
  RD não traz o número do Cartão Nacional de Saúde do paciente (p. 1–4). Não trate
  linhas como pacientes, e compare linhas com valores distintos de `n_aih` (consulta
  `aih_distintas`) antes de contar AIH.
- Se uma internação longa aparece em mais de uma linha: o documento traz o tipo da AIH
  e o sequencial de longa permanência (p. 1 e p. 3), mas não diz como uma internação se
  divide em AIH. Não conte internações como linhas sem olhar `ident`, `seq_aih5` e
  `n_aih` nos seus dados.
- Se o mês do arquivo (`mes`) é sempre igual a `mes_cmpt`: o documento não explica o
  nome do arquivo. Compare as duas colunas antes de supor.
- Os códigos de `ident`: o informe não os lista. Para idade e sexo,
  a auditoria de 2026-09-14 acrescentou o pacote oficial TAB_SIH: unidade 5 usa
  100 + quantidade no domínio confirmado; sexo 1 é masculino e 2/3 feminino. A consulta `campo_morte` do notebook mostra
  os valores publicados.
- O comprimento do código de município nos dados: o documento declara 6 caracteres
  (p. 1–2). Confira nos seus dados antes de juntar com outra base.
- A largura de seis campos de texto. O informe dá `nacional` char(2), `raca_cor` char(4),
  `cbor` char(3), `gestor_cpf` char(11) e `gestor_cod` char(3) (Informe SIH 2016-03,
  p. 2–3), e o último layout lido (2025-03 a 2026-07) publica C(3), C(2), C(6), C(15) e
  C(5). Nos arquivos lidos, `gestor_cod` é C(3) e `insc_pn` C(10) até 2011-12, e C(5) e
  C(12) de 2012-01 em diante; o informe, que diz valer "para janeiro de 2008 em diante",
  dá char(3) e char(12). O censo lê um arquivo de RR (ou AP) por mês, mais SP e MG nos
  meses de troca de layout (`evidence/2026-10-06-rd-2008-layouts/`), não todas as UFs. O
  dicionário declara a largura do último layout lido e traz a divergência na issue
  `largura-difere-do-documento` de cada um dos seis campos.
- Se o layout vale para arquivos processados depois de 2016-03: o documento é o informe
  desse processamento (p. 1).
- `nat_jur` e `cnaer` (no RD e no RJ) e `gestor_cod` (no RJ) ficam sem rótulo: o DEF
  liga cada um a tabelas do `TAB_SIH.zip` que ainda não estão empacotadas (`NATJUR.CNV`,
  `NATJURC.CNV`, `ESFERAJUR.CNV` e `ESFERAJURC.CNV`; `CNAEG.CNV` e `CNAE.CNV`;
  `AUTORIZ.CNV`), e a escolha do vínculo está na issue #7. O `vinculos.json` registra o
  motivo em `sem_cnv`. Nas fixtures, `cnaer` é `000` em todas as linhas e o `gestor_cod`
  do RJ vem em branco; o `gestor_cod` do RD é relacionado a `DBF/LIBGESTOR.DBF`.
- Os demais campos que o `RD2008.DEF` e o `RJ2008.DEF` ligam a um CNV e que ficam sem
  mapa (19 no RD, 18 no RJ) também estão em `sem_cnv`, com as linhas do DEF e o motivo:
  agrupamento do código (capítulo e grupo da CID, ano e mês das datas, região e UF do
  município), coluna inicial diferente de 1 (`dias_perm`, `n_aih`), linhas que trazem um
  nome de campo no lugar da coluna inicial (`proc_rea`) ou tabela não empacotada (os
  demais, #137).
- `faec_tp` (no RD e no RJ) tem os rótulos de `CNV/TP_FINAN.CNV`. O DEF liga o campo à
  tabela com `DS_TPFIN` no lugar da coluna inicial. A linha tem a forma da relação com
  DBF do TabWin.pdf (p. 88), mas nomeia um CNV; `DS_TPFIN` é a coluna de descrição do
  `DBF/TP_FINAN.dbf` do mesmo pacote. O mapa usa o CNV, o arquivo que o DEF nomeia, na
  posição 1, a única que cabe num campo de 6 caracteres com códigos de 6 (decisão na
  #182, registrada em `inicio_revisto` do `vinculos.json`). As duas tabelas diferem em 17
  códigos e 2 rótulos (`evidence/2026-11-18-tp-finan-cnv-e-dbf/`): 3 dos 32 códigos que
  os arquivos medidos publicam não estão no DBF. A primeira linha do CNV traz a faixa
  `000000-999999`, "Não discriminado/Não se aplica", e as outras 100 listam um código
  cada: o mapa rotula os 100 e o branco, e não aplica a faixa, então um código fora da
  lista fica sem rótulo, embora a tabela reserve a ele aquele rótulo. Nos 238 arquivos
  RD medidos, os 32 códigos publicados estão todos entre os 100
  (`evidence/2026-11-18-rd-medidas/`). Os rótulos ficam como a tabela os escreve, com
  erros de digitação (`040080`, "… (antigo Reduçäo das Filas)"). A issue
  `faec_tp-faixa-de-reserva` do campo registra isso.
- `RDAC0909.dbc` (Acre, 2009-09) está fora dos 6 layouts. O servidor o data de
  2024-05-22; os outros `RDAC` de 2009 são de 2013-11-01. O cabeçalho tem 82 campos, não
  86: faltam `qt_diarias`, `etnia`, `sequencia` e `remessa`. Em 17 campos o tipo é outro,
  número inteiro de um dígito: 11 campos de valor (`val_sh`, `val_sp` e mais nove) e 6 de
  texto (`num_proc`, `cpf_aut`, `gestor_cod`, `gestor_dt`, `infehosp`, `faec_tp`).
  `val_sh` e `val_sp` vêm zerados nos 4.540 registros, e `val_tot` vem preenchido; em
  `RDAC0908` os dois estão preenchidos nos 4.379. O escopo é importado como publicado: no
  lake, a soma de `val_sh` e a de `val_sp` do Acre em 2009-09 são zero, e as quatro
  colunas que faltam ficam NULL. A issue `zerado-em-rdac0909` dos dois campos registra
  isso. A importação grava os 17 campos com o tipo que o dicionário declara, e o arquivo
  divide a tabela com os outros `RD`: os 11 de valor saem como número com casas, e os 6
  de texto, vazios ou zerados nos 4.540 registros, saem como texto (NULL nos 5 registros
  da fixture, que os trazem vazios). Três campos (`val_tot`, `val_uti`, `us_tot`) têm tipo
  `F`, que o leitor Rust não lê; a biblioteca lê o arquivo com o leitor Python. A
  evidência está em `evidence/2026-11-19-sih-cabecalhos/` e a decisão, na
  [issue #219](https://github.com/raphaelfh/omnisus/issues/219).

## Como usar

```python
import omnisus as sus

alvo = "ducklake:./data/raw/omnisus.ducklake"  # o padrão de Lake.local() e load()
escopos = sus.available("sih_aih_reduzida", years=[2024], ufs=["RR"], months=[1], refresh=True)
relatorio = sus.import_dataset(
    "sih_aih_reduzida", scopes=escopos, target=alvo, policy="skip_same", run_id="sih-rr-2024-01"
)
with sus.LakeReader(alvo) as leitor:
    print(leitor.connect().sql("SELECT ano, mes, count(*) AS aih FROM lake.sih_aih_reduzida GROUP BY ALL").pl())
```

Passo a passo com análise e procedência:
[notebooks/sih_aih_reduzida.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sih_aih_reduzida.py)
[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sih_aih_reduzida.py).

## Fontes

- Disseminação de Informações do Sistema de Informações Hospitalares (SIH), Informe
  Técnico referente ao processamento 2016-03 (`IT_SIHSUS_1603.pdf`), Ministério da
  Saúde / Secretaria de Gestão Estratégica e Participativa / DATASUS:
  <ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Doc/IT_SIHSUS_1603.pdf>
  — consultado em 2026-09-10; SHA-256
  `1e89d5f2cc41420385d7e30ba5541a387912ab3a0efb167d39def74502076220`, conferido de novo
  em 2026-09-13 e em 2026-11-18. Registro: `src/omnisus/data/dicionarios/sources/registry.json`.
  A Tabela 1 do informe (pp. 1–4) está transcrita linha a linha em
  `evidence/2026-11-18-it-sihsus-1603-layout-rd/tabela1.csv`, e a descrição de 110 campos
  no dicionário (`sus.describe_dataset("sih_aih_reduzida")`) é a frase que a tabela traz,
  erros de digitação inclusive; 19 campos são descritos só como "Zerado". O rótulo de 24
  campos também é o texto da tabela, até o primeiro ponto (em `ano_cmpt` e `mes_cmpt`,
  até ", no formato"): os que antes diziam mais do que ela ou outra coisa (por exemplo
  `munic_res`, "Município de Residência do Paciente", sem o "(IBGE)" de antes, e
  `uti_int_to`, "Quantidade de diárias em unidade intermediaria", como o documento
  escreve). Parte do que saiu desses rótulos vinha do `RD2008.DEF`, não do informe
  ("Inscrição pré-natal", "Diárias UCI", a tabela `TB_SIGTAW.DBF` dos procedimentos): a
  claim de rótulo de cada um cita a primeira linha do DEF que nomeia o campo. Ao todo 45
  dos 118 rótulos têm claim verificada; os outros 73 não têm, e nenhum teste os compara
  com o documento.
- Layout do arquivo de REDUZIDA gerado pelo SIHD (`Layout_REDUZIDA.pdf`), Ministério da
  Saúde / DATASUS, que a página de manuais do SIHD lista sob "SIHD (uso até 12/2007)":
  <ftp://ftp2.datasus.gov.br/public/sistemas/dsweb/SIHD/Manuais/Layout_REDUZIDA.pdf>
  — consultado em 2026-11-18; SHA-256
  `f6084d22de3011fd9d2f490736e6d0469c45ac3ccc45be56f4e5c0ad564cb13d`. Está transcrito em
  `evidence/2026-11-18-layout-reduzida-sihd/layout.csv`. Os 19 campos que o informe de
  2016 descreve só como "Zerado" levam como rótulo o texto deste layout anterior (por
  exemplo `val_sadtsr`, "Valor de SADT sem rateio"): o rótulo diz o que o campo era em
  2006 e 2007, os meses em que os arquivos RD lidos têm exatamente os 75 campos do
  documento. Nos 238 arquivos RD lidos de 2008-01 a 2026-07 (1.994.690 registros, 222
  dos arquivos de Roraima; `evidence/2026-11-18-rd-medidas/`) nenhum dos 19 vem
  preenchido em registro algum. Nos 21 arquivos de Roraima de 2006-04 a 2007-12, os
  meses desse layout, 13 deles vêm (`val_sadt` em 36.858 dos 36.983 registros);
  `num_proc` não vem em nenhum, só nos três arquivos de 2006-01 a 2006-03. Cada um traz a
  issue `rotulo-do-layout-ate-2007`. Onde o informe de 2016 descreve o campo, vale o
  texto dele, mesmo quando o layout anterior dizia outra coisa (`ano_cmpt` era "ANO
  COMPETÊNCIA" e é "Ano de processamento da AIH").
- [Bases e argumentos](../datasets.md#sih), página gerada do registro da biblioteca.

## Detalhes técnicos

### Linha de comando

```bash
omnisus inventory sih_aih_reduzida --refresh
omnisus import sih_aih_reduzida --plan inventory --years 2020-2024 --ufs RR
```

As importações acrescentam linhas a `lake.sih_aih_reduzida`. Ao terminar, a importação
devolve um `ImportReport`; o estado de uma transação interrompida aparece em
`ImportAbortedError`. Veja
[resultados e transações](../guides/inventory.md#transactions-and-interrupted-imports).

### Dicionário

As definições de campo, os metadados de chave estrangeira e as regras de decodificação
ficam em `src/omnisus/data/dicionarios/sih_aih_reduzida.yaml`. A ingestão preserva os valores e tipos do DBF, normaliza nomes de colunas e
acrescenta as partições e a modalidade de origem. O YAML descreve campos e
apresentação; ele não comanda coerções na ingestão. Colunas não listadas no YAML
também são preservadas. A validação do dicionário, sozinha, não
certifica todos os registros recebidos.

### Auditoria do contrato analítico (2026-09-14)

Regras, divergências, inventário e limites de aplicabilidade estão na
[auditoria reproduzível](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-09-14-contrato-analitico/regras.md).
Ela registra o snapshot 5, os hashes das publicações, schemas e consultas agregadas.
A aplicabilidade se restringe aos escopos confirmados; uma edição documental não
valida automaticamente toda a série histórica. A procedência de arquivo é
consultada por `LakeReader.publications()` no mesmo snapshot.

### Extensão de escopo (2026-09-14)

A regra 1.1.0 inclui o arquivo final RDRR2301.dbc, identificado pelo SHA-256
`e9f717ff378477a883d19f733efe8409aee7f7795a027584b9f383364264d8e4`.
As 4.734 linhas foram auditadas integralmente para idade, sexo e datas.
Códigos fora do domínio documentado permanecem sem interpretação exata.
Veja [relatório e reprodução](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-09-14-extensao-regras/README.md).

### Validação em lote (2026-10-07)

A regra 1.3.0 cobre os 1.674 arquivos `RD{UF}{AAMM}.dbc` das 27 UFs, das competências
2020-01 a 2025-02, cada um identificado pelo SHA-256 em `validated_sources`. Os arquivos
foram auditados um a um, com uma regra de aceite escrita (ADR 0003, Consequences), e
nenhum foi bloqueado. Ficam sem idade interpretada 9.158 registros com a composta `230` e
12 com a `000`, como a regra documenta. A partir de 2025-03 o RD está no layout 6, ainda
não validado (#86). Um arquivo republicado depois perde as categorias harmonizadas até
uma nova validação.
Veja [relatório e reprodução](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-10-07-validacao-sih_aih_reduzida-2020-01-2025-02/README.md).
