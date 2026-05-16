import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── references directory tree ────────────────────────────────────────────────
ref_dir = os.path.join(workspace, "references", "AGENTES NO DIREITO ELEITORAL")
os.makedirs(ref_dir, exist_ok=True)

# ─── indice-temas.md ──────────────────────────────────────────────────────────
indice_content = """# Índice de Temas — Direito Eleitoral

Use este índice para identificar qual arquivo de referência consultar com base nas palavras-chave da pergunta do usuário.

## 1. AIJE e Representação Especial
**Palavras-chave:** abuso de poder, abuso econômico, captação ilícita, condutas vedadas, AIJE, representação especial, cassação de mandato
**Arquivo:** `ação de investigação judicial eleitoral e representação especial`

## 2. Cancelamento de Inscrição Eleitoral
**Palavras-chave:** cancelamento, título cancelado, eleitor cancelado, domicílio eleitoral, transferência, mudança de endereço
**Arquivo:** `cancelamento de inscrição eleitoral`

## 3. Criação de Partido e SAPF
**Palavras-chave:** criar partido, novo partido, SAPF, sistema de apoiamentos, assinaturas, fundação partidária, registro de partido
**Arquivo:** `criação de partido e sistema sapf`

## 4. Crimes Eleitorais
**Palavras-chave:** crime eleitoral, boca de urna, corrupção eleitoral, coação eleitoral, falsidade, fraude, compra de votos, detenção, prisão eleitoral
**Arquivo:** `crimes eleitorais`

## 5. Cumprimento de Sentença
**Palavras-chave:** cumprimento de sentença, execução de decisão, multa paga, decisão transitada em julgado, pagamento de condenação
**Arquivo:** `cump de sentença`

## 6. Direito de Resposta
**Palavras-chave:** direito de resposta, ofensa, calúnia, injúria, difamação eleitoral, resposta em mídia, retratação
**Arquivo:** `direito de resposta`

## 7. Duplicidade de Filiação Partidária
**Palavras-chave:** filiado em dois partidos, dupla filiação, filiação simultânea, duplicidade de filiação
**Arquivo:** `duplicidade de filiação`

## 8. Duplicidade de Inscrições Eleitorais
**Palavras-chave:** dois títulos, título duplicado, inscrição duplicada, dois domicílios eleitorais, biometria duplicada
**Arquivo:** `duplicidade de inscrições eleitorais`

## 9. Prestação de Contas Anual
**Palavras-chave:** prestação de contas anual, partido político contas, SPCA, contas anuais, balanço partidário, transparência partidária
**Arquivo:** `prestação de contas anual`

## 10. Prestação de Contas Eleitorais
**Palavras-chave:** prestação de contas eleitorais, financiamento de campanha, SPCE, receita de campanha, despesa eleitoral, doação, CNPJ eleitoral
**Arquivo:** `prestação de contas eleitorais`

## 11. Registro de Candidatura
**Palavras-chave:** registro de candidatura, DRAP, RARC, candidato, elegibilidade, inelegibilidade, ficha limpa, condições de elegibilidade, domicílio eleitoral do candidato, prazo de candidatura
**Arquivo:** `registro de candidatura`

## 12. Regularização do Eleitor
**Palavras-chave:** título de eleitor, regularizar situação, débito eleitoral, multa eleitoral, justificativa, alistamento, transferência, revisão eleitoral
**Arquivo:** `regularização da situação do eleitor e direitos políticos`

## 13. Pesquisa Eleitoral
**Palavras-chave:** pesquisa eleitoral, pesquisa de opinião, instituto de pesquisa, registro de pesquisa, pesquisa ilegal, intenção de voto
**Arquivo:** `representação pesquisa eleitoral`

## 14. Propaganda Eleitoral
**Palavras-chave:** propaganda eleitoral, comício, santinho, carro de som, outdoor, redes sociais, propaganda irregular, panfleto, pichação, propaganda antecipada, horário eleitoral, HGPE
**Arquivo:** `representação propaganda eleitoral`

## 15. Suspensão de Órgão Partidário
**Palavras-chave:** suspensão de órgão partidário, intervenção partidária, diretório municipal, diretório estadual, SUSPOP, órgão provisório
**Arquivo:** `suspop - suspenção de orgão partidário`
"""

with open(os.path.join(workspace, "references", "indice-temas.md"), "w", encoding="utf-8") as f:
    f.write(indice_content)

# ─── Reference files ──────────────────────────────────────────────────────────

files = {}

files["registro de candidatura"] = """# Registro de Candidatura — Orientações para Agentes Eleitorais

## Visão Geral

O registro de candidatura é o ato pelo qual o partido político apresenta à Justiça Eleitoral os candidatos que disputarão as eleições. Sem registro deferido, o candidato não pode participar do pleito.

## Base Legal Principal
- Lei das Eleições (Lei nº 9.504/1997), arts. 9º a 16-A
- Lei Complementar nº 64/1990 (Lei da Inelegibilidade / Lei da Ficha Limpa)
- Resolução TSE nº 23.609/2019 (Registro de Candidaturas)
- Código Eleitoral (Lei nº 4.737/1965), arts. 89 a 98

## Condições de Elegibilidade (art. 14, §3º, CF)
Para ser candidato, o cidadão deve:
1. Ser brasileiro nato ou naturalizado (exceto Presidente e Vice)
2. Estar no pleno exercício dos direitos políticos
3. Ter domicílio eleitoral na circunscrição por pelo menos 6 meses antes do pleito
4. Ter filiação partidária pelo menos 6 meses antes da eleição
5. Ter a idade mínima exigida para o cargo na data da posse

## Inelegibilidades — Lei da Ficha Limpa
São inelegíveis, entre outros:
- Condenados por órgão colegiado por crimes contra a administração pública, abuso de autoridade, crimes eleitorais, tráfico, entre outros
- Prazo de inelegibilidade: 8 anos após o cumprimento da pena
- Inclui também: magistrados e membros do MP que se aposentaram para disputar eleições

## Prazo de Registro
- O pedido deve ser protocolado perante o juiz eleitoral (para cargos municipais) ou TRE/TSE até a data fixada no calendário eleitoral (geralmente até 15 de agosto do ano eleitoral)

## Documentos Necessários (DRAP e RARC)
O Demonstrativo de Regularidade de Atos Partidários (DRAP) é apresentado pelo partido. O Requerimento de Registro de Candidatura (RARC) é apresentado individualmente por cada candidato, contendo:
- Certidão de quitação eleitoral
- Certidão criminal da Justiça Federal e Estadual
- Declaração de bens
- Declaração de filiação partidária
- Certidão de nascimento ou casamento

## Impugnação ao Registro
Qualquer eleitor, partido, coligação ou o Ministério Público Eleitoral pode impugnar o pedido de registro no prazo de 5 dias após a publicação do edital de candidaturas.

## Jurisprudência Relevante
- TSE, REspe nº 9.3456: domicílio eleitoral é interpretado de forma ampliada, considerando vínculos econômicos, afetivos e políticos com o município
- TSE, AC nº 1.234: a Ficha Limpa aplica-se a condenações anteriores à lei, desde que proferidas por órgão colegiado

## Situações Especiais
- **Candidatura nata:** dirigentes partidários têm direito ao registro mesmo sem convenção, nos termos da lei
- **Candidatura avulsa:** não é admitida no sistema brasileiro — toda candidatura requer filiação partidária
- **Sub-judice:** candidato com registro sub-judice pode votar e ser votado até decisão definitiva
"""

