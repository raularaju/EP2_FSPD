from __future__ import print_function # usado internamente nos stubs
import os
import sys
import grpc

import loja_pb2, loja_pb2_grpc, banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC

MINHA_CARTEIRA = None
PRECO_PRODUTO = 0

def compra(stub_loja, stub_banco):
    response = stub_banco.cria_ordem(banco_pb2.RequestCriaOrdem(carteira = MINHA_CARTEIRA, valor = PRECO_PRODUTO))
    print(f"Ordem criada: {response.status}")
    if response.status > 0:
        response = stub_loja.vender(loja_pb2.RequestVender(ordem = response.status))
        print(f"Status Venda: {response.status}")


def termina_exec_loja(stub):
    response = stub.termina_exec(loja_pb2.RequestTerminaExec())
    print(f"Fim loja: {response.saldo}")

def termina_exec_banco(stub):
    response = stub.termina_exec(banco_pb2.RequestTerminaExec())
    print(f"Fim banco: {response.n_pendencias}")

def processa_comandos(stub_loja, stub_banco):
    for line in sys.stdin:
        operacao, *args = line.strip().split()
        if operacao == 'C':
            compra(stub_loja, stub_banco)
        elif operacao == 'T':
            termina_exec_loja(stub_loja)
            return
        elif operacao == 'F':
            termina_exec_banco(stub_banco)
            return

def run():
    _, carteira, servidor_banco, servidor_loja = sys.argv

    global MINHA_CARTEIRA 
    MINHA_CARTEIRA = carteira
    
    channel_loja = grpc.insecure_channel(servidor_loja)
    stub_loja = loja_pb2_grpc.DoStuffStub(channel_loja)
    response = stub_loja.le_preco(loja_pb2.RequestLePreco())
    global PRECO_PRODUTO
    PRECO_PRODUTO = response.preco

    channel_banco = grpc.insecure_channel(servidor_banco)
    stub_banco = banco_pb2_grpc.DoStuffStub(channel_banco)

    processa_comandos(stub_loja, stub_banco)
    
    channel_loja.close()
    channel_banco.close()


if __name__ == '__main__':
    run()

# python3 cli_loja.py Bezos 0.0.0.0:8888 0.0.0.0:8889