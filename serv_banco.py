import sys
from concurrent import futures # usado na definição do pool de threads
import threading
import grpc

import banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC


# Os procedimentos oferecidos aos clientes precisam ser encapsulados
#   em uma classe que herda do código do stub.
class Banco(banco_pb2_grpc.BancoServicer):
    def __init__(self, stop_event, saldo):
        self._stop_event = stop_event
        self._cont_ordem = 1
        self._saldo = saldo
        self._ordens = {}
   # A assinatura de todos os procedimentos é igual: um objeto com os
   # parâmetros e outro com o contexto de execução do servidor
    def le_saldo(self, request, context):
        if request.carteira not in self._saldo: # carteira não existe
            return banco_pb2.ReplyLeSaldo(valor=-1)
        else: 
            return banco_pb2.ReplyLeSaldo(valor=self._saldo[request.carteira])

    def cria_ordem(self, request, context):
        if request.carteira not in self._saldo: # carteira não existe
            return banco_pb2.ReplyCriaOrdem(status=-1)
        elif self._saldo[request.carteira] < request.valor: # saldo insuficiente
            return banco_pb2.ReplyCriaOrdem(status=-2)
        else: 
            request[request.carteira] -= request.valor
            self._ordens[self._cont_ordem] = (request.valor, request.carteira)
            self._cont_ordem += 1
            return banco_pb2.ReplyCriaOrdem(status=self._cont_ordem - 1)
        
    def transfere(self, request, context):
        if request.ordem not in self._ordens: # ordem não existe
            return banco_pb2.ReplyTransfere(status=-1)
        elif self._cont_ordem[request.ordem][0] != request.conferencia: # valor incorreto
            return banco_pb2.ReplyTransfere(status=-2)
        elif request.carteira not in self._saldo: # carteira destino não existe
            return banco_pb2.ReplyTransfere(status=-3)
        else:
            self._saldo[request.carteira] += request.conferencia
            del self._ordens[request.ordem]
            return banco_pb2.ReplyTransfere(status=0)
    
    def termina_exec(self, request, context):
        self._stop_event.set()
        print(self._saldo)
        return banco_pb2.ReplyTerminaExec(n_pendencias=len(self._ordens))
            
def serve():
    port = sys.argv[1]
    saldo = {}
    for line in sys.stdin:
        carteira, s = line.strip().split()
        saldo[carteira] = int(s)
    stop_event = threading.Event()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # O servidor precisa ser ligado ao objeto que identifica os
    #   procedimentos a serem executados.
    banco_pb2_grpc.add_BancoServicer_to_server(Banco(stop_event, saldo), server)
    # O método add_insecure_port permite a conexão direta por TCP
    #   Outros recursos estão disponíveis, como uso de um registry
    #   (dicionário de serviços), criptografia e autenticação.
    server.add_insecure_port(f'0.0.0.0:{port}')
    # O servidor é iniciado e esse código não tem nada para fazer
    #   a não ser esperar pelo término da execução.
    server.start()
    stop_event.wait()
    server.stop(grace=None)

if __name__ == '__main__':
    serve()
    
# python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. banco.proto
# python3 serv_banco.py 8888 < carteiras.in 