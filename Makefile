
arg1 = 10
arg2 = 8889
arg3 = Dorgival 
arg4 = 0.0.0.0:8888


clean: 
	rm -f banco_pb2_grpc.py banco_pb2.py loja_pb2_grpc.py loja_pb2.py

stub_banco:
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. banco.proto

stub_loja:
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. loja.proto

stubs:stub_banco stub_loja

run_serv_banco: stub_banco
	python3	serv_banco.py $(arg1) 

run_cli_banco: stub_banco
	python3 cli_banco.py $(arg1) $(arg2) 

run_serv_loja: stubs
	python3 serv_loja.py $(arg1) $(arg2) $(arg3) $(arg4)

run_cli_loja: stubs
	python3 cli_loja.py $(arg1) $(arg2) $(arg3)