import sys
from concurrent import futures # usado na definição do pool de threads
import threading
import grpc

import loja_pb2, loja_pb2_grpc, banco_pb2_grpc, banco_pb2 # módulos gerados pelo compilador de gRPC
PRECO = 1
MINHA_CARTEIRA = None
MEU_SALDO = 0
# Os procedimentos oferecidos aos clientes precisam ser encapsulados
#   em uma classe que herda do código do stub.
class DoStuff(loja_pb2_grpc.DoStuffServicer):
    def __init__(self, stop_event, banco_stub):
        self._stop_event = stop_event
        self._banco_stub = banco_stub

   # A assinatura de todos os procedimentos é igual: um objeto com os
   # parâmetros e outro com o contexto de execução do servidor
    def le_preco(self, request, context):
        return loja_pb2.ReplyLePreco(preco = PRECO)

    def vender(self, request, context):
        try:
            response = self._banco_stub.transfere(banco_pb2.RequestTransfere(carteira = MINHA_CARTEIRA, ordem = request.ordem, conferencia = PRECO))
            if(response.status == 0):
                global MEU_SALDO
                MEU_SALDO += PRECO
            return loja_pb2.ReplyVender(status = response.status)
        except grpc.RpcError as e:
            return loja_pb2.ReplyVender(status = -9)

    def termina_exec(self, request, context):
        self._stop_event.set()
        return loja_pb2.ReplyTerminaExec(saldo = MEU_SALDO)

def serve():
    _ , preco, port, carteira, serv_banco = sys.argv
    global PRECO, MINHA_CARTEIRA
    PRECO = int(preco)
    MINHA_CARTEIRA = carteira
    global MEU_SALDO

    channel = grpc.insecure_channel(serv_banco)
    stub_banco = banco_pb2_grpc.DoStuffStub(channel)
    response = stub_banco.le_saldo(banco_pb2.RequestLeSaldo(carteira = MINHA_CARTEIRA))
    MEU_SALDO = response.valor


    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    loja_pb2_grpc.add_DoStuffServicer_to_server(DoStuff(stop_event, stub_banco), server)
    server.add_insecure_port(f'0.0.0.0:{port}')
    server.start()
    stop_event.wait()
    server.stop(grace=None)

if __name__ == '__main__':
    serve()
    
# python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. loja.proto
# python3 serv_loja.py 1 8889 Dorgival 0.0.0.0:8888