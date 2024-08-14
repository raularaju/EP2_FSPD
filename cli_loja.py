from __future__ import print_function # usado internamente nos stubs
import os
import sys
import grpc

import loja_pb2, loja_pb2_grpc, banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC

MINHA_CARTEIRA = None # nome da carteira do cliente
PRECO_PRODUTO = 0 

def compra(stub_loja, stub_banco):
    """
    Faz uma compra na loja
    stub_loja : stub da Loja
    stub_banco : stub do Banco
    """
    response = stub_banco.cria_ordem(banco_pb2.RequestCriaOrdem(carteira = MINHA_CARTEIRA, valor = PRECO_PRODUTO))
    print(f"{response.status}")
    if response.status > 0:
        response = stub_loja.vender(loja_pb2.RequestVender(ordem = response.status))
        print(f"{response.status}")


def termina_exec(stub_loja):
    """
    Termina execução do vervidor da loja e do banco
    stub_loja : stub da loja
    """
    response = stub_loja.termina_exec(loja_pb2.RequestTerminaExec())
    print(f"{response.saldo} {response.n_pendencias}")


def processa_comandos(stub_loja, stub_banco):
    """
    Processa os comandos da stdin
    stub_loja : stub da Loja
    stub_banco : stub do Banco
    """
    opcoes_validas = ['C', 'T']
    for line in sys.stdin:

        if not line or not line.strip() or line.strip() == '' or line[0] not in opcoes_validas: # linha inválida
            continue

        operacao, *args = line.strip().split()
        if operacao == 'C':
            compra(stub_loja, stub_banco)
        elif operacao == 'T':
            termina_exec(stub_loja)
            return

def run():
    _, carteira, servidor_banco, servidor_loja = sys.argv

    global MINHA_CARTEIRA 
    MINHA_CARTEIRA = carteira
    
    channel_loja = grpc.insecure_channel(servidor_loja)
    stub_loja = loja_pb2_grpc.LojaStub(channel_loja)
    response = stub_loja.le_preco(loja_pb2.RequestLePreco())
    global PRECO_PRODUTO
    PRECO_PRODUTO = response.preco

    channel_banco = grpc.insecure_channel(servidor_banco)
    stub_banco = banco_pb2_grpc.BancoStub(channel_banco)

    processa_comandos(stub_loja, stub_banco)
    
    channel_loja.close()
    channel_banco.close()


if __name__ == '__main__':
    run()
