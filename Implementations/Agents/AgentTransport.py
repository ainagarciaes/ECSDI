# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Esqueleto de agente usando los servicios web de Flask

/comm es la entrada para la recepcion de mensajes del agente
/Stop es la entrada que para el agente

Tiene una funcion AgentBehavior1 que se lanza como un thread concurrente

Asume que el agente de registro esta en el puerto 9000

@author: javier
"""

from multiprocessing import Process, Queue
import socket
import sys
import os

sys.path.append(os.path.relpath("../AgentUtil"))
sys.path.append(os.path.relpath("../Utils"))

from rdflib import Namespace, Graph, Literal
from flask import Flask, request


from FlaskServer import shutdown_server
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA
from StringDateConversions import stringToDate
from Agent import Agent

__author__ = 'javier'


# Configuration stuff
#hostname = socket.gethostname()
hostname = "localhost"
port = 8081

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentTransport = Agent('AgenteTransport',
                       agn.AgentTransport,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)

AgentePlanificador = Agent('AgentePlanificador',
                       agn.AgentePlanificador,
                       'http://%s:%d/comm' % ("localhost", 8000),
                       'http://%s:%d/Stop' % ("localhost", 8000))


# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """

    def cercaTransports():

        resultat =Graph()
        resultat.bind('via',VIA)
        contingut = Graph()
        global ciutat_origen
        restriccions_transport = gm.value(subject=content, predicate=DEM.Restriccions_transports)
        DataF = gm.value(subject=restriccions_transport, predicate=DEM.Data_final)
        DataIni = gm.value(subject=restriccions_transport, predicate=DEM.Data_inici)
        ciutat_desti = gm.value(subject=restriccions_transport, predicate=DEM.Desti)
        NPers = gm.value(subject=restriccions_transport, predicate=DEM.NumPersones)
        ciutat_origen = gm.value(subject=restriccions_transport, predicate=DEM.Origen)
        Preu = gm.value(subject=restriccions_transport, predicate=DEM.Preu)
        print(DataF)
        print(DataIni)
        print(ciutat_desti)
        print(NPers)
        print(ciutat_origen)
        print(Preu)
        contingut.parse('../../Ontologies/Viatge-RDF.owl', format='xml')
        res_Anada = contingut.query(f"""
                        SELECT ?nm ?mitja ?c ?preu ?se
                        WHERE {{
                            ?t rdf:type via:Transport .
                            ?t via:Nom ?nm .
                            ?t via:MitjaTransport ?mitja .
                            ?t via:Capacitat ?c .
                            ?t via:val ?p .
                            ?t via:data_anada ?da .
                            ?t via:ofereix_seients ?s .
                            ?s via:Nom ?se .
                            ?da via:Data "{DataIni}" .
                            ?t via:data_tornada ?dt .
                            ?dt via:Data "{DataF}" .
                            ?p via:Import ?preu .
                            ?t via:origen ?ciu .
                            ?ciu via:Nom "{ciutat_origen}" .
                            ?t via:desti ?ciu1 .
                            ?ciu1 via:Nom "{ciutat_desti}" .
                        }}""", initNs={"via":VIA})
        for row in res_Anada:
            if(int(NPers) <= int(row[2])):
                preuTotal = int(NPers)*int(row[3])*2
                if (preuTotal <= Preu):
                    Transports = VIA.Transport + "_" + row[0]
                    resultat.add((Transports,RDF.type,VIA.Transport))
                    resultat.add((Transports, VIA.Nom , Literal(row[0])))
                    resultat.add((Transports, VIA.Capacitat, Literal(row[2])))
                    resultat.add((Transports, VIA.MitjaTransport, Literal(row[1])))
                    resultat.add((Transports, VIA.Preu, Literal(preuTotal)))
                    resultat.add((Transports, VIA.Nom, Literal(row[4])))
                    resultat.add((Transports, VIA.Data + "_anada", Literal(DataIni)))
                    resultat.add((Transports, VIA.Data + "_tornada", Literal(DataF)))
                    resultat.add((Transports, VIA.Nom + "_origen", Literal(ciutat_origen)))
                    resultat.add((Transports, VIA.Nom + "_desti", Literal(ciutat_desti)))
        for s, p, o in resultat:
            print(s,p,o)
        #posar al content la busqueda del que ens demanen
        #gr = build_message(resultat,
        #    ACL['inform'],
        #    sender=AgentTransport.uri,
        #    msgcnt=mss_cnt,
        #    receiver=msgdic['sender'], content = VIA)
        return resultat

    global dsgraph
    global mss_cnt

    # crear graf amb el missatge que rebem
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood"
        gr = build_message(Graph(), ACL['not-understood'], sender=AgentTransport.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=AgentTransport.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                action = gm.value(subject=content, predicate=RDF.type) # TODO preguntar com va aixo

                if action == DEM.Consultar_transports: #comparar que sigui del tipus d'accio que volem
                    graf_resposta = cercaTransports()
                    gr = build_message(graf_resposta, ACL['inform'], sender=AgentTransport.uri, msgcnt=mss_cnt, content = VIA.Viatge)
                else:
                    gr = build_message(Graph(), ACL['not-understood'], sender=AgentTransport.uri, msgcnt=mss_cnt)

    mss_cnt += 1

    return gr.serialize(format='xml')


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """
    pass


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=8081)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
