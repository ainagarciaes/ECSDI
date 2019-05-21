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

from rdflib import Namespace, Graph, Literal
from flask import Flask, request


from FlaskServer import shutdown_server
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA
from Agent import Agent

__author__ = 'javier'


# Configuration stuff
hostname = 'localhost'
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

@app.route("/")
def testing():
    return "testing connection"

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    print('entrypoint comunicacion')
    global dsgraph
    global mss_cnt

    def GetTransports():

    #----------- STUB VERSION -----------#
        transports = Graph()
        #transports.bind('foaf', FOAF)
        transports.bind('via', VIA)

        transport= VIA.transport + '_transport' + str(mss_cnt)
        transports.add((transport, RDF.type, VIA.Transport))

        # Municipi origen i desti del transport
        localitzacio = VIA.Localitzacio + '_localitzacio' + str(mss_cnt)
        municipi = VIA.Municipi + '_municipi' + str(mss_cnt)                               
        transports.add((localitzacio, RDF.type, VIA.Localitzacio))
        transports.add((localitzacio, VIA.Municipi, municipi))                                
        transports.add((municipi, VIA.Nom, Literal('NOM MUNICIPI ' + str(mss_cnt))))     
        transports.add((transport, VIA.origen, municipi))
        transports.add((transport, VIA.desti, municipi))                          
        
        # Data anada i tornada del transport
        temps = VIA.Temps + '_temps' + str(mss_cnt)
        data = VIA.Data + '_data' + str(mss_cnt)                              
        transports.add((temps, RDF.type, VIA.Temps))
        transports.add((temps, VIA.Data, data))                                  
        transports.add((data, VIA.DAta, Literal('DATA ' + str(mss_cnt))))     
        transports.add((transport, VIA.data_anada, data))
        transports.add((transport, VIA.data_tornada, data)) 

        # preu del transport
        preu = VIA.Preu + '_preu' + str(mss_cnt)                              
        transports.add((preu, RDF.type, VIA.Preu))                                
        transports.add((preu, VIA.Import, Literal('IMPORT PREU ' + str(mss_cnt))))     
        transports.add((transport, VIA.val, preu))

        # tipus de seient del transport
        seient = VIA.Tipus_seient + '_seient' + str(mss_cnt)                              
        transports.add((seient, RDF.type, VIA.Tipus_seient))                                
        transports.add((seient, VIA.Nom, Literal('NOM TIPUS SEIENT ' + str(mss_cnt))))     
        transports.add((transport, VIA.ofereix_seients, seient)) 

        # transport dummy de capacitat 10
        transport1 = VIA.Transport + 'transport' + str(mss_cnt)
        transports.add((transport, VIA.Transport, transport1))
        transports.add((transport1, VIA.Nom, Literal("Transport 1 " + str(mss_cnt))))
        transports.add((transport1, VIA.Capacitat, Literal("10 " + str(mss_cnt))))

        # transport dummy de capacitat 20
        transport2 = VIA.Transport + 'transport' + str(mss_cnt)
        transports.add((transport, VIA.Transport, transport2))
        transports.add((transport2, VIA.Nom, Literal("Transport 2 " + str(mss_cnt))))
        transports.add((transport2, VIA.Capacitat, Literal("20 " + str(mss_cnt))))

        return transports      

    # crear graf amb el missatge que rebem
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood"
        print('you did not send anything')
        gr = build_message(Graph(), ACL['not-understood'], sender=AgentTransport.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            print('did not receive an acl request')
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=AgentTransport.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type) # TODO preguntar com va aixo

                if accion == DEM.Consultar_transports: #comparar que sigui del tipus d'accio que volem
                    print('getting transports')
                    graph_content = GetTransports()
                    gr = build_message(graph_content, ACL['inform'], sender=AgentTransport.uri, msgcnt=mss_cnt, content = VIA.Transport)

                else:
                    print('wrong action')
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
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
