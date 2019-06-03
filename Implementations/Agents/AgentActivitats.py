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

import math

sys.path.append(os.path.relpath("../AgentUtil"))
sys.path.append(os.path.relpath("../Utils"))

from rdflib import Namespace, Graph, Literal, URIRef
from flask import Flask, request

from FlaskServer import shutdown_server
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA, FOAF
from StringDateConversions import stringToDate
from datetime import datetime
from Agent import Agent

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
                       'http://%s:%d/comm' % (hostname, 8082),
                       'http://%s:%d/Stop' % (hostname, 8082))

# Global triplestore graph
dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)

@app.route("/")
def testing():
    return "testing connection"

i = 0

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    global dsgraph
    global mss_cnt
    global i

    def buscaActivitats():
        global i
        
        activitats = Graph()
        activitats.bind('via', VIA)
        contingut = Graph()
        ciutat = gm.value(subject=content, predicate=DEM.Ciutat)
        cost_max = gm.value(subject=content, predicate=DEM.Cost)
        data_act = gm.value(subject=content, predicate=DEM.Data_activitat)        
        franja = gm.value(subject=content, predicate=DEM.Horari)
        tipus_activitat = gm.value(subject=content, predicate=DEM.Tipus_activitat)
        if (Literal(tipus_activitat).eq('LUDICA')):
            tipus_activitat = "Ludica"
        elif (Literal(tipus_activitat).eq('CULTURAL')):
            tipus_activitat = "Cultural"
        else:
            tipus_activitat = "Festiva"

        contingut.parse('../../Ontologies/Viatge-RDF.owl', format='xml')

        for x in range (3):
            res = contingut.query(f"""
                            SELECT ?nm ?id ?preu ?dat ?franja ?ciu ?rec
                            WHERE {{
                                ?a rdf:type via:{tipus_activitat} .
                                ?a via:val ?p .
                                ?p via:Import ?preu .
    			                FILTER (?preu <= {cost_max}) .
                                ?a via:se_celebra_de ?franja .
                                ?franja via:Nom "{franja}" .
                                ?a via:se_celebra_el ?dat .
                                ?dat via:Data "{data_act}" .
                                ?a via:se_celebra_a ?rec .
                                ?rec via:es_troba_a ?ciu .
                                ?ciu via:Nom "{ciutat}" .
    			    			?a via:Nom ?nm .
    			    			?a via:IDAct ?id .
                            }}
                            LIMIT 1
                            """, initNs={"via":VIA})
            if (len(res) == 0):
                if (Literal(tipus_activitat).eq('Ludica')):
                    tipus_activitat = "Cultural"
                elif (Literal(tipus_activitat).eq('Cultural')):
                    tipus_activitat = "Festiva"
                else:
                    tipus_activitat = "Ludica"
            else: break

        if (len(res) == 0):
        	print("BUIT------------------------------------------")

        for row in res:
            Activitat= VIA.Activitat + "_" + tipus_activitat + str(i)
            i += 1
            activitats.add((Activitat, RDF.type, VIA.Activitat))
            activitats.add((Activitat, VIA.Nom , Literal(row[0])))
            activitats.add((Activitat, VIA.IDAct, Literal(row[1])))
            activitats.add((Activitat, VIA.Preu, Literal(row[2])))
            activitats.add((Activitat, VIA.Data, Literal(row[3])))
            activitats.add((Activitat, VIA.Nom + "_Franja", Literal(row[4])))
            activitats.add((Activitat, VIA.Nom + "_Ciutat", Literal(row[5])))
            activitats.add((Activitat, VIA.Nom + "_Recinte", Literal(row[6])))

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
    app.run(host="0.0.0.0", port=8082)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
