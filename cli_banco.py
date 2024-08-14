from __future__ import print_function # usado internamente nos stubs
import os
import sys
import grpc

import banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC

MINHA_CARTEIRA = None # nome da carteira do cliente

def le_saldo(stub):
    """
    Lê o saldo da carteira
    stub : stub do Banco
    """
    response = stub.le_saldo(banco_pb2.RequestLeSaldo(carteira = MINHA_CARTEIRA))
    print(f"{response.valor}")

def cria_ordem(stub, valor):
    """
    Cria uma ordem de pagamento
    stub : stub do Banco
    valor : valor do pagamento
    """
    response = stub.cria_ordem(banco_pb2.RequestCriaOrdem(carteira = MINHA_CARTEIRA, valor = valor))
    print(f"{response.status}")

def transfere(stub, opag, valor, destino):
    """
    Faz uma transferência
    stub : stub do Banco
    opag : número da ordem de pagamento
    valor : valor da transferência
    destino : carteira destino
    """
    response = stub.transfere(banco_pb2.RequestTransfere(carteira = destino, ordem = opag, conferencia = valor))
    print(f"{response.status}")

def termina_exec(stub):
    """
    Termina do servidor de banco
    stub : stub do Banco
    """
    response = stub.termina_exec(banco_pb2.RequestTerminaExec())
    print(f"{response.n_pendencias}")

def processa_comandos(stub):
    opcoes_validas = ['S', 'O', 'X', 'F']
    for line in sys.stdin:
        if not line or not line.strip() or line[0] not in opcoes_validas: # linha inválida
            continue
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
    stub = banco_pb2_grpc.BancoStub(channel)


    processa_comandos(stub)
    
    channel.close()


if __name__ == '__main__':
    run()

# python3 cli_banco.py Dorgival 0.0.0.0:8888