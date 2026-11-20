# SINAN · dengue (`sinan_dengue`)

## Em uma frase

Notificações de dengue do Sistema de Informação de Agravos de Notificação (SINAN), com
sinais clínicos, exames, classificação e evolução do caso, que o DATASUS publica em um
arquivo nacional por ano: 2000 a 2025 no diretório final e 2026 no preliminar
(listagem de 2026-11-20). A série tem quatro leiautes e fica em três bases, uma tabela do
lake cada: `sinan_dengue_2000_2012`, `sinan_dengue_2013` e `sinan_dengue` (2014 em diante).
Esta página descreve os campos de `sinan_dengue`.

## O que um registro representa

- Uma linha é uma notificação: os campos da notificação individual seguem o Dicionário
  Notificação Individual v5, e os do agravo seguem o Dicionário de Dados Sinan Online,
  Dengue/Chikungunya (`DIC_DADOS_ONLINE.pdf`, revisado em 21/10/2015, campos 31 a 71).
- O dicionário do agravo serve a dengue e a chikungunya (campo 2, "1-Dengue,
  2-Chikungunya", p. 2), mas os arquivos `DENGBR` trazem só dengue: `id_agravo` é `A90`
  em todas as linhas de `DENGBR14` (543.918), `DENGBR17` (239.395) e `DENGBR26`
  (502.229). A biblioteca espera `A90`
  (`src/omnisus/data/dicionarios/sinan_dengue.yaml`, `x-identity`). Chikungunya tem
  arquivos próprios (`CHIKBR`), fora desta base.
- `classi_fin` é a classificação do caso: 5 = descartado, 10 = dengue, 11 = dengue com
  sinais de alarme, 12 = dengue grave, 13 = chikungunya (p. 14). O código 8 não está na
  página; `Classdeng.cnv`, de `TAB_SINANNET`, o chama de "Inconclusivo".
- `criterio` é o critério de confirmação ou descarte: 1 = laboratório, 2 = clínico
  epidemiológico, 3 = em investigação (p. 14).
- `evolucao`: 1 = cura, 2 = óbito pelo agravo, 3 = óbito por outras causas, 4 = óbito em
  investigação, 9 = ignorado (p. 15).
- Sinais clínicos (`febre` a `dor_retro`), doenças pré-existentes (`diabetes` a
  `auto_imune`), sinais de alarme (`alrm_*`) e de gravidade (`grav_*`) são 1 = sim,
  2 = não (pp. 3–4 e 16–26). `grav_orgao` não tem categorias na página 26; o rótulo vem
  de `Sim_nao.cnv`, que o arquivo de definição do TabWin liga ao campo.
- Exames: `resul_soro`, `res_chiks1`, `res_chiks2` e `resul_prnt` são 1 = reagente,
  2 = não reagente, 3 = inconclusivo, 4 = não realizado (p. 5); `resul_ns1`,
  `resul_vi_n`, `resul_pcr_`, `histopa_n` e `imunoh_n` são 1 = positivo, 2 = negativo,
  3 = inconclusivo, 4 = não realizado (pp. 6–7); `sorotipo` vai de 1 = DEN 1 a
  4 = DEN 4 (p. 7).
- `tp_sistema` diz em qual sistema o registro entrou: 2 = Sinan Online; em branco ou
  1 = Sinan NET (`TipoSistema.cnv`).
- `nu_idade_n` é a idade na notificação: o primeiro dígito é a unidade (1 hora, 2 dia,
  3 mês, 4 ano) e os três seguintes a quantidade; `4088` = 88 anos (Dicionário
  Notificação Individual v5, pp. 3–4). `analytical_projection` só a interpreta para o
  `DENGBR17` final auditado (`x-analytics.validated_sources`).
- O dicionário da biblioteca é um inventário físico de `DENGBR17.dbc` (121 campos), mais
  as duas colunas que a importação acrescenta. Têm
  rótulo 82 campos: cada código cita a página do dicionário oficial ou o CNV de
  `TAB_SINANNET` que o nomeia. Branco fica sem rótulo, salvo em `nduplic_n` e
  `tp_sistema`, onde a fonte o nomeia. Os códigos armazenados não mudam.
- A importação grava as colunas do arquivo com nomes em minúsculas e acrescenta
  `_source_ano` e `_source_release`; como o arquivo é nacional, não acrescenta `ano`
  nem `mes`. A coluna `uf` é a do arquivo: a UF de hospitalização (p. 7).

## Datas e geografia

- `dt_notific` é a data de preenchimento da ficha e `nu_ano` o ano da notificação;
  `dt_sin_pri` é a data dos primeiros sintomas (Dicionário Notificação Individual v5,
  pp. 2–3). `sem_not` e `sem_pri` são as semanas epidemiológicas das duas datas, no
  formato `AAAASS`.
- O ano do arquivo é o da semana epidemiológica, não o do calendário: em `DENGBR14`,
  `sem_not` e `sem_pri` começam por 2014 nas 543.918 linhas, enquanto `nu_ano` é 2014 em
  542.335, 2015 em 1.414 e 2013 em 169, e `dt_sin_pri` cai em 2013 em 920 linhas e em
  2015 em 628. Em `DENGBR17` e `DENGBR26`, `nu_ano`, `sem_not` e `sem_pri` coincidem com
  o ano do arquivo em todas as linhas. Nenhum documento oficial afirma a regra; é
  observação desses três arquivos.
- `_source_ano` é o ano do arquivo (`DENGBR17.dbc` → 2017), não uma data dos registros.
  A biblioteca rejeita o arquivo inteiro quando o valor mais frequente de `nu_ano` não é
  o ano do arquivo, e mantém no lake os registros isolados de outro ano
  (`src/omnisus/sources/datasus_ftp/identity.py`).
- `sg_uf_not` e `id_municip` são a UF e o município da unidade que notificou; `sg_uf` e
  `id_mn_resi`, os de residência (Dicionário Notificação Individual v5, pp. 2 e 6).
- `uf` e `municipio` são a UF e o município do hospital, preenchidos quando
  `hospitaliz` = 1 (p. 7).
- `coufinf`, `copaisinf` e `comuninf` são a UF, o país e o município prováveis da
  infecção; o sistema os apaga quando a classificação passa a 5 = descartado
  (pp. 10–12).
- `dt_alrm` e `dt_grav` são as datas de início dos sinais de alarme e de gravidade
  (pp. 21 e 27).

## Cobertura e modalidade

- `FINAIS`: `DENGBR00` a `DENGBR25`; `PRELIM`: `DENGBR26`. Um ano está em um só
  diretório, e `_source_release` diz qual. A importação não aceita filtro de UF nem de
  mês.
- Os 27 arquivos têm quatro leiautes, lidos do cabeçalho de cada um em 2026-11-20
  (`evidence/2026-11-20-sinan-dengue/leiautes.json`):

  | Arquivos | Campos | O que muda |
  | --- | ---: | --- |
  | `DENGBR00` a `DENGBR06` | 107 | ficha do Sinan Windows: sem `ID_AGRAVO` e `TP_NOT`; `NU_IDADE`, `CS_ESCOLAR` e `NDUPLIC` no lugar de `NU_IDADE_N`, `CS_ESCOL_N` e `NDUPLIC_N` |
  | `DENGBR07` a `DENGBR12` | 67 | ficha do Sinan NET; `NU_IDADE_N` é do tipo `F` |
  | `DENGBR13` | 67 | os mesmos nomes; `NU_IDADE_N` e `PLAQ_MENOR` são do tipo `N` |
  | `DENGBR14` a `DENGBR26` | 121 | ficha do Sinan Online, com sinais de alarme e de gravidade |

- O lake não converte uma coluna de um tipo para outro, e `NU_IDADE_N` e `PLAQ_MENOR`
  mudam de tipo entre os leiautes. Por isso a série fica em três bases, cada uma com a
  sua tabela e o seu dicionário:

  | Base | Arquivos | Campos do dicionário |
  | --- | --- | ---: |
  | `sinan_dengue_2000_2012` | `DENGBR00` a `DENGBR12` | 147 (os 107 de 2000–2006 e os 40 que só 2007–2012 tem) |
  | `sinan_dengue_2013` | `DENGBR13` | 67 |
  | `sinan_dengue` | `DENGBR14` a `DENGBR26` | 121 |

- Cada base lista e importa só os anos da sua cobertura: `sus.available("sinan_dengue")`
  começa em 2014, e pedir 2012 a essa base devolve `outside_coverage`.
- Teste de 2026-11-20 com os arquivos do servidor, num lake só:
  `sinan_dengue_2000_2012` recebeu `DENGBR12`, `DENGBR06`, `DENGBR00` e `DENGBR07`, nessa
  ordem; `sinan_dengue_2013` recebeu `DENGBR13`; `sinan_dengue` recebeu `DENGBR26`,
  `DENGBR14` e `DENGBR17` (`evidence/2026-11-20-sinan-dengue/README.md`).
- `DENGBR24` é o maior arquivo: 287.558.389 bytes comprimidos e 6.564.924 registros.
- Os 27 arquivos (27.036.454 registros) foram lidos inteiros em 2026-11-20 e passam na
  conferência de identidade da biblioteca. `DENGBR00` a `DENGBR06` não têm `id_agravo`;
  de `DENGBR07` em diante ele é `A90` em todas as linhas, exceto 11.218 das 1.405.095 de
  `DENGBR22`, que o deixam em branco. Em 18 arquivos há linhas com `nu_ano` de outro ano
  (9.340 das 1.643.215 de `DENGBR25`, o máximo): ficam no lake como publicadas
  (`evidence/2026-11-20-sinan-dengue/serie.json`).

## Armadilhas

- Uma notificação não é um caso confirmado: `classi_fin` separa descartado (5) e
  inconclusivo (8) das três formas de dengue (10, 11, 12), e fica em branco enquanto o
  caso não é encerrado. Em `DENGBR17`, 73.852 das 239.395 linhas são 8 e 458 estão em
  branco; em `DENGBR26`, preliminar, 33.285 das 502.229 estão em branco.
- **A série completa são três tabelas.** Para analisar 2000 a 2026, importe as três
  bases e una as tabelas na consulta, escolhendo as colunas: os leiautes não têm os
  mesmos campos, e `nu_idade_n` é número com casas em `sinan_dengue_2000_2012` (só de
  2007 a 2012; antes o campo não existe) e inteiro nas outras duas; `plaq_menor` é
  número em `sinan_dengue_2013` e texto nas outras.
- Na versão 0.4.0, `sinan_dengue` cobria 2000 em diante. Um lake que recebeu 2000–2006
  nessa tabela com a 0.4.0 mantém as linhas, mas esses anos agora pertencem a
  `sinan_dengue_2000_2012`.
- `DENGBR26` traz `0` em campos que a página lista como 1 e 2 (por exemplo 20.194 linhas
  em `alrm_hipot`, 20.778 em `res_chiks1`, 4.245 em `classi_fin`) e `9` nos sinais de
  alarme e de gravidade (40 linhas em `alrm_hipot`). Nenhuma página nem CNV dá nome a
  esses códigos: ficam sem rótulo.
- Os campos da ficha antiga (`mani_hemor`, `epistaxe`, `gengivo`, `metro`, `petequias`,
  `hematura`, `sangram`, `laco_n`, `plasmatico`, `evidencia`, `con_fhd`, `complica`,
  `plaq_menor`) continuam no leiaute de 121 campos, mas o dicionário do Sinan Online
  não os lista. Em `DENGBR17` estão em branco em todas as linhas; em `DENGBR14`, o mais
  preenchido é `mani_hemor`, com valor em 638 das 543.918. Os rótulos vêm dos CNV que
  `DengueNET.def` liga a cada um; `complica` fica sem rótulo, porque o arquivo o liga a
  dois CNV que divergem no código 4 (plaquetas abaixo de 50.000 ou de 20.000).
- `sinan_dengue_2000_2012` e `sinan_dengue_2013` têm rótulo só nos campos da
  notificação individual (`cs_sexo`, `cs_raca`, `cs_gestant`…), que vêm do Dicionário
  Notificação Individual v5. Os campos da dengue (`classi_fin`, `evolucao`, `febre`,
  `hospitaliz`…) ficam sem rótulo nessas bases: o dicionário do Sinan Online foi lido só
  para o leiaute de 121 campos, e nenhum documento registrado descreve as fichas
  antigas. A idade também não é interpretada nelas.
- `doenca_tra` está em branco em todas as linhas de `DENGBR17`.
- Em `sinan_dengue_2000_2012`, a coluna `ano` vem da ficha antiga (campo `ANO` de
  `DENGBR00` a `DENGBR06`, sem documento registrado): não é o ano do arquivo, que é
  `_source_ano`.
- A idade (`nu_idade_n`) só é interpretada para o `DENGBR17` final auditado. Nele, 19
  linhas têm menos de quatro dígitos e ficam `invalid`, e 15 trazem `4401` a `4407`,
  que a regra lê como 401 a 407 anos: confira o intervalo antes de usar
  `idade_anos_completos`.
- Duplicidades marcadas com 2 em `nduplic_n` não devem ser computadas na incidência
  (Dicionário Notificação Individual v5, pp. 8–9).
- Os dois diretórios são reescritos: em 2026-11-20, `DENGBR07` a `DENGBR25` tinham data
  de modificação entre fevereiro e setembro de 2026, e `DENGBR26` é republicado ao longo
  do ano (2026-11-16). A data prova reescrita, não mudança de conteúdo; `sus.outdated`
  compara o SHA-256.

### Em aberto

- O que significam o `0` e o `9` de `DENGBR26` nos campos Sim/Não.
- O dicionário de dados das fichas de 2000–2006 (Sinan Windows) e de 2007–2013
  (Sinan NET): nenhum está no registro de fontes, por isso os campos que só existem
  nesses leiautes não têm rótulo.
- Se o ano do arquivo segue a semana epidemiológica da notificação ou a dos primeiros
  sintomas: nos três arquivos medidos as duas coincidem com o ano do arquivo em todas
  as linhas.

## Como usar

```python
import omnisus as sus

alvo = "ducklake:./data/raw/omnisus.ducklake"  # o padrão de Lake.local() e load()
print(sus.available_releases("sinan_dengue", refresh=True))  # ano -> final ou prelim
escopos = sus.available("sinan_dengue", years=[2017])
relatorio = sus.import_dataset(
    "sinan_dengue", scopes=escopos, target=alvo, policy="skip_same", run_id="dengue-2017"
)
with sus.LakeReader(alvo) as leitor:
    dados = leitor.connect().sql("SELECT * FROM lake.sinan_dengue WHERE _source_ano = 2017").pl()
print(sus.label("sinan_dengue", dados, columns=["classi_fin"]).group_by("classi_fin_rotulo").len())
```

Para os anos anteriores, troque a base: `sus.available("sinan_dengue_2000_2012", years=[2010])`
e `lake.sinan_dengue_2000_2012`; para 2013, `sinan_dengue_2013`.

Passo a passo com Chagas, hanseníase, tuberculose e dengue, análise e procedência:
[notebooks/sinan.py](https://github.com/raphaelfh/omnisus/blob/main/notebooks/sinan.py)
[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/github/raphaelfh/omnisus/blob/main/notebooks/sinan.py).

## Fontes

- Dicionário de Dados – Sinan Online, Dengue/Chikungunya (`DIC_DADOS_ONLINE.pdf`,
  revisado em 21/10/2015), Ministério da Saúde:
  <https://portalsinan.saude.gov.br/images/documentos/Agravos/Dengue/DIC_DADOS_ONLINE.pdf>
  — consultado em 2026-11-20; 339.721 bytes; SHA-256
  `da262c3b9f20f242d01ee235e64c221dd97e6ad9a53d38cc94da9316bf98c4eb`. Registro:
  `sinan-da262c3b9f20`.
- Dicionário de Dados – SINAN NET – Versão 5.0, Notificação Individual:
  <https://portalsinan.saude.gov.br/images/documentos/Agravos/NINDIV/DIC_DADOS_Notificacao_Individual_v5.pdf>
  — SHA-256 `b3e0561c7a2d0a83d717286e07d01ca75b0d4499a38d3b3ba2b602a4fc983004`.
- `TAB_SINANNET.zip` (`DengueNETON3.0.def`, `DengueNET.def`, `Classdeng.cnv`,
  `Sim_nao.cnv`, `TipoSistema.cnv`, `Evideng.cnv`, `Graufhd.cnv`):
  <ftp://ftp.datasus.gov.br/dissemin/publicos/SINAN/AUXILIAR/TAB_SINANNET.zip> —
  consultado em 2026-11-20; 44.001.396 bytes; SHA-256
  `24ac0c62fb84e5458574fef5a9939b4e47f33ba67038549752b787006ca5944e`. Registro:
  `sinan-tab-24ac0c62fb84`.
- Leitura dos 27 arquivos, auditoria da idade e teste do lake:
  [evidence/2026-11-20-sinan-dengue](https://github.com/raphaelfh/omnisus/blob/main/evidence/2026-11-20-sinan-dengue/README.md).
- [Bases e argumentos](../datasets.md#sinan), página gerada do registro da biblioteca.
