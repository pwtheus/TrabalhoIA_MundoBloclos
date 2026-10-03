"""Converte um dos três cenários em CNF e, opcionalmente, usa MiniSat 2.2."""

import argparse
from itertools import combinations
from pathlib import Path

BLOCKS = {"a": 1, "b": 1, "c": 2, "d": 3}
MAX_POINT = 6
MAX_LEVEL = 3

# Cada par indica (ponto inicial, nível). T é o nome da mesa.
CENARIOS = {
    1: ({"a": (3, 0), "b": (5, 0), "c": (0, 0), "d": (3, 1)},
        {"a": (0, 1), "b": (5, 0), "c": (0, 0), "d": (2, 0)}, 4),
    2: ({"a": (0, 1), "b": (1, 1), "c": (0, 0), "d": (3, 0)},
        {"a": (4, 2), "b": (5, 2), "c": (4, 1), "d": (3, 0)}, 5),
    3: ({"a": (3, 0), "b": (5, 0), "c": (0, 0), "d": (3, 1)},
        {"a": (0, 1), "b": (1, 1), "c": (0, 0), "d": (3, 0)}, 6),
}


def posicoes(b):
    return range(MAX_POINT - BLOCKS[b] + 1)


def slots(b, p):
    return range(p, p + BLOCKS[b])


def sobrepoe(b, p, y, q):
    return p < q + BLOCKS[y] and q < p + BLOCKS[b]


def gerar_cnf(inicial, meta, horizonte):
    """Cria variáveis numeradas e cláusulas, sem fixar um plano de ações."""
    ids, clausulas = {}, []

    def var(nome, *args):
        simbolo = f"{nome}({','.join(map(str, args))})"
        if simbolo not in ids:
            ids[simbolo] = len(ids) + 1
        return ids[simbolo]

    def no_maximo_uma(lista):
        for x, y in combinations(lista, 2):
            clausulas.append([-x, -y])

    def exatamente_uma(lista):
        clausulas.append(lista)
        no_maximo_uma(lista)

    # Estados: posição, nível, ocupação, colisões, estabilidade e topo livre.
    for t in range(horizonte + 1):
        celulas = {(s, l): [] for s in range(MAX_POINT)
                   for l in range(MAX_LEVEL + 1)}
        for b in BLOCKS:
            exatamente_uma([var("at", b, p, t) for p in posicoes(b)])
            exatamente_uma([var("lev", b, l, t) for l in range(MAX_LEVEL + 1)])
            for p in posicoes(b):
                for l in range(MAX_LEVEL + 1):
                    # pos(b,p,l,t) <-> at(b,p,t) AND lev(b,l,t).
                    z = var("pos", b, p, l, t)
                    a, h = var("at", b, p, t), var("lev", b, l, t)
                    clausulas.extend([[-z, a], [-z, h], [-a, -h, z]])
                    for s in slots(b, p):
                        celulas[s, l].append(z)

                    if l > 0:
                        abaixo = [var("occ", s, l - 1, t) for s in slots(b, p)]
                        minimo = (BLOCKS[b] + 1) // 2
                        # Pelo menos k de n: toda seleção de n-k+1 contém um true.
                        for grupo in combinations(abaixo, len(abaixo) - minimo + 1):
                            clausulas.append([-z, *grupo])

                    # clr é verdadeiro exatamente quando não há bloco acima.
                    acima = [var("occ", s, h, t) for s in slots(b, p)
                             for h in range(l + 1, MAX_LEVEL + 1)]
                    livre = var("clr", b, t)
                    clausulas.append([-z, livre, *acima])
                    for ocupado in acima:
                        clausulas.append([-z, -livre, -ocupado])

        for (s, l), ocupantes in celulas.items():
            ocupado = var("occ", s, l, t)
            # occ <-> OR dos blocos que podem ocupar esta célula.
            clausulas.append([-ocupado, *ocupantes])
            for z in ocupantes:
                clausulas.append([-z, ocupado])
            no_maximo_uma(ocupantes)

    # Estado inicial e meta: só estes estados são fixados, nunca os intermediários.
    for estado, t in [(inicial, 0), (meta, horizonte)]:
        for b, (p, l) in estado.items():
            clausulas.extend([[var("at", b, p, t)], [var("lev", b, l, t)]])

    for t in range(horizonte):
        acoes, por_bloco = [], {b: [] for b in BLOCKS}
        for b in BLOCKS:
            for y in ["T"] + [x for x in BLOCKS if x != b]:
                for p in posicoes(b):
                    m = var("move", b, y, p, t)
                    acoes.append(m)
                    por_bloco[b].append(m)
                    clausulas.append([-m, var("clr", b, t)])
                    clausulas.append([-m, var("at", b, p, t + 1)])
                    # O bloco chega livre: não pode entrar sob uma ponte.
                    # Colisões em t+1 garantem espaço no nível de destino.
                    clausulas.append([-m, var("clr", b, t + 1)])

                    if y == "T":
                        clausulas.append([-m, var("lev", b, 0, t + 1)])
                        clausulas.append([-m, -var("at", b, p, t),
                                          -var("lev", b, 0, t)])
                    else:
                        # Basta a região utilizada estar livre; o apoio pode
                        # sustentar outro bloco ao lado, como nas figuras.
                        permitidas = [var("at", y, q, t) for q in posicoes(y)
                                      if sobrepoe(b, p, y, q)]
                        clausulas.append([-m, *permitidas])
                        clausulas.append([-m, -var("lev", y, MAX_LEVEL, t)])
                        clausulas.append([-m, -var("clr", y, t + 1)])
                        for l in range(MAX_LEVEL):
                            apoio = var("lev", y, l, t)
                            clausulas.append([-m, -apoio, var("lev", b, l + 1, t + 1)])
                            # Proíbe ação que mantenha posição E nível iguais.
                            clausulas.append([-m, -apoio, -var("at", b, p, t),
                                              -var("lev", b, l + 1, t)])

        exatamente_uma(acoes)
        # Frame axioms: se b não se move, sua posição e seu nível persistem.
        # clr e on acompanham a geometria, inclusive a retirada de um apoio.
        for b in BLOCKS:
            for nome, valores in [("at", posicoes(b)),
                                  ("lev", range(MAX_LEVEL + 1))]:
                for valor in valores:
                    antes = var(nome, b, valor, t)
                    depois = var(nome, b, valor, t + 1)
                    clausulas.append([-antes, depois, *por_bloco[b]])
                    clausulas.append([antes, -depois, *por_bloco[b]])
    return ids, clausulas


