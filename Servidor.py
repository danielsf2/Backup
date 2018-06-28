# coding: utf-8
import socket, os, sys, hashlib, json, time, zipfile

'''
	Porta Default da Aplicação
'''
SOCKETPADRAO = 55555

LOGDECONEXAO = None
HISTORICODELOG = None

'''
	A parte do Servidor estará em execução em cada Host que será objeto do Backup, esta aplicação tem por
	finalidade receber como parametro uma pasta padrão, junta os arquivos e cria um zip e posteriormente
	se conecta a aplicação que recebera os dados de Backup.
'''
def main():
	GeraArquivoBackup()
	
	'''
		Váriaveis definidas no escopo global que têm por objetivo armazenar os conteúdos de 
		log de conexao e histórico.
	'''
	LOGDECONEXAO = "{0}{1}{2}".format("log", ObtemSeparadorDeArquivo(), "Conexao.log")
	HISTORICODELOG = "{0}{1}{2}".format("log", ObtemSeparadorDeArquivo(), "Histórico de Conexão.log")
	
	socketConexao = None

	ChecaDiretorio("log")
	ChecaDiretorio("Backup")
	CriaArquivoZip("Arquivos")

	'''
		Gera uma senha de conexão com a criptografia do MD5.
	'''
	senhaServidor = hashlib.md5("123456".encode("utf-8").strip()).hexdigest()

	'''
		Tenta Obter conexão com o Servidor de Backup.
	'''
	socketConexao = ObtemConexao()

	'''
		Verifica se a conexão foi estabelecida com o servidor através do socket.
	'''
	if (socketConexao):
		try:
			'''
				Recebe a chave de conexão da aplicação que receberá os dados.
			'''
			senhaCliente = socketConexao.recv(1024).decode("utf-8")

			'''
				Grava as informações a respeito dos dados da conexão em um Histórico.
			'''
			historicoConexao = "\n[{0} - {1}]: {2}".format(ObtemData(), ObtemHora(), "Conexão estabelecida!")
			GeraLog(HISTORICODELOG, historicoConexao)

			'''
				Verifica se as senhas coincidem para estabeleciemnto de conexão e envio dos dados.
			'''
			if (senhaCliente == senhaServidor):
				if (os.path.exists("{0}{1}{2}{3}".format("Backup",ObtemSeparadorDeArquivo(), ObtemNomeArquivo(), ".zip"))):
					
					'''
						Confirma o acesso a aplicação que receberá os dados.
					'''
					socketConexao.send(bytes("Conectado!".encode("utf-8").strip()))

					'''
						Obtem os dados do Host
					'''
					dados = ObtemDadosHost()

					'''
						Transforma os dados do Host em um objeto JSON que é um objeto padrão de envio
						de dados na internet que tem por finalidade comprimir os dados e coloca-los em 
						um formato compatível para transmissão, feito através da função dumps.
					'''
					json_dados = json.dumps(dados)

					'''
						Envia os dados do Host para o Servidor de Backup.
					'''
					EnviaDadosHost(socketConexao, json_dados)

					'''
						Envia o Arquivo Zip para o Servidor de Backup.
					'''
					EnviaArquivo(socketConexao)

					if(ChecaDiretorio("log")):
						logData = "\n[{0} - {1} - {2}:{3}]\n\t{4}".format(ObtemData(), ObtemHora(), dados["Ip"], dados["Porta"], '\n\t'.join(ObtemArquivoZip()))

						GeraLog(LOGDECONEXAO, logData)
				else:
					print("Arquivo de Backup Inexistente.")

			socketConexao.close()

			# Gravando no log de conexões.
			#HISTORICODELOG = "\n[{0} - {1}]: {2}".format(ObtemData(), ObtemHora(), "Conexão finalizada!")
			#GeraLog(HISTORICODELOG, historicoConexao)


		except (socket.herror, socket.gaierror, socket.error):
			historicoConexao = "\n[{0} - {1}]: {2}".format(ObtemData(), ObtemHora(), "Erro ao Estabelecer Conexao.")
			if(ChecaDiretorio("log")):
				GeraLog(HISTORICODELOG, historicoConexao)
				
		except (socket.timeout):
			history_data = "\n[{0} - {1}]: {2}".format(ObtemData(), ObtemHora(), "Tempo limite Esgotado.")
			if(ChecaDiretorio("log")):
				GeraLog(HISTORICODELOG, historicoConexao)

'''
	Gera um diretório para armazenamento do arquivo.
'''
def GeraArquivoBackup():
	ChecaDiretorio("log")
	try:
		diretorio = "Arquivos"
		ChecaDiretorio(diretorio)
	except IOError:
		diretorio = ObtemDiretorioPadrao()

	CriaArquivoZip(diretorio)
	
'''
	Obtém o diretório padrão do Host de onde os dados serão armazenados e enviados.
'''
def ObtemDiretorioPadrao():
	
	if sys.platform == "linux" or sys.platform == "linux2":
		diretorio = os.environ['HOME']
	
	elif sys.platform == "win32":
		diretorio = os.environ['USERPROFILE']

	diretorio += "{0}{1}{2}".format(diretorio , ObtemSeparadorDeArquivo(), "Arquivos")

	ChecaDiretorio(diretorio)

	return diretorio
	
'''
	Checa o arquivo Zip recebido, cria um diretório caso a mesma não exista, compacta os
	dados e armazena no diretório.
'''
def CriaArquivoZip(diretorio):
	
	nomeArquivo = ObtemNomeArquivo()

	'''
		Checa se o diretório existe caso contrário cria.
	'''
	ChecaDiretorio("Backup")

	LOGDECONEXAO = "{0}{1}{2}".format("log", ObtemSeparadorDeArquivo(), "Conexao.log")

	logData = "\n[{0} - {1}]: {2}".format(ObtemData(), ObtemHora(), "Criação do arquivo Zip.")

	GeraLog(LOGDECONEXAO, logData)

	arquivoZip = zipfile.ZipFile("{0}{1}{2}{3}".format("Backup", ObtemSeparadorDeArquivo(), nomeArquivo, ".zip"), "w")
	
	for dirname, subdirs, files in os.walk("{0}".format(diretorio)):
		
		arquivoZip.write(dirname)
		
		for filename in files:
			arquivoZip.write(os.path.join(dirname, filename))

	arquivoZip.close()

	logData = "\n[{0} - {1}]: {2}".format(ObtemData(), ObtemHora(), "Arquivo Zip Criado.")

	GeraLog(LOGDECONEXAO, logData)
	print("Arquivo Zip Criado")

'''
	Obtem o nome do arquivo que sera Zipado.
'''
def ObtemNomeArquivo():
	return os.environ['USER']
	
'''
	Oferece um separados de arquivo com base no sistema opracional onde roda a aplicação, caso seja Windows
	"\\", caso de linux "/".
'''
def ObtemSeparadorDeArquivo():
	
	if sys.platform == "linux" or sys.platform == "linux2":
		separadorArquivo = "/"
	
	elif sys.platform == "win32":
		separadorArquivo = "\\"

	return separadorArquivo
	
'''
	Checa se o diretório existe, caso contrário cria, onde serão armazenados os dados relativos à aplicação
	bem como os dados de envio e recebimento dos arquivos.
'''
def ChecaDiretorio(diretorio):
	
	if(not os.path.isdir(diretorio)):
		
		os.system("mkdir {0}".format(diretorio))

		logDeConexao = "{0}{1}{2}".format("log", ObtemSeparadorDeArquivo(), "Conexao.log")
		
		logData = "\n[{0} - {1}]: Criação do diretorio: {2}".format(ObtemData(), ObtemHora(), diretorio)
		#GeraLog(LOGDECONEXAO, logData)

	return True

'''
	Obtém o Ip do Host Estabelecendo uma conexão com o google open DNS, onde é recuperado através do
	socket usado para estabelecer conexão (Define o a conexao como IPV4(AF_INET) e UDP(SOCK_DGRAM), 
	pois sua única finalidade é obtero Ip do Host).
'''
def ObtemIpHost():
	
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    soc.connect(("8.8.8.8", 80))

    return soc.getsockname()[0]

