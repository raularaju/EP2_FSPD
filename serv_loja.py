import sys
from concurrent import futures # usado na definição do pool de threads
import threading
import grpc

import loja_pb2, loja_pb2_grpc, banco_pb2_grpc, banco_pb2 # módulos gerados pelo compilador de gRPC


class Loja(loja_pb2_grpc.LojaServicer):
    def __init__(self, stop_event, banco_stub, preco, carteira, saldo):
        """
        stop_event : evento de parada necessário para terminar a execução do servidor
        banco_stub : stub do Banco
        preco : preço do produto
        carteira : nome da carteira do cliente
        saldo : saldo da loja
        """
        self._stop_event = stop_event
        self._banco_stub = banco_stub
        self._preco = preco
        self._carteira = carteira
        self._saldo = saldo 

    def le_preco(self, request, context):
        """
        Retorna o preço do produto
        """
        return loja_pb2.ReplyLePreco(preco = self._preco)

    def vender(self, request, context):
        """
        Realiza uma venda
        request : RequestVender
        """
        try:
            response = self._banco_stub.transfere(banco_pb2.RequestTransfere(carteira = self._carteira, ordem = request.ordem, conferencia = self._preco))
            if(response.status == 0):
                self._saldo += self._preco
            return loja_pb2.ReplyVender(status = response.status)
        except grpc.RpcError as e: # erro de comunicação com o servidor do banco
            return loja_pb2.ReplyVender(status = -9)

    def termina_exec(self, request, context):
        """
        Termina a execução do servidor do banco e da loja
        request : RequestTerminaExec
        """
        response = self._banco_stub.termina_exec(banco_pb2.RequestTerminaExec())
        self._stop_event.set()
        return loja_pb2.ReplyTerminaExec(saldo = self._saldo, n_pendencias = response.n_pendencias)

def serve():
    _ , preco, port, carteira, serv_banco = sys.argv
    preco = int(preco)

    # Conecta ao servidor do banco e consulta saldo
    channel = grpc.insecure_channel(serv_banco)
    stub_banco = banco_pb2_grpc.BancoStub(channel)
    response = stub_banco.le_saldo(banco_pb2.RequestLeSaldo(carteira = carteira))
    saldo = response.valor


    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    loja_pb2_grpc.add_LojaServicer_to_server(Loja(stop_event, stub_banco, preco, carteira, saldo), server)
    server.add_insecure_port(f'0.0.0.0:{port}')
    server.start()
    stop_event.wait()
    server.stop(grace=None)

if __name__ == '__main__':
    serve()
    
