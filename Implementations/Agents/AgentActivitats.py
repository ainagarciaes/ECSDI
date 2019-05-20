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
from Agent import Agent
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA, FOAF

__author__ = 'javier'


# Configuration stuff
#hostname = socket.gethostname()
hostname = "localhost"
port = 8082

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
AgentActivitats = Agent('AgentActivitats',
                       agn.AgentActivitats,
                       'http://%s:%d/comm' % ("localhost", 8082),
                       'http://%s:%d/Stop' % ("localhost", 8082))

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
    global dsgraph
    global mss_cnt
    

    def buscaActivitats():
        #----------- FILE VERSION -----------#

        '''
        # use sparql to read each param received from the planificador agent
        graph_activitats = Graph()
        # load file here to graph 

        activitats = graph_activitats.query("""
            SELECT ...
            WHERE {
                ...
                FILTER{ ... }
            }
        """, initNs = {'via', VIA})
        '''

        #----------- STUB VERSION -----------#
        activitats = Graph()
        activitats.bind('foaf', FOAF)
        activitats.bind('via', VIA)

        activitat = VIA.Activitat + '_activitat' + str(mss_cnt)
        activitats.add((activitat, RDF.type, VIA.Activitat))

        # recinte on es fa l'activitat
        recinte = VIA.Recinte + '_recinte' + str(mss_cnt)                               # id del objecte recinte
        activitats.add((recinte, RDF.type, VIA.Recinte))                                # assigno el tipus
        activitats.add((recinte, FOAF.name, Literal('NOM RECINTE ' + str(mss_cnt))))     # informacio literal sobre recinte
        activitats.add((activitat, VIA.se_celebra_a, recinte))                          # relacio del recinte creat amb l'activitat
        
        # activitat dummy de tipus ludica, concert
        ludica = VIA.Ludica + 'ludica' + str(mss_cnt)
        concert = VIA.Concert + 'concert' + str(mss_cnt)
        activitats.add((activitat, VIA.Ludica, ludica))
        activitats.add((ludica, VIA.Concert, concert))
        activitats.add((concert, FOAF.name, Literal("NOM CONCERT " + str(mss_cnt))))
        # TODO posar aqui les dates d'obertura?
        return activitats

    # crear graf amb el missatge que rebem
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)
    
    msgdic = get_message_properties(gm)
    
    gr = Graph()

    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood"
        print('msg dic is empty')
        gr = build_message(Graph(), ACL['not-understood'], sender=AgentActivitats.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            print('not an acl request')
            gr = build_message(Graph(), ACL['not-understood'], sender=AgentActivitats.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)
                print(accion)
                if accion == DEM.Demanar_activitat : #comparar que sigui del tipus d'accio que volem
                    graph_content = buscaActivitats()
                    gr = build_message(graph_content, ACL['inform'], sender=AgentActivitats.uri, msgcnt=mss_cnt, content = VIA.Activitat)
                else:
                    print('action not understood')
                    gr = build_message(Graph(), ACL['not-understood'], sender=AgentActivitats.uri, msgcnt=mss_cnt)

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
    app.run(host="localhost", port=8082)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')


