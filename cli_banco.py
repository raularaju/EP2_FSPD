from __future__ import print_function # usado internamente nos stubs
import os
import sys
import grpc

import banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC

MINHA_CARTEIRA = None

def le_saldo(stub):
    response = stub.le_saldo(banco_pb2.RequestLeSaldo(carteira = MINHA_CARTEIRA))

    print(f"Saldo Conta: {response.valor}")

def cria_ordem(stub, valor):
    response = stub.cria_ordem(banco_pb2.RequestCriaOrdem(carteira = MINHA_CARTEIRA, valor = valor))
    print(f"Ordem criada: {response.status}")

def transfere(stub, opag, valor, destino):
    response = stub.transfere(banco_pb2.RequestTransfere(carteira = destino, ordem = opag, conferencia = valor))
    print(f"Transferência: {response.status}")

def termina_exec(stub):
    response = stub.termina_exec(banco_pb2.RequestTerminaExec())
    print(f"Operações pendentes: {response.n_pendencias}")

def processa_comandos(stub):
    for line in sys.stdin:
        operacao, *args = line.strip().split()
        if operacao == 'S':
            le_saldo(stub)
        elif operacao == 'O':
            cria_ordem(stub, int(args[0]))
        elif operacao == 'X':
            transfere(stub, int(args[0]), int(args[1]), args[2])
        elif operacao == 'F':
            termina_exec(stub)
            return
def run():
    _, carteira, servidor = sys.argv

    global MINHA_CARTEIRA 
    MINHA_CARTEIRA = carteira
    
    channel = grpc.insecure_channel(servidor)
    stub = banco_pb2_grpc.DoStuffStub(channel)


    processa_comandos(stub)
    
    channel.close()


if __name__ == '__main__':
    run()

# python3 cli_banco.py Dorgival 0.0.0.0:8888