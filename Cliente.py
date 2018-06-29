# coding: utf-8
import socket, hashlib, time, threading, json, enum, os

'''
	Trabalho de Redes de Computadores

	Desenvolvedores:
		Daniel Soares
		Eva Costa de Melo

	version 0.1
'''
def main():
	'''
		Verifica se o diretório existe
	'''
	verificaPath("logs");
	verificaPath("backups");

	'''
		Obtém o conteudo do arquivo de endereços ip.
	'''
	arquivo_de_ip = open("Arquivos/ArquivoDeIps.txt", "r")

	'''
		Obtém a lista de ips (hosts).
	'''
	lista_ip = arquivo_de_ip.read().split("\n");

	'''
		Fecha o arquivo de ips.
	'''
	arquivo_de_ip.close()

	'''
		Inicia a conexão.
	'''
	gerenciaConexao(lista_ip)

'''
	Gerencia as conexões.
	Para cada cliente é associada uma thread, executando somente o numero
	de coenxões definido (Conextion.NUMBER_THREAD) por vez.
'''
def gerenciaConexao(lista_ip):
	threads = [] # Array com as threads
	ultima_thread = 0; # Última Thread executada.
	wait_thread = 0; # Thread em estado de espera.

	'''
		Verifica se a lista de hosts está vazia.
	'''
	if(len(lista_ip) > 0):
		for lista in lista_ip:
			if(lista != ''):
				dados = lista.split(":")
				if(len(dados) == 2):

					'''
						Inicializa as Threads.
					'''
					thread = threading.Thread(target=backupDados, args=(dados[0], dados[1].replace("\r", ""), 0,))

					'''
						Adiciona a nova Thread na lista de Threads.
					'''
					threads.append(thread)

	'''
		Verifica qual foi a última thread executada.
		Quando todas forem executadas, finaliza a execução.
	'''
	while(ultima_thread < len(threads)):
		tamanho = (len(threads)-ultima_thread) if (len(threads)-ultima_thread) < Connection.NUMBER_THREAD.value else Connection.NUMBER_THREAD.value

		for count in range(tamanho):
			threads[ultima_thread].start()
			ultima_thread += 1

		for count in range(tamanho):
			threads[wait_thread].join()
			wait_thread += 1

def backupDados(ip, senha, attempt):
	try:
		'''
			Grava os logs
		'''
		gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "IP: {0} Porta: {1} Tentativa: {2}".format(ip, Connection.PORT.value, attempt))

		'''
			Estabelece conexão com um host
		'''
		clientSocket = conexaoTCP(ip, Connection.PORT.value)

		'''
			Envia a senha de conexão
		'''
		clientSocket.send(bytes(senha.encode().strip()))

		'''
			Recebe mensagem de confirmação da conexão
		'''
		estado_de_conexao = clientSocket.recv(1024).decode("utf-8")

		'''
			Verfica se a conexão foi aceita.
		'''
		if(estado_de_conexao == "Conectado!"):
			print("Conexao Estabelecida com Sucesso! ")
			gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "Conexão estabelecida com {0} na porta {1}".format(ip, Connection.PORT.value))
			arquivo(clientSocket) # Tenta realizar backup do arquivo

			clientSocket.close()
			gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "Conexão finalizada com {0} na porta {1}".format(ip, Connection.PORT.value))

	except(socket.timeout):
		tentativa_de_reconexao("Tempo excedido", attempt, ip, senha)
	except(socket.error):
		tentativa_de_reconexao("Erro ao estabelecer conexão. Verifique o estado de conexão do host", attempt, ip, senha)
	except(socket.herror):
		tentativa_de_reconexao("Erro no endereço do host", attempt, ip, senha)
	except(socket.gaierror):
		tentativa_de_reconexao("Erro ao conectar", attempt, ip, senha)

'''
	Conexão TCP com um host
'''
def conexaoTCP(ip, porta):
	ip_do_servidor = ip
	porta_do_servidor = porta

	'''
		Definindo socket
		IPv4 (socket.AF_INET)
		TCP socket.SOCK_STREAM
	'''
	clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


	print("Tentando Estabelecer Conexão com o Servidor")

	'''
		Tentativa de conexão com o servidor
	'''
	clientSocket.connect((ip_do_servidor,porta_do_servidor))

	return clientSocket

