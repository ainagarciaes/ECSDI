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

from rdflib import Namespace, Graph
from flask import Flask

sys.path.append(os.path.relpath("../AgentUtil"))

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA, FOAF

__author__ = 'javier'


# Configuration stuff
hostname = socket.gethostname()
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

    global dsgraph
    global mss_cnt

    def getAllotjaments():
    #----------- STUB VERSION -----------#
        allotjaments = Graph()
        #allotjaments.bind('foaf', FOAF)
        allotjaments.bind('via', VIA)

        allotjament = VIA.allotjament + '_allotjament' + str(mss_cnt)
        allotjaments.add((allotjament, RDF.type, VIA.Allotjament))

        # localització de l'allotjament
        localitzacio = VIA.Localitzacio + '_localitzacio' + str(mss_cnt)                               
        allotjaments.add((localitzacio, RDF.type, VIA.Localitzacio))                                
        allotjaments.add((localitzacio, VIA.Nom, Literal('NOM LOCALITZACIO ' + str(mss_cnt))))     
        allotjaments.add((allotjament, VIA.es_troba_a, localitzacio))                          
        
        # popularitat de l'allotjament
        popularitat = VIA.Popularitat + '_popularitat' + str(mss_cnt)                              
        allotjaments.add((popularitat, RDF.type, VIA.Popularitat))                                
        allotjaments.add((popularitat, VIA.Nom, Literal('NOM POPULARITAT ' + str(mss_cnt))))     
        allotjaments.add((allotjament, VIA.es_popular, popularitat)) 

        # preu de l'allotjament
        preu = VIA.Preu + '_preu' + str(mss_cnt)                              
        allotjaments.add((preu, RDF.type, VIA.Preu))                                
        allotjaments.add((preu, VIA.Import, Literal('IMPORT PREU ' + str(mss_cnt))))     
        allotjaments.add((allotjament, VIA.val, preu))

        # situacio de l'allotjament
        situacio = VIA.Situacio + '_situacio' + str(mss_cnt)                              
        allotjaments.add((situacio, RDF.type, VIA.Situacio))                                
        allotjaments.add((situacio, VIA.Nom, Literal('NOM SITUACIO ' + str(mss_cnt))))     
        allotjaments.add((allotjament, VIA.es_troba_a, situacio))  

        # tipus d'estada de l'allotjament
        estada = VIA.Tipus_estada + '_estada' + str(mss_cnt)                              
        allotjaments.add((estada, RDF.type, VIA.Tipus_estada))                                
        allotjaments.add((estada, VIA.Nom, Literal('NOM TIPUS ESTADA ' + str(mss_cnt))))     
        allotjaments.add((allotjament, VIA.ofereix, estada)) 

        # tipus d'habitacio de l'allotjament
        habitacio = VIA.Tipus_habitacio + '_habitacio' + str(mss_cnt)                              
        allotjaments.add((habitacio, RDF.type, VIA.Tipus_habitacio))                                
        allotjaments.add((habitacio, VIA.Nom, Literal('NOM TIPUS HABITACIO ' + str(mss_cnt))))     
        allotjaments.add((allotjament, VIA.te_habitacions, habitacio)) 


        # allotjament dummy de capacitat 10
        allotjament1 = VIA.Allotjament + 'allotjament1' + str(mss_cnt)
        allotjaments.add((allotjament, VIA.Allotjament, allotjament1))
        allotjaments.add((allotjament1, VIA.Nom, Literal("Apartament 1 " + str(mss_cnt))))
        allotjaments.add((allotjament1, VIA.Capacitat, Literal("10 " + str(mss_cnt))))

        # allotjament dummy de capacitat 20
        allotjament2 = VIA.Allotjament + 'allotjament2' + str(mss_cnt)
        allotjaments.add((allotjament, VIA.Allotjament, allotjament2))
        allotjaments.add((allotjament2, VIA.Nom, Literal("Apartament 2 " + str(mss_cnt))))
        allotjaments.add((allotjament2, VIA.Capacitat, Literal("20 " + str(mss_cnt))))

        return allotjaments
    # crear graf amb el missatge que rebem
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    gr = Graph()

    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood" i un graph de contingut buit
        gr = build_message(Graph(), ACL['not-understood'], sender=AgentAllotjament.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=AgentAllotjament.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)

                if action == DEM.Demanar.Consultar_hotels: #comparar que sigui del tipus d'accio que volem
                    graph_content = getAllotjaments()
                    gr = build_message(graph_content, ACL['inform'], sender=AgentAllotjament.uri, msgcnt=mss_cnt, content = VIA.Allotjament)

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
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
