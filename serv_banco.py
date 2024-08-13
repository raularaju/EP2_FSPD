import sys
from concurrent import futures # usado na definição do pool de threads
import threading
import grpc

import banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC
ORDEM = 1
saldo = {} # dicionário que simula um banco de dados
ordens = {}
# Os procedimentos oferecidos aos clientes precisam ser encapsulados
#   em uma classe que herda do código do stub.
class DoStuff(banco_pb2_grpc.DoStuffServicer):
    def __init__(self, stop_event):
        self._stop_event = stop_event

   # A assinatura de todos os procedimentos é igual: um objeto com os
   # parâmetros e outro com o contexto de execução do servidor
    def le_saldo(self, request, context):
        if request.carteira not in saldo: # carteira não existe
            return banco_pb2.ReplyLeSaldo(valor=-1)
        else: 
            return banco_pb2.ReplyLeSaldo(valor=saldo[request.carteira])

    def cria_ordem(self, request, context):
        if request.carteira not in saldo: # carteira não existe
            return banco_pb2.ReplyCriaOrdem(status=-1)
        elif saldo[request.carteira] < request.valor: # saldo insuficiente
            return banco_pb2.ReplyCriaOrdem(status=-2)
        else: 
            global ORDEM
            ordens[ORDEM] = (request.valor, request.carteira)
            ORDEM += 1 
            return banco_pb2.ReplyCriaOrdem(status=ORDEM-1)
        
    def transfere(self, request, context):
        if request.ordem not in ordens: # ordem não existe
            return banco_pb2.ReplyTransfere(status=-1)
        elif ordens[request.ordem][0] != request.conferencia: # valor incorreto
            return banco_pb2.ReplyTransfere(status=-2)
        elif request.carteira not in saldo: # carteira destino não existe
            return banco_pb2.ReplyTransfere(status=-3)
        else:
            saldo[request.carteira] += request.conferencia
            saldo[ordens[request.ordem][1]] -= request.conferencia
            del ordens[request.ordem]
            return banco_pb2.ReplyTransfere(status=0)
    
    def termina_exec(self, request, context):
        self._stop_event.set()
        print(saldo)
        return banco_pb2.ReplyTerminaExec(n_pendencias=len(ordens))
            
def serve():
    port = sys.argv[1]
    for line in sys.stdin:
        carteira, s = line.strip().split()
        saldo[carteira] = int(s)
    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # O servidor precisa ser ligado ao objeto que identifica os
    #   procedimentos a serem executados.
    banco_pb2_grpc.add_DoStuffServicer_to_server(DoStuff(stop_event), server)
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