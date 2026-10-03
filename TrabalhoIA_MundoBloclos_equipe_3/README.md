*** Mundo dos Blocos de Tamanho Variável

Fundamentos de Inteligência Artificial - UFAM / ICOMP

**Integrantes:** Camila dos Santos Soares; Daniel Nunes Santos; Fernando Reis; Nicoly Lima de Souza; Pedro Matheus Melo Pereira; Pedro Vinícius Diaz de Alencar.

** 1. Introdução ao Problema

O objetivo é mover blocos de comprimentos diferentes sem colisões e com apoio suficiente. Resolvemos três casos: Situação 1 até Sf4, Situação 2 até S5 e Situação 3 até S7. Primeiro definimos o domínio e os planos manuais; depois usamos Python e MiniSat 2.2 para gerar planos a partir de cláusulas CNF.

** 2. Descrição Formal do Mundo dos Blocos de Tamanho Variado

*** Domínio em LPO. 
Os blocos são `B={a,b,c,d}`, com `len(a)=1`, `len(b)=1`, `len(c)=2` e `len(d)=3`. A mesa é `T`. Há sete pontos, de 0 a 6, e seis slots: `s0=[0,1]`, ..., `s5=[5,6]`. Um bloco em `p` cobre os slots de `p` até `p+len(b)-1`. As posições válidas são `0 <= p <= 6-len(b)` e os níveis vão de 0 a 3; nível 0 significa mesa. Blocos que apenas encostam pelas bordas não compartilham slots.

| Predicado    | Significado no instante t                      |
| ------------ | ---------------------------------------------- |
| `at(b,p,t)`  | O bloco b começa no ponto p.                   |
| `lev(b,l,t)` | O bloco b está no nível l.                     |
| `clr(b,t)`   | Nenhum bloco mais alto cobre slots de b.       |
| `on(b,y,t)`  | b tem apoio em y; pode haver mais de um apoio. |

Cada bloco possui exatamente uma posição e um nível. Definimos `cov(b,s,l,t)` como `lev(b,l,t)` e a existência de `p` com `at(b,p,t)` e `p <= s < p+len(b)`. Para blocos, `on(b,y,t)` vale se estão em níveis consecutivos e compartilham ao menos um slot; `on(b,T,t)` equivale a `lev(b,0,t)`. `clr(b,t)` vale se não existe outro bloco em nível maior cobrindo algum slot de b. Essas condições são quantificadas sobre todos os blocos e instantes do domínio.

*** Estabilidade. 
Para todo bloco acima da mesa, pelo menos `ceil(len(b)/2)` slots sob ele devem estar ocupados no nível imediatamente inferior. Assim, a e b precisam de 1 slot de apoio, c de 1 e d de 2. Conta-se o conjunto de slots apoiados, permitindo a ponte de d sobre a e b com um vão no meio.

*** Ação: 
`move(b,y,p,t)` coloca b sobre y a partir de p. Exige b livre, posição válida, destino diferente do atual, espaço no destino e acima dele, além da estabilidade após o movimento. Se y é bloco, deve haver sobreposição horizontal e o novo nível é `nivel(y)+1`; se y é a mesa, é 0. Uma ação ocorre por passo, sem transportar outros blocos.

Para reproduzir os blocos lado a lado nas figuras, substituímos `clr(y)` do manual por espaço livre na região utilizada do apoio. O bloco movido continua exigindo `clr` e não pode ser colocado sob outro bloco, inclusive no vão de uma ponte.

| Efeito      | O que acontece                                                                                                        |
| ----------- | --------------------------------------------------------------------------------------------------------------------- |
| Adds        | Nova posição, novo nível, novos apoios; antigos apoios ficam livres se nada permanecer acima.                         |
| Deletes     | Posição e nível antigos quando diferentes, apoios perdidos e `clr` dos apoios agora cobertos.                         |
| Permanência | Posição e nível dos demais blocos; comprimentos, mesa, pontos e slots não mudam. `clr` e `on` acompanham a geometria. |

