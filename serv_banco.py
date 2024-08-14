import sys
from concurrent import futures # usado na definição do pool de threads
import threading
import grpc

import banco_pb2, banco_pb2_grpc # módulos gerados pelo compilador de gRPC


class Banco(banco_pb2_grpc.BancoServicer):
    def __init__(self, stop_event, saldo):
        """
        stop_event : evento de parada necessário para terminar a execução do servidor
        saldo : dicionário com o saldo das carteiras
        """
        self._stop_event = stop_event
        self._cont_ordem = 1
        self._saldo = saldo
        self._ordens = {}

    def le_saldo(self, request, context):
        """
        Retorna o saldo da carteira
        request : RequestLeSaldo
        """
        if request.carteira not in self._saldo: # carteira não existe
            return banco_pb2.ReplyLeSaldo(valor=-1)
        else: 
            return banco_pb2.ReplyLeSaldo(valor=self._saldo[request.carteira])

    def cria_ordem(self, request, context):
        """
        Cria uma ordem de pagamento
        request : RequestCriaOrdem
        """
        if request.carteira not in self._saldo: # carteira não existe
            return banco_pb2.ReplyCriaOrdem(status=-1)
        elif self._saldo[request.carteira] < request.valor: # saldo insuficiente
            return banco_pb2.ReplyCriaOrdem(status=-2)
        else: 
            self._saldo[request.carteira] -= request.valor
            self._ordens[self._cont_ordem] = (request.valor, request.carteira)
            self._cont_ordem += 1
            return banco_pb2.ReplyCriaOrdem(status=self._cont_ordem - 1)
        
    def transfere(self, request, context):
        """
        Faz uma transferência
        request : RequestTransfere
        """
        if request.ordem not in self._ordens: # ordem não existe
            return banco_pb2.ReplyTransfere(status=-1)
        elif self._ordens[request.ordem][0] != request.conferencia: # valor incorreto
            return banco_pb2.ReplyTransfere(status=-2)
        elif request.carteira not in self._saldo: # carteira destino não existe
            return banco_pb2.ReplyTransfere(status=-3)
        else:
            self._saldo[request.carteira] += request.conferencia
            del self._ordens[request.ordem]
            return banco_pb2.ReplyTransfere(status=0)
    
    def termina_exec(self, request, context):
        """
        Termina execução do servidor
        request : RequestTerminaExec
        """
        for cliente, saldo in self._saldo.items():
            print(saldo)
        self._stop_event.set()
        return banco_pb2.ReplyTerminaExec(n_pendencias = len(self._ordens))
            
def serve():
    port = sys.argv[1]
    saldo = {}

    # Leitura das carteiras e saldos
    for line in sys.stdin:
        if not line or not line.strip() or len(line.strip()) == 1: # linha inválida
            continue
        carteira, s = line.strip().split()
        saldo[carteira] = int(s)

    stop_event = threading.Event()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    banco_pb2_grpc.add_BancoServicer_to_server(Banco(stop_event, saldo), server)

    server.add_insecure_port(f'0.0.0.0:{port}')

    server.start()
    stop_event.wait()
    server.stop(grace=None)

if __name__ == '__main__':
    serve()
    