'''
	Realiza o download dos dados (backup)
'''
def arquivo(clientSocket):
	'''
		Dados do host e do arquivo
	'''
	ip, data, checksum_md5_servidor, dados = propriedadesDoArquivo(clientSocket)

	nomeDoArquivo = "{0}:{1}".format(ip, data)
	'''
		Cria o arquivo.
	'''
	arquivo_backup = open("backups/{0}.zip".format(nomeDoArquivo), "wb")

	gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "Iniciando transferência do arquivo zip de {0}.".format(ip))

	'''
		É iniciada a transmissão do arquivo.
	'''
	rec = clientSocket.recv(1024)

	print("Obtida Primeira Parte do Arquivo")

	while(rec):
		print("Obtendo Arquivos")
		arquivo_backup.write(rec);
		rec = clientSocket.recv(1024)

	gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "Finalizando transferência do arquivo zip de {0}.".format(ip))

	'''
		Checksum é uma soma de verificação,  conjunto de caracteres
		utilizado para conferir a integridade do arquivo.

		MD5 é o algoritmo criptográfico responsável por gerar um
		hash individual para cada arquivo existente.
	'''
	checksum_md5_cliente = hashlib.md5(arquivo_backup.read()).hexdigest()

	if(checksum_md5_cliente == checksum_md5_servidor):
		gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "Arquivo zip de {0} foi transferido com sucesso.".format(ip))
	else:
		gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "Arquivo zip de {0} está corrompido.".format(ip))

	arquivo_backup.close()
'''
	Grava no diretório de backup o nome do computador
	e a data em que o arquivo foi criado.
'''
def propriedadesDoArquivo(clientSocket):
	'''
		Json (é o formato mais leve de transferência/intercâmbio de dados)
		recebe os dados do host e do arquivo.
	'''

	json_dados = clientSocket.recv(1024).decode("utf-8")

	gravar_arquivo_de_log(logs.CONNECTION_LOG.value, json_dados)

	'''
		Mensagem de confirmação.
	'''
	clientSocket.send(bytes("ok".encode("utf-8")))

	'''
		Parse de json para um dicionário.
	'''
	dados = json.loads(json_dados)

	data = dados["Data"]
	checksum_md5 = dados["ChecksumMD5"]
	ip = dados["Ip"]

	return ip, data, checksum_md5, dados

'''
	Verifica se o diretório existe.
	Caso não exista, tenta criar.
'''
def verificaPath(path):
	if(not os.path.isdir(path)):
		os.system("mkdir {0}".format(path))

'''
	Tenta reconectar com o host.
'''
def tentativa_de_reconexao(msg, attempt, ip, senha):
	'''
		Connection.RECONNECT (número máximo de tentativas de reconexões permitidas).
	'''
	gravar_arquivo_de_log(logs.CONNECTION_LOG.value, "{0}: {1}".format(ip, msg))
	if(attempt < Connection.RECONNECT.value):
		backupDados(ip, senha, attempt+1)

'''
	Registra no arquivo de log a mensagem correspondente.
'''
def gravar_arquivo_de_log(arquivo, msg):
	arquivo_de_log = open(arquivo, "a+")

	arquivo_de_log.write("[{0} {1}]: {2}.\n".format(get_data(), get_hora(), msg))

'''
	Obtém a data do sistema.
'''
def get_data():
	return time.strftime("%d/%m/%Y")

'''
	Obtém a hora do sistema.
'''
def get_hora():
	return time.strftime("%H:%M:%S")

'''
	Enum
	Armazena os dados sobre a conexão.
'''
class Connection(enum.Enum):
	NUMBER_THREAD = 2
	RECONNECT = 2
	PORT = 55555

class logs(enum.Enum):
	CONNECTION_LOG = "logs/connection.log"

if __name__ == "__main__":
	main()
