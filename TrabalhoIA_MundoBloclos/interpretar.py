"""Lê uma resposta do MiniSat e o MAP da mesma situação."""

import argparse
from pathlib import Path
from bw2cnf_var import BLOCKS, sobrepoe


def derivar_on(estado):
    apoios = {}
    for b, (p, l) in estado.items():
        apoios[b] = ["T"] if l == 0 else [
            y for y, (q, h) in estado.items()
            if y != b and h == l - 1 and sobrepoe(b, p, y, q)
        ]
    return apoios


def interpretar(resultado, mapa):
    linhas = resultado.read_text(encoding="utf-8").split()
    if linhas[0] == "UNSAT":
        print("Não há plano para o horizonte escolhido.")
        return
    if linhas[0] != "SAT":
        raise ValueError("O resultado deve começar com SAT ou UNSAT.")
    verdadeiros = {int(x) for x in linhas[1:] if int(x) > 0}
    simbolos = {}
    for linha in mapa.read_text(encoding="utf-8").splitlines():
        numero, simbolo = linha.split(maxsplit=1)
        simbolos[int(numero)] = simbolo

    acoes, posicoes, niveis = [], {}, {}
    for numero in sorted(verdadeiros):
        simbolo = simbolos[numero]
        nome, parametros = simbolo[:-1].split("(")
        args = parametros.split(",")
        if nome == "move":
            b, y, p, t = args
            acoes.append((int(t), b, y, int(p)))
        elif nome in ("at", "lev"):
            b, valor, t = args
            destino = posicoes if nome == "at" else niveis
            destino[b, int(t)] = int(valor)

    print(f"PLANO ENCONTRADO ({len(acoes)} ações):")
    for t, b, y, p in sorted(acoes):
        destino = "a MESA" if y == "T" else f"cima de '{y}'"
        print(f"  {t + 1}. t={t}: mover '{b}' para {destino}, no ponto p={p}.")

    final = max(t for b, t in posicoes)
    estado = {b: (posicoes[b, final], niveis[b, final]) for b in BLOCKS}
    print(f"\nESTADO FINAL (t={final}):")
    for b, (p, l) in estado.items():
        print(f"  {b}: p={p}, nível={l}, intervalo=[{p},{p + BLOCKS[b]}].")
    print("\nRELAÇÕES on:")
    for b, apoios in derivar_on(estado).items():
        descricao = "na MESA" if apoios == ["T"] else "sobre: " + ", ".join(apoios)
        print(f"  {b} está {descricao}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resultado", type=Path)
    args = parser.parse_args()
    interpretar(args.resultado, args.resultado.parent / "trab01_blocos2SAT.map")


if __name__ == "__main__":
    main()