def salvar(ids, clausulas, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    cnf = pasta / "trab01_blocos2SAT.cnf"
    mapa = pasta / "trab01_blocos2SAT.map"
    with cnf.open("w", encoding="utf-8") as arq:
        arq.write(f"p cnf {len(ids)} {len(clausulas)}\n")
        for clausula in clausulas:
            arq.write(" ".join(map(str, clausula)) + " 0\n")
    with mapa.open("w", encoding="utf-8") as arq:
        for simbolo, numero in ids.items():
            arq.write(f"{numero} {simbolo}\n")
    print(f"Gerados: {cnf} e {mapa}")
    return cnf


def resolver(cnf, resultado):
    from pysat.formula import CNF
    from pysat.solvers import Minisat22

    formula = CNF(from_file=str(cnf))
    with Minisat22(bootstrap_with=formula.clauses) as solver:
        satisfaz = solver.solve()
        with resultado.open("w", encoding="utf-8") as arq:
            if satisfaz:
                arq.write("SAT\n" + " ".join(map(str, solver.get_model())) + " 0\n")
            else:
                arq.write("UNSAT\n")
    print(f"{'SAT' if satisfaz else 'UNSAT'}: {resultado}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("situacao", type=int, choices=CENARIOS)
    parser.add_argument("--resolver", action="store_true", help="executar MiniSat 2.2")
    args = parser.parse_args()
    inicial, meta, horizonte = CENARIOS[args.situacao]
    pasta = Path(__file__).resolve().parent / f"situacao{args.situacao}"
    ids, clausulas = gerar_cnf(inicial, meta, horizonte)
    cnf = salvar(ids, clausulas, pasta)
    if args.resolver:
        resolver(cnf, pasta / f"resultado{args.situacao}.txt")


if __name__ == "__main__":
    main()