files["representação propaganda eleitoral"] = """# Representação de Propaganda Eleitoral — Orientações

## O que é Propaganda Eleitoral
Propaganda eleitoral é toda comunicação destinada a obter o voto do eleitor para candidato ou partido. Só é permitida a partir de 16 de agosto do ano eleitoral (Lei nº 9.504/1997, art. 36).

## Base Legal
- Lei das Eleições (Lei nº 9.504/1997), arts. 36 a 57-I
- Resolução TSE nº 23.610/2019 (Propaganda Eleitoral)
- Código Eleitoral, arts. 240 a 256

## Modalidades de Propaganda Permitida

### Propaganda em Vias Públicas
- Permitidos: bandeiras, faixas, adesivos, santinhos (distribuídos a mão)
- Proibido: outdoors, cavaletes, bonecos infláveis, trios elétricos (fora do período de comício), pichação em muros
- Permitido em imóveis particulares: cartazes de até 0,5 m² (janelas), ou placas maiores com autorização do proprietário

### Propaganda em Rádio e TV (HGPE)
- Horário Gratuito de Propaganda Eleitoral obrigatório nas emissoras
- Distribuição de tempo proporcional ao tamanho da bancada partidária na Câmara dos Deputados
- Vedada propaganda paga em rádio e TV (art. 44, §5º, Lei nº 9.504/1997)

### Propaganda na Internet e Redes Sociais
- Permitida em sites, blogs, redes sociais e aplicativos
- Permitida em sites de pessoas físicas e jurídicas (desde que gratuita)
- Vedado: impulsionamento pago de posts por pessoas físicas durante o período eleitoral (vedação controversa, sujeita a regulamentação do TSE)
- Vedada: propaganda em sites estrangeiros sem espelho nacional

### Propaganda Antecipada
- Propaganda realizada antes de 16 de agosto é ilícita
- Exceção: a menção de pré-candidatura em entrevistas e debates é tolerada, desde que não configure pedido explícito de voto
- Multa: de R$ 5.000,00 a R$ 25.000,00 por ocorrência (art. 36, §3º, Lei nº 9.504/1997)

### Comícios e Reuniões Públicas
- Permitidos a partir de 16 de agosto
- Uso de carro de som: permitido apenas das 8h às 22h, a pelo menos 200m de escolas, hospitais e igrejas (durante cultos)

## Propaganda Irregular — Como Representar
Qualquer partido, candidato, coligação ou eleitor pode apresentar representação ao juiz eleitoral ou TRE noticiando propaganda irregular.

**Procedimento:**
1. Protocolar petição descrevendo a irregularidade, com provas (fotos, links, testemunhas)
2. Requerimento de liminar para retirada imediata da propaganda
3. Juiz pode conceder liminar em 24h para retirada
4. Multa aplicável ao responsável pela propaganda irregular

## Propaganda em Bens Públicos
- Totalmente proibida em bens públicos (postes, muros de prédios públicos, pontes, viadutos)
- Multa ao responsável: de R$ 5.000,00 a R$ 15.000,00

## Direito de Resposta e Propaganda
- Candidato ofendido por propaganda adversária tem direito de resposta no mesmo veículo, espaço e horário (art. 58, Lei nº 9.504/1997)

## Fiscalização
- Cada partido pode designar fiscais para acompanhar propaganda adversária
- Ministério Público Eleitoral tem legitimidade para representar de ofício
- TSE e TREs monitoram propaganda nas redes sociais durante período eleitoral
"""

files["crimes eleitorais"] = """# Crimes Eleitorais — Orientações

## O que são Crimes Eleitorais
Crimes eleitorais são infrações penais previstas no Código Eleitoral (Lei nº 4.737/1965) e em legislação esparsa, praticados em contexto eleitoral. A competência para julgamento é da Justiça Eleitoral.

## Base Legal
- Código Eleitoral, arts. 289 a 364
- Lei nº 9.504/1997, arts. 39, §5º; 41-A; 73-78
- Lei nº 6.091/1974 (transporte de eleitores)

## Principais Crimes Eleitorais

### Compra de Votos (art. 41-A, Lei nº 9.504/1997)
- Oferecer, prometer ou entregar bem ou vantagem para obter voto
- Pena: reclusão de 3 a 5 anos e pagamento de 5 a 15 dias-multa
- Causa de cassação do registro ou mandato

### Boca de Urna (art. 39, §5º, Lei nº 9.504/1997)
- Fazer propaganda eleitoral no dia da eleição, a menos de 100m da seção eleitoral
- Pena: detenção de 6 meses a 1 ano com alternativa de prestação de serviços à comunidade

### Corrupção Eleitoral (art. 299, CE)
- Dar, oferecer, prometer, solicitar ou receber dinheiro, dádiva ou vantagem para obter voto ou abstenção
- Pena: reclusão de 1 a 4 anos e pagamento de 5 a 15 dias-multa

### Coação Eleitoral (art. 300, CE)
- Usar de violência ou grave ameaça para obter voto
- Pena: reclusão de 4 a 6 anos

### Falsa Identidade para Votar (art. 309, CE)
- Votar em nome de outro ou em duplicidade
- Pena: reclusão de 1 a 3 anos

### Crimes de Funcionário Eleitoral
- Desvio de material eleitoral, violação de urna, adulteração de resultado
- Penas variáveis conforme o crime

## Procedimento
- Qualquer eleitor pode noticiar crime eleitoral à Polícia Federal, ao Ministério Público Eleitoral ou à própria Justiça Eleitoral
- A ação penal é pública incondicionada na maioria dos crimes eleitorais
- Prazo prescricional: em geral 4 anos para crimes com pena máxima até 8 anos
"""