'''
	Cria um socket TCP para conexão com a aplicação que recebrá os dados do Host, a qual ficará aberta 
	aguardando que o host que receberá os dados se conecte, caso as informações de segurança não sejam 
	atendidas a conexão será abortada.
'''
def ObtemConexao():
	try:
		'''
			Define a porta que será estabelecida como IPV4(AF_INET) e TCP(SOCK_STREAM).
		'''
		socketServidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		'''
			Realiza o bind do socket, que é anexar um endereço local ao socket no caso a porta default
			da aplicação definida por 55555
		'''
		socketServidor.bind(("",SOCKETPADRAO))

		'''
			Define o máximo de conexões que o socket pode receber neste caso é definido como uma.
		'''
		socketServidor.listen(1)

		print("Aguardando Conexão.")

		'''
			Neste ponto o servido está aguardando uma conexao.
		'''
		socketServidor, addr = socketServidor.accept()

		return socketServidor

	except (socket.error, socket.herror, socket.gaierror, socket.timeout):
		print("Ocorreu um Erro Durante o Estabelecimento de Conexão")
		return None

'''
	Tem como função gerar um Checksum MD5 do Arquivo Zip Criado(o Checksum é uma soma de verificação, ou seja,
	esse é um conjunto de caracteres utilizado para conferir a integridade do arquivo, o MD5 é o algoritmo
	criptográfico responsável por gerar um hash individual para cada arquivo existente.
'''
def ObtemZipMD5():
	'''
		Abre o arquivo para obter seu Checsun
	'''
	arquivo = open("{0}{1}{2}{3}".format("Backup",ObtemSeparadorDeArquivo(), ObtemNomeArquivo(), ".zip"), "rb")

	'''
		Obtem o Hash do Arquivo através do algoritmo MD5
	'''
	hashMD5 = hashlib.md5(arquivo.read()).hexdigest()

	arquivo.close()

	return hashMD5

'''
	Obtém as propriedades do Host para verificação do conteúdo no momento do recebimento
	bem como verificação da integridade dos dados.
'''
def ObtemDadosHost():
	'''
		Armazenando os dados do Hots em um objeto.
	'''
	dados = {
		"Ip" : "{0}".format(ObtemIpHost()),
		"Porta": SOCKETPADRAO,
		"NomeArquivo": "{0}".format(ObtemNomeArquivo()),
		"ChecksumMD5": ObtemZipMD5(),
		"Data": time.strftime("%d-%m-%Y"),
		"Hora": time.strftime("%H:%M:%S")
	}

	return dados

'''
	Grava as mensagens de Log em um Arquivo.
'''
def GeraLog(arquivo, mensagem):
	
	LOGDECONEXAO = open(arquivo,"a+")

	LOGDECONEXAO.write(mensagem)

'''
	Envia json com com as propriedades do host e do arquivo que é um modelo para armazenamento e transmissão de informações no 
	formato texto e que é bastante utilizado por aplicações que realizam Transmissão de Dados por conexão. Recebe uma mensagem de 
	confirmação de recebimento.
'''
def EnviaDadosHost(socketConexao, json_dados):

	socketConexao.send(bytes(json_dados.encode("utf-8").strip()))

	socketConexao.recv(1024).decode("utf-8")

'''
	Envia o arquivo Zip que esta armazenado no Host para o cliente, o arquivo é enviado em partes de 1024 bytes
	para que nao seja sobrecarregado o canal, a conexão é encerrada após o envio completo dos dados. 
'''
def EnviaArquivo(socketConexao):

	'''
		Abre o arquivo armazenado para enviar.
	'''
	arquivo = open("Backup{0}{1}{2}".format(ObtemSeparadorDeArquivo(), ObtemNomeArquivo(), ".zip"), "rb")

	'''
		Envia os primeiros 1024 bytes para a aplicação e caso o arquivo seja maior que isso 
		entra em um loop até que o arquivo seja enviado completamente. 
	'''
	leitura = arquivo.read(1024)
	print("Enviando Arquivo...")

	while(leitura):
		print("Enviando Arquivo...")
		socketConexao.send(bytes(leitura))
		leitura = arquivo.read(1024)

	arquivo.close()

'''
	Obtém a uma lista com os arquivos zip, e a envia.
'''
def ObtemArquivoZip():

	arquivoZip = zipfile.ZipFile("Backup{0}{1}{2}".format(ObtemSeparadorDeArquivo(), ObtemNomeArquivo(), ".zip"))

	listaArquivos = arquivoZip.namelist()

	return listaArquivos

'''
	Obtém a data do sistema Operacional (dd/mm/aaaa)
'''
def ObtemData():
	return time.strftime("%d/%m/%Y")

'''
	Obtém a hora do sistema Operacional (hh:mm:ss)
'''
def ObtemHora():
	return time.strftime("%H:%M:%S")

if __name__ == "__main__":
		main()
