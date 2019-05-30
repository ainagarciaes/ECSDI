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

from rdflib import Namespace, Graph, Literal, URIRef
from flask import Flask, request

from FlaskServer import shutdown_server
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA, FOAF
from Agent import Agent

__author__ = 'javier'


# Configuration stuff
#hostname = socket.gethostname()
hostname = "localhost"
port = 8080

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente

AgentAllotjament = Agent('AgentAllotjament',
                       agn.AgentAllotjament,
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

cola1 = Queue() # crec que aixo no ens cal per ara pero ho deixo por si acaso

# Flask stuff
app = Flask(__name__)


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """

    def cercaHotels():



        contingut = Graph()
        obj_restriccions = gm.value(subject=content, predicate=DEM.Restriccions_hotels)
        ciutat = gm.value(subject=obj_restriccions, predicate=DEM.Ciutat)
        dataI = gm.value(subject=obj_restriccions, predicate=DEM.Data_inici)
        dataF = gm.value(subject=obj_restriccions, predicate=DEM.Data_final)
        NumPer = gm.value(subject=obj_restriccions, predicate=DEM.NumPersones)
        preuAllot = gm.value(subject=obj_restriccions, predicate=DEM.Preu)
        print(ciutat)
        print(dataI)
        print(dataF)
        print(NumPer)
        print(preuAllot)
        #q = prepareQuery()
        contingut.parse('../../Ontologies/Viatge-RDF.owl', format='xml')
        print("HEM FET EL PARSE")
        #via = URIRef("http://www.semanticweb.org/guille/ontologies/2019/3/Viatge#Allotjament")
        res = contingut.query("""
                        SELECT ?nm
                        WHERE {
                            ?a rdf:type via:Allotjament .
                            ?a via:Nom ?nm .
                            ?a via:es_troba_a ?ciu .
                            ?ciu via:Nom "BUDAPEST".
                        }""", initNs={"via":VIA})
        print("RESULTAT SPARQL")
        for row in res:
            print("%s" % row)

        print("HE ARRIBAT FINS AQUÍ")


        gr = build_message(Graph(),
            ACL['inform'],
            sender=AgentAllotjament.uri,
            msgcnt=mss_cnt,
            receiver=msgdic['sender'], content = content)
        return gr

    global dsgraph
    global mss_cnt

    # crear graf amb el missatge que rebem
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood" i un graph de contingut buit
        gr = build_message(Graph(), ACL['not-understood'], sender=AgentAllotjament.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # SI NO ENS FAN UN REQUEST
            gr = build_message(Graph(), ACL['not-understood'], sender=AgentAllotjament.uri, msgcnt=mss_cnt)
        else:
            # AQUI HI ARRIBEM QUAN HEM ENTES EL MISSATGE I ES DEL TIPUS QUE VOLIEM

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                action = gm.value(subject=content, predicate=RDF.type)

                if action == DEM.Consultar_hotels: #comparar que sigui del tipus d'accio que volem
                    graf_resposta = cercaHotels()
                    gr = build_message(graf_resposta, ACL['inform'], sender=AgentAllotjament.uri, msgcnt=mss_cnt, content = VIA.Viatge)
                else:
                    gr = build_message(Graph(), ACL['not-understood'], sender=AgentAllotjament.uri, msgcnt=mss_cnt)

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
    # no se de que serveix pero suposo que anira sol i ya
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=8080)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