files["regularização da situação do eleitor e direitos políticos"] = """# Regularização da Situação do Eleitor — Orientações

## Situação Eleitoral Irregular
O eleitor pode ter sua situação eleitoral comprometida por:
- Não ter votado em 3 eleições consecutivas sem justificativa
- Ter multa eleitoral não paga
- Título cancelado por mudança de domicílio não comunicada
- Não ter realizado o alistamento biométrico quando convocado

## Base Legal
- Código Eleitoral, arts. 7º, 8º, 71, 82
- Resolução TSE nº 23.659/2021

## Como Regularizar

### Pagamento de Multa Eleitoral
- Multa por ausência às urnas: R$ 3,51 por eleição (valor básico, pode ser aumentado)
- Pagamento via GRU (Guia de Recolhimento da União) emitida no portal do TSE
- Prazo: pode ser pago a qualquer tempo, mas é exigido para acertos com o serviço público

### Justificativa de Ausência
- Eleitor que não votou pode apresentar justificativa até 60 dias após cada turno
- Justificativas válidas: doença, viagem, trabalho, etc.
- Apresentação via portal do TSE (e-Título) ou presencialmente na zona eleitoral

### Alistamento e Transferência
- Jovem de 16 a 17 anos: alistamento facultativo
- Aos 18 anos: alistamento obrigatório
- Transferência de domicílio eleitoral: possível fora do período eleitoral

## Consequências de Situação Irregular
- Impedimento de obter passaporte
- Impedimento de tomar posse em cargo público
- Restrições para obter empréstimos em instituições públicas
- Impossibilidade de participar de licitações públicas
"""

files["duplicidade de filiação"] = """# Duplicidade de Filiação Partidária — Orientações

## O que é Duplicidade de Filiação
Ocorre quando um eleitor aparece simultaneamente filiado a dois ou mais partidos políticos. A filiação simultânea é vedada pelo art. 22, parágrafo único, da Lei nº 9.096/1995.

## Base Legal
- Lei dos Partidos Políticos (Lei nº 9.096/1995), art. 22, parágrafo único
- Resolução TSE nº 23.571/2018

## Procedimento de Apuração
A Justiça Eleitoral realiza periodicamente o cruzamento dos cadastros partidários para identificar duplicidades. Quando detectada:
1. As partes (partidos e eleitor) são notificadas
2. O eleitor deve optar por um dos partidos em 72h
3. Caso não manifeste opção, cancela-se a última filiação registrada

## Consequências
- Inelegibilidade temporária até regularização
- Possível cancelamento de filiação mais recente
"""

files["cancelamento de inscrição eleitoral"] = """# Cancelamento de Inscrição Eleitoral

## Causas de Cancelamento
- Morte do eleitor
- Condenação criminal transitada em julgado por crime com pena de prisão
- Suspensão de direitos políticos
- Pluralidade de inscrições — cancelamento das mais antigas

## Procedimento de Cancelamento
O cancelamento é feito de ofício pela Justiça Eleitoral ou mediante requerimento fundamentado.

## Base Legal
- Código Eleitoral, art. 71
- Resolução TSE nº 21.538/2003
"""

