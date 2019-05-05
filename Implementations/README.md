# Primera fase d'implementació

L'objectiu d'aquesta primera fase d'implementació és programar el software que farà de client del nostre sistema, l'agent planificador que busca un hotel i un mitjà de transport i els agents externs de búsqueda de transport i hotel. També tenim com objectiu fer la interface del client i jocs de prova pels agents externs. Actualment s'executa tot des d'una mateixa màquina però més endavant posarem opcions de configuració per tal de poder canviar les ips i ports de les ocnfiguracions dels servidors dels agents.

## Estructura del Software
+ **form.html** fitxer de la interface web. Quan fas submit al form crida al client.py
+ **client.py** programa que rep les dades del formulari a través de _cgi_ i és l'encarregat de cridar al sistema per crear un viatge. Corre en un servidor apache2 que actualment està a _localhost:80_
+ **AgentPlanificador.py** agent encarregat de gestionar les peticions de viatge. Es comunica amb els agents externs per demanar-lis dades i retorna la resposta al client. Es un servidor de flask que es posa en marxa des del terminal.
+ **AgentTransport.py** agent de transport que retorna resultats a les peticions del agent planificador. Té una base de dades que actualment serà un fitxer RDF que consultarà i retornarà la part necessaria.
+ **AgentAllotjament.py** agent d'allotjament que retorna resultats a les peticions del agent planificador. Té una base de dades que actualment serà un fitxer RDF que consultarà i retornarà la part necessaria.
+ **AgentTransportStub.py** stub de l'agent de transport utilitzat per testejar el correcte funcionament del agent planificador.
+ **AgentAllotjamentStub.py** stub de l'agent d'allotjament utilitzat per testejar el correcte funcionament del agent planificador.

  ```
  └── form.html
      └── client.py
          └── AgentPlanificador.py
              ├── AgentTransport.py / AgentTransportStub.py
              └── AgentAllotjament.py / AgentAllotjamentStub.py
  ```


## Estat actual del software 
+ **form.html** acabat i testejat (son exemples, actualitzar abans d'entregar)
+ **client.py** acabat i testejat
+ **AgentPlanificador.py** acabat però no testejat
+ **AgentTransport.py** per acabar
+ **AgentAllotjament.py** per acabar
+ **AgentTransportStub.py** per acabar
+ **AgentAllotjament.py** per acabar

## Com instal·lar i executar
Primer de tot cal tenir instal·lat apache2 al ordinador.
```
$ sudo apt-get update
$ sudo apt-get install apache2
``` 
Es possible que no tinguis instal·lada la llibreria `cgi` per python3, que és la que fem servir pel client. Si no està instal·lada cal fer.
```
$ pip3 install cgi
```
Baixar-se el repositori del github. 
```
$ git clone https://github.com/ainagarciaes/ECSDI.git
```
En cas de no tenir accés al Github, descomprimir el .zip.
```
$ unzip -v ECSDI.zip
```
Crear un softlink de cgi.load desde `/etc/apache2/mods-available` a `/etc/apache2/mods-enabled`
```
$ ln -s /etc/apache2/mods-available/cgi.load /etc/apache2/mods-enabled/cgi.load 
``` 
Crear un hardlink de `client.py` fins a `/usr/lib/cgi-bin/`
```
$ ln client.py /usr/lib/cgi-bin/client.py
```

Reiniciar el servidor apache 
```
$ sudo service apache2 restart
```
Executar els agents en terminals separats des de `/ECSDI/Implementacions/Agents`.
```
$ python3 AgentePlanificador.py
$ python3 AgenteExternoTransporte[Stub].py 
$ python3 AgenteExternoAlojamiento[Stub].py
```
Obrir _form.html_ al navegador habitual, omplir el formulari i apretar el botó de _Submit_.
## Repartició del treball
* Client & AgentePlanificador - Aina
* Agentes Externos & Stubs - Guille, Marti
