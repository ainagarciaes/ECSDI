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
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA

__author__ = 'javier'


# Configuration stuff
#hostname = socket.gethostname()
hostname = "localhost"
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

AgenteTransporte = Agent('AgenteTransporte',
                       agn.AgenteTransporte,
                       'http://%s:%d/comm' % ("localhost", 8081),
                       'http://%s:%d/Stop' % ("localhost", 8081))

AgenteAlojamiento = Agent('AgenteAlojamiento',
                       agn.AgenteAlojamiento,
                       'http://%s:%d/comm' % ("localhost", 8080),
                       'http://%s:%d/Stop' % ("localhost", 8080))

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
    def prepare_trip():        
        obj_restriccions = gm.value(subject=content, predicate=DEM.Restriccions)
        data_inici = gm.value(subject=obj_restriccions, predicate=DEM.Data_inici)
        data_final = gm.value(subject=obj_restriccions, predicate=DEM.Data_final)
        n_pers = gm.value(subject=obj_restriccions, predicate=DEM.NumPersones)
        origen = gm.values(subject=obj_restriccions, predicate=DEM.Origen)
        desti = gm.values(subject=obj_restriccions, predicate=DEM.Desti)

        obj_preferencies = gm.value(subject=content, predicate=DEM.Restriccions)
 
        # Aqui realizariamos lo que pide la accion
        # Por ahora simplemente retornamos un Inform
        #t = obtain_transport()
        #h = obtain_hotel() -> ha de retornar el graph pero per testejar de moment no retorno res
        obtain_transport()
        obtain_hotel()
        content = Graph() # posar el t i h al graf de resultats com toqui
        #content.bind('via', VIA)

        return content

    def obtain_transport():
        # 0. extract parameters from the initial request
        obj_restriccions_transport = gm.value(subject=obj_restriccions, predicate=DEM.Restriccions_transports)
        preu_transport = gm.value(subject=obj_restriccions_transport, predicate=DEM.Preu)

        # 1. build graph
        content_transport = Graph()
        content_transport.bind('dem', DEM)

        consultar_transport_obj = DEM.Consultar_transports + '_cons_transp'
        restr_transport_obj = DEM.Restriccions_transports
        pref_transport_obj = DEM.Preferencies_transports

        content_transport.add((consultar_transport_obj, RDF.type, DEM.Consultar_transports))
        content_transport.add((consultar_transport_obj, DEM.Restriccions_transports, restr_transport_obj))
        content_transport.add((consultar_transport_obj, DEM.Preferencies_transports, pref_transport_obj))

        content_transport.add((restr_transport_obj, DEM.Preu, Literal(preu_transport)))
        content_transport.add((restr_transport_obj, DEM.Data_inici, Literal(data_inici)))
        content_transport.add((restr_transport_obj, DEM.Data_final, Literal(data_final)))
        content_transport.add((restr_transport_obj, DEM.Origen, Literal(origen)))
        content_transport.add((restr_transport_obj, DEM.Desti, Literal(desti)))
        content_transport.add((restr_transport_obj, DEM.NumPersones, Literal(n_pers)))

        # 2. build && send message to the external agent
        mss_cnt += 1
        gr = build_message(content_transport, perf=ACL.request, sender=AgentePlanificador.uri, msgcnt=mss_cnt, receiver=AgenteTransporte.uri, content=consultar_transport_obj)
        res = send_message(gr, AgenteTransporte.address)

        # 3. get response
        # 4. parse response and choose one
        # 5. return chosen transport
        return 
    
    def obtain_hotel():
        # 0. extract parameters from the initial request
        obj_restriccions_allotjament = gm.value(subject=obj_restriccions, predicate=DEM.Restriccions_hotels)
        preu_allotjament = gm.value(subject=obj_restriccions_allotjament, predicate=DEM.Preu)
        
        # 1. build graph
        content_allotjament = Graph()
        content_allotjament.bind('dem', DEM)

        consultar_allotjament_obj = DEM.Consultar_hotels + '_cons_hotels'
        restr_allotjament_obj = DEM.Restriccions_hotels
        pref_allotjament_obj = DEM.Preferencies_hotels

        content_allotjament.add((consultar_allotjament_obj, RDF.type, DEM.Consultar_hotels))
        content_allotjament.add((consultar_allotjament_obj, DEM.Restriccions_hotels, restr_allotjament_obj))
        content_allotjament.add((consultar_allotjament_obj, DEM.Preferencies_hotels, pref_allotjament_obj))

        content_allotjament.add((restr_allotjament_obj, DEM.Preu, Literal(preu_allotjament)))
        content_allotjament.add((restr_allotjament_obj, DEM.Data_inici, Literal(data_inici)))
        content_allotjament.add((restr_allotjament_obj, DEM.Data_final, Literal(data_final)))
        content_allotjament.add((restr_allotjament_obj, DEM.Ciutat, Literal(origen)))
        content_allotjament.add((restr_allotjament_obj, DEM.NumPersones, Literal(n_pers)))

        # 2. build && send message to the external agent
        mss_cnt += 1
        gr = build_message(content_allotjament, perf=ACL.request, sender=AgentePlanificador.uri, msgcnt=mss_cnt, receiver=AgenteAlojamiento.uri, content=consultar_allotjament_obj)
        res = send_message(gr, AgenteAlojamiento.address)
        
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
    
    gr = Graph()

    # FIPA ACL message?
    if msgdic is None:      # NO: responem "not understood"
        gr = build_message(Graph(), ACL['not-understood'], sender=AgentePlanificador.uri, msgcnt=mss_cnt)
    else:                   # SI: mirem que demana
        # Performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=AgentePlanificador.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)
                

                if accion == DEM.Planificar_viatge : #comparar que sigui del tipus d'accio que volem
                    graph_content = prepare_trip()
                    """
                    gr = build_message(graph_content, ACL['inform'], sender=AgentePlanificador.uri, msgcnt=mss_cnt, content = VIA.Viatge)
                else:
                    """
                    gr = build_message(Graph(), ACL['not-understood'], sender=AgentePlanificador.uri, msgcnt=mss_cnt)

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
    app.run(host="localhost", port=8000)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')