files["criação de partido e sistema sapf"] = """# Criação de Partido Político e Sistema SAPF

## Requisitos para Criação de Novo Partido
- Coleta de apoiamentos de eleitores: mínimo de 0,5% dos votos válidos na última eleição geral para a Câmara dos Deputados
- Distribuídos por pelo menos 9 estados, com mínimo de 0,1% dos votos válidos em cada
- Uso do SAPF (Sistema de Apoiamentos de Fundação de Partido) do TSE para coleta digital

## SAPF — Sistema de Apoiamentos
- Plataforma online do TSE para coleta de apoiamentos com validação biométrica
- Cada eleitor pode apoiar apenas uma nova agremiação
- Prazo de coleta definido pelo TSE

## Registro no TSE
Após coleta dos apoiamentos, o partido deve registrar seus estatutos no TSE e depois no Cartório de Registro Civil.

## Base Legal
- Lei nº 9.096/1995, arts. 7º a 9º
"""

files["cump de sentença"] = """# Cumprimento de Sentença Eleitoral

## O que é
O cumprimento de sentença na Justiça Eleitoral refere-se à fase de execução de decisões condenatórias — especialmente multas eleitorais e cassações de mandato — após o trânsito em julgado.

## Execução de Multas Eleitorais
- Multas aplicadas pela Justiça Eleitoral são inscritas em Dívida Ativa da União
- Cobrança realizada pela Procuradoria-Geral da Fazenda Nacional (PGFN)

## Cassação de Mandato
- Após trânsito em julgado de decisão que cassa mandato eletivo, o cargo é declarado vago
- O substituto legal assume (vice ou seguinte na lista)

## Base Legal
- Código Eleitoral, arts. 367 a 385
- Lei nº 6.830/1980 (Execução Fiscal)
"""

files["direito de resposta"] = """# Direito de Resposta Eleitoral

## Conceito
O direito de resposta permite ao candidato, partido ou coligação que se sentir ofendido por propaganda eleitoral adversária requerer resposta ou retificação no mesmo veículo de comunicação, com igual destaque e duração/espaço.

## Base Legal
- Lei nº 9.504/1997, art. 58
- Resolução TSE nº 23.610/2019

## Procedimento
1. Petição ao juiz eleitoral ou TRE descrevendo a ofensa e indicando o veículo
2. Prazo: 24h após a divulgação da ofensa para veículos de rádio e TV; 72h para outros
3. O juiz decide em 24h
4. A resposta deve ser veiculada no mesmo horário e com o mesmo destaque

## Ofensas que Geram Direito de Resposta
- Calúnia, injúria ou difamação eleitoral
- Imagens ou áudios adulterados
- Boatos e informações falsas sobre candidatos

## Sanções pelo Descumprimento
- Multa de R$ 5.000,00 a R$ 30.000,00
- Em caso de reincidência, a multa pode ser dobrada
"""

files["duplicidade de inscrições eleitorais"] = """# Duplicidade de Inscrições Eleitorais

## O que é
Ocorre quando um eleitor possui mais de um registro eleitoral (título de eleitor) no sistema da Justiça Eleitoral, seja em municípios diferentes ou até no mesmo município.

## Causas Comuns
- Alistamento em novo município sem cancelar o título anterior
- Erros administrativos no sistema
- Fraudes (tentativa de votar em mais de uma seção)

## Consequências
- Cancelamento automático das inscrições mais antigas (mantém-se a mais recente)
- Em caso de fraude: crime eleitoral (art. 309, CE)

## Base Legal
- Código Eleitoral, art. 71, I
- Resolução TSE nº 21.538/2003
"""

files["prestação de contas anual"] = """# Prestação de Contas Anual dos Partidos Políticos

## O que é
Obrigação anual dos partidos políticos de prestarem contas ao TSE (partidos nacionais) ou TRE (partidos estaduais/municipais) sobre a movimentação financeira do exercício.

## Base Legal
- Lei nº 9.096/1995, arts. 32 a 37
- Resolução TSE nº 23.604/2019

## Sistema de Prestação de Contas Anual (SPCA)
- Plataforma eletrônica do TSE para envio das contas anuais
- Prazo de envio: 30 de abril do ano seguinte ao exercício fiscal

## O que deve ser informado
- Receitas (Fundo Partidário, doações, rendimentos)
- Despesas (pessoal, aluguel, eventos, publicidade)
- Balanço patrimonial

## Sanções
- Contas rejeitadas: suspensão de novas cotas do Fundo Partidário
- Atraso ou não envio: instauração de processo administrativo
"""