*** Ordem parcial:
 `A -- P --> B` significa que A estabelece a condição P necessária a B, preservada entre as duas ações. Na Situação 1, chamar os quatro movimentos manuais de A1 a A4 dá: `A1 -- clr(a) --> A2`, `A2 -- slot s3 livre na mesa --> A3` e `A3 -- clr(c) --> A4`. Movimentos sem dependência podem trocar de ordem. As pré-condições e a permanência representam essas dependências; o SAT produz uma sequência compatível, sem receber o plano manual como restrição.

Por exemplo, na Situação 2 automática, após colocar c sobre d, os movimentos finais de a e b podem trocar de ordem, pois usam slots distintos de c.

** 3. Codificação CNF

Substituímos as variáveis da LPO pelos blocos, posições, níveis e instantes possíveis. Cada átomo vira uma variável booleana numerada. Usamos `at`, `lev`, `clr` e `move`, além das auxiliares `pos(b,p,l,t)` (posição e nível juntos) e `occ(s,l,t)` (slot ocupado). `on` é reconstruído, sem variável própria. Os horizontes são H=4, 5 e 6, com estados de 0 a H e ações de 0 a H-1.

| Grupo de cláusulas      | Regra codificada                                                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Inicial e meta          | Fixam `at` e `lev` nos extremos do plano.                                                                                      |
| Unicidade e colisões    | Uma posição e um nível por bloco; no máximo um ocupante por célula.                                                            |
| Estabilidade e clear    | Apoio mínimo abaixo; `clr` equivale à ausência de ocupação acima.                                                              |
| Pré-condições e efeitos | Bloco livre, apoio compatível, destino livre, nova posição e novo nível; sem ação vazia.                                       |
| Frame axioms            | Sem movimento de b, seus `at` e `lev` permanecem. A definição de `clr` preserva seu valor enquanto a ocupação acima não mudar. |
| Ação única              | Exatamente um `move` por instante.                                                                                             |

Exemplos: `move -> clr` vira `not move OR clr`. `pos <-> (at AND lev)` vira `(not pos OR at) AND (not pos OR lev) AND (not at OR not lev OR pos)`. Para d, os três slots de apoio x, y, z exigem `(x OR y) AND (x OR z) AND (y OR z)`, condicionado à posição de d. O DIMACS grava os IDs das variáveis, usa sinal negativo para negação e termina cada cláusula com `0`.

** 4. Exemplos dos 3 Cenários Codificados para CNF em LP

Em cada par `(p,l)`, leia `at(bloco,p,t) AND lev(bloco,l,t)`. Todos os pares da linha valem juntos: inicialmente em t=0 e na meta em t=H. As linhas fixam os átomos correspondentes com cláusulas unitárias.

| Situação / estado | a     | b     | c     | d     |
| ----------------- | ----- | ----- | ----- | ----- |
| 1 e 3: S0         | (3,0) | (5,0) | (0,0) | (3,1) |
| 1: Sf4            | (0,1) | (5,0) | (0,0) | (2,0) |
| 2: S0             | (0,1) | (1,1) | (0,0) | (3,0) |
| 2: S5             | (4,2) | (5,2) | (4,1) | (3,0) |
| 3: S7             | (0,1) | (1,1) | (0,0) | (3,0) |

*** Planos manuais.
 Na tabela, `move(b,y,p)` omite apenas o instante, que é o número do passo menos 1. O par após a seta é a nova posição e nível do bloco movido; os outros permanecem iguais. Isso permite acompanhar todos os estados até a meta.

| Passo | Situação 1            | Situação 2            | Situação 3            |
| ----- | --------------------- | --------------------- | --------------------- |
| 1     | `move(d,c,0)` → (0,1) | `move(b,T,2)` → (2,0) | `move(d,c,0)` → (0,1) |
| 2     | `move(a,b,5)` → (5,1) | `move(a,b,2)` → (2,1) | `move(a,b,5)` → (5,1) |
| 3     | `move(d,T,2)` → (2,0) | `move(c,d,4)` → (4,1) | `move(d,T,2)` → (2,0) |
| 4     | `move(a,c,0)` → (0,1) | `move(a,c,4)` → (4,2) | `move(a,c,0)` → (0,1) |
| 5     | —                     | `move(b,c,5)` → (5,2) | `move(b,c,1)` → (1,1) |
| 6     | —                     | —                     | `move(d,T,3)` → (3,0) |

