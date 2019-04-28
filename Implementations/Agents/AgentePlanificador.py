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

from rdflib import Namespace, Graph
from flask import Flask

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message
from OntoNamespaces import ACL, DSO

__author__ = 'javier'


# Configuration stuff
hostname = socket.gethostname()
port = 8000

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
AgentePlanificador = Agent('AgentePlanificador',
                       agn.AgentePlanificador,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                       agn.Directory,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)


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

    print("I ENTER HERE")
    def prepare_trip():         
        # Aqui realizariamos lo que pide la accion
        # Por ahora simplemente retornamos un Inform
        t = obtain_transport()
        h = obtain_hotel()
        
        content = Graph() # posar el t i h al graf de resultats com toqui

        return content

    def obtain_transport():
        # ... 
        # 1. build message
        m = build_message(Graph(), ACL['request']) #posar params que faltin
        # 2. send message to the external agent
        gr = send_message(m, )
        # 3. get response 
        # 4. parse response and choose one
        # 5. return chosen transport
        return 
    
    def obtain_hotel():
        # ...
        # 1. build message
        m = build_message(Graph(), ACL['request']) #posar params que faltin
        # 2. send message to the external agent
        send_message(m, )
        # 3. get response 
        # 4. parse response and choose one
        # 5. return chosen transport
        return

    global dsgraph
    global mss_cnt

    # crear graf amb el missatge que rebem
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)
    
    msgdic = get_message_properties(gm)
    
    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood"
        gr = build_message(Graph(), ACL['not-understood'], sender=InfoAgent.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=InfoAgent.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)

                if action: #comparar que sigui del tipus d'accio que volem
                    graph_content = prepare_trip()
                    gr = build_message(Graph(), ACL['inform'], sender=InfoAgent.uri, msgcnt=mss_cnt, content = graph_content)

                else:
                    gr = build_message(Graph(), ACL['not-understood'], sender=InfoAgent.uri, msgcnt=mss_cnt)

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