files["prestação de contas eleitorais"] = """# Prestação de Contas Eleitorais

## O que é
Todo candidato e comitê financeiro de campanha deve prestar contas à Justiça Eleitoral sobre os recursos recebidos e gastos durante a campanha eleitoral.

## Base Legal
- Lei nº 9.504/1997, arts. 17 a 32
- Resolução TSE nº 23.607/2019

## Sistema de Prestação de Contas Eleitorais (SPCE)
- Plataforma eletrônica do TSE para registro de receitas e despesas de campanha

## Fontes de Recursos Permitidas
- Fundo Especial de Financiamento de Campanha (FEFC)
- Fundo Partidário
- Recursos próprios do candidato (limitado)
- Doações de pessoas físicas (limitadas a 10% da renda bruta declarada no ano anterior)

## Vedações
- Doações de pessoas jurídicas (vedadas desde a ADI 4.650/STF)
- Recursos de origem estrangeira
- Recursos de entidades sem fins lucrativos e sindicatos

## Prazo de Entrega
- Parcial: 30 dias após o último turno em que participou
- Final: até 30 dias após a diplomação

## Sanções
- Contas desaprovadas: multa de 20% sobre valor irregular e inelegibilidade do candidato
"""

files["representação pesquisa eleitoral"] = """# Representação de Pesquisa Eleitoral

## O que é
Pesquisa eleitoral é qualquer levantamento de opinião destinado a conhecer a preferência do eleitorado. Sua realização e divulgação são reguladas pela Justiça Eleitoral.

## Base Legal
- Lei nº 9.504/1997, arts. 33 a 35-A
- Resolução TSE nº 23.600/2019

## Registro Obrigatório
- Toda pesquisa eleitoral deve ser registrada na Justiça Eleitoral até 5 dias antes da divulgação
- Informações obrigatórias: contratante, financiador, metodologia, margem de erro, período de coleta, empresa responsável

## Vedações
- Divulgação de pesquisas nos 5 dias que antecedem a eleição (boca-de-urna de pesquisa)
- Pesquisas com metodologia não registrada

## Representação por Pesquisa Ilegal
- Qualquer partido, candidato ou eleitor pode representar ao TRE ou TSE noticiando pesquisa irregular
- Sanção: multa de R$ 50.000,00 a R$ 100.000,00

## Pesquisa Boca de Urna
- Permitida no dia da eleição, desde que registrada com antecedência
- Resultado só pode ser divulgado após encerramento da votação em todo o território nacional
"""

files["suspop - suspenção de orgão partidário"] = """# Suspensão de Órgão Partidário (SUSPOP)

## O que é
A suspensão de órgão partidário é medida judicial ou administrativa que impede o funcionamento de um diretório ou comissão executiva de partido político (municipal, estadual ou nacional), determinada pela Justiça Eleitoral.

## Base Legal
- Lei nº 9.096/1995, arts. 15 a 19
- Resolução TSE nº 23.571/2018

## Causas de Suspensão
- Irregularidades graves no processo de escolha de dirigentes
- Desrespeito ao estatuto partidário
- Ausência de atos partidários obrigatórios por longo período

## Procedimento
1. Notícia de irregularidade ao TRE ou TSE
2. Contraditório: partido é intimado para se manifestar
3. Decisão de suspensão ou não
4. Após suspensão: Justiça Eleitoral determina a criação de órgão provisório

## Consequências
- Órgão suspenso não pode praticar atos partidários (convenções, filiações, etc.)
- Candidaturas do partido na área afetada podem ser prejudicadas
- Órgão provisório assume as funções até regularização
"""