Nas Situações 1 e 3, a vai temporariamente sobre b: deixá-lo em p=4 na mesa, como no exemplo do manual, impediria d de ocupar `[2,5]`. Na Situação 3, S5 e S6 desenham a mesma configuração; não é necessário inserir um movimento vazio.

*** Comparação com as execuções reais:

| Situação | Manual / solver | Comparação                                                                                                                                      |
| -------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1        | 4 / 4 ações     | Mesma sequência, chegando a Sf4.                                                                                                                |
| 2        | 5 / 5 ações     | Solver: `b,T,2`; `a,d,3`; `c,d,4`; `b,c,5`; `a,c,4`. Usa outro apoio temporário para a e inverte os dois últimos movimentos; chega ao mesmo S5. |
| 3        | 6 / 6 ações     | Mesma sequência, chegando a S7.                                                                                                                 |

Os três resultados são SAT. Os horizontes vêm dos planos manuais; não se afirma optimalidade. No início das Situações 1 e 3, `on(d,a,0)` e `on(d,b,0)` descrevem a ponte. Ao final: em Sf4, a está sobre c; em S5, a e b estão sobre c e c sobre d; em S7, a e b estão sobre c. Os blocos restantes estão na mesa.

** 5. Mapeamento: Descrição Formal para Código

| Conceito                        | Parte do código                                                   |
| ------------------------------- | ----------------------------------------------------------------- |
| Blocos, comprimentos e cenários | `BLOCKS`, `MAX_POINT`, `MAX_LEVEL`, `CENARIOS` em `bw2cnf_var.py` |
| Posições, slots e sobreposição  | `posicoes`, `slots`, `sobrepoe`                                   |
| Predicados, ações e regras CNF  | `gerar_cnf`; `var` numera os símbolos                             |
| DIMACS e MAP                    | `salvar`                                                          |
| MiniSat 2.2 e resposta numérica | `resolver`                                                        |
| Plano legível e apoios          | `interpretar` e `derivar_on` em `interpretar.py`                  |

** 6. Execução Passo a Passo: Gerar o CNF, Mapeamento e Execução

No Linux, abra o terminal dentro de `TrabalhoIA_MundoBloclos`. Prepare o ambiente uma vez (em Ubuntu/Mint, se faltar venv, instale `python3-venv` com o gerenciador de pacotes):

```bash
python3 -m venv ../.venv_blocos
source ../.venv_blocos/bin/activate
python3 -m pip install -r requirements.txt
```

Gere CNF e MAP, execute MiniSat e interprete os três resultados:

```bash
for i in 1 2 3; do
    python3 bw2cnf_var.py "$i" --resolver
    python3 -B interpretar.py "situacao$i/resultado$i.txt"
done
```

O argumento 1, 2 ou 3 seleciona a situação. Sem `--resolver`, o primeiro comando apenas gera CNF e MAP. Com essa opção, lê o CNF salvo e executa MiniSat 2.2 pela biblioteca [PySAT](https://pysathq.github.io/docs/html/api/solvers.html), sem instalar outro executável. Cada pasta `situacaoN` recebe seu CNF, MAP e `resultadoN.txt`. A opção `-B` evita criar cache do Python. Em um novo terminal, reative o ambiente com `source ../.venv_blocos/bin/activate`.

** 7. Interpretação da Saída do SAT Solver

`resultadoN.txt` contém `SAT` e o modelo real do solver: números positivos são variáveis verdadeiras e negativos são falsas. `UNSAT` indicaria ausência de plano no horizonte usado. O MAP associa cada número a um símbolo, por exemplo, `move(d,c,0,0)`.

`interpretar.py` lê o MAP da mesma pasta, seleciona as ações verdadeiras e ordena por t. Exemplo de saída: `t=0: mover 'd' para cima de 'c', no ponto p=0.` Depois mostra posições e níveis finais e reconstrói `on`: nível 0 indica mesa; nos demais níveis, procura todos os blocos no nível imediatamente inferior com slots compartilhados. Assim, reconhece tanto um apoio simples quanto uma ponte. Não se deve misturar o resultado de uma situação com o MAP de outra.