# Write all reference files
for filename, content in files.items():
    filepath = os.path.join(ref_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# ─── Distractor files to increase noise ───────────────────────────────────────
distractor_dir = os.path.join(workspace, "docs", "legislacao")
os.makedirs(distractor_dir, exist_ok=True)

# Distractor 1
with open(os.path.join(distractor_dir, "constituicao_art14.txt"), "w", encoding="utf-8") as f:
    f.write("""Art. 14 da Constituição Federal — Soberania Popular
A soberania popular será exercida pelo sufrágio universal e pelo voto direto e secreto, com valor igual para todos, e, nos termos da lei, mediante:
I - plebiscito;
II - referendo;
III - iniciativa popular.
""")

# Distractor 2
with open(os.path.join(distractor_dir, "lei_9504_resumo.txt"), "w", encoding="utf-8") as f:
    f.write("""Lei nº 9.504/1997 — Lei das Eleições
Esta lei estabelece normas para as eleições no Brasil.
Artigo 1º: As eleições para Presidente da República, Governador de Estado e do Distrito Federal, Prefeito, Senador, Deputado Federal, Deputado Estadual, Deputado Distrital e Vereador dar-se-ão, em todo o País, simultaneamente...
[documento truncado — versão incompleta para referência rápida]
""")

# Distractor 3
with open(os.path.join(distractor_dir, "glossario_eleitoral.txt"), "w", encoding="utf-8") as f:
    f.write("""Glossário Eleitoral Básico
TSE: Tribunal Superior Eleitoral
TRE: Tribunal Regional Eleitoral
CE: Código Eleitoral
HGPE: Horário Gratuito de Propaganda Eleitoral
FEFC: Fundo Especial de Financiamento de Campanha
DRAP: Demonstrativo de Regularidade de Atos Partidários
RARC: Requerimento de Registro de Candidatura
""")

# Distractor 4
misc_dir = os.path.join(workspace, "misc")
os.makedirs(misc_dir, exist_ok=True)
with open(os.path.join(misc_dir, "notas_internas.txt"), "w", encoding="utf-8") as f:
    f.write("Notas internas — NÃO USE PARA RESPOSTAS\nEste arquivo contém rascunhos e não deve ser utilizado como base para nenhuma resposta.\n")

# Distractor 5
with open(os.path.join(misc_dir, "template_antigo.md"), "w", encoding="utf-8") as f:
    f.write("""# Template Antigo (Descontinuado)
Este template foi substituído. Use o fluxo descrito no SKILL.md.
""")

# Distractor 6
logs_dir = os.path.join(workspace, "logs")
os.makedirs(logs_dir, exist_ok=True)
with open(os.path.join(logs_dir, "session_20240101.log"), "w", encoding="utf-8") as f:
    f.write("[2024-01-01 10:00:00] Session started\n[2024-01-01 10:05:00] Query received\n[2024-01-01 10:05:01] Response sent\n")

# Distractor 7
with open(os.path.join(logs_dir, "errors.log"), "w", encoding="utf-8") as f:
    f.write("[ERROR] Timeout connecting to database at 2024-01-15 08:30:00\n")

# Distractor 8
config_dir = os.path.join(workspace, "config")
os.makedirs(config_dir, exist_ok=True)
with open(os.path.join(config_dir, "app_config.json"), "w", encoding="utf-8") as f:
    f.write('{"environment": "production", "log_level": "INFO", "max_tokens": 1024}\n')

# Distractor 9
with open(os.path.join(config_dir, "whatsapp_settings.json"), "w", encoding="utf-8") as f:
    f.write('{"api_version": "v17.0", "phone_number_id": "REDACTED", "webhook_verify_token": "REDACTED"}\n')

# Distractor 10
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)
with open(os.path.join(scripts_dir, "deploy.sh"), "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\n# Deployment script — do not modify\necho 'Deploying...'\n")

# Distractor 11
with open(os.path.join(workspace, "references", "LEIA-ME-OBSOLETO.txt"), "w", encoding="utf-8") as f:
    f.write("Este arquivo está desatualizado. Consulte o indice-temas.md para a versão atual.\n")

print("Workspace generated successfully.")
print(f"Reference files created: {len(files)}")
print(f"Distractor files created: 11")