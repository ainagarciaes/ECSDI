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


        resultat =Graph()
        resultat.bind('via',VIA)
        contingut = Graph()
        obj_restriccions = gm.value(subject=content, predicate=DEM.Restriccions_hotels)
        ciutat = gm.value(subject=obj_restriccions, predicate=DEM.Ciutat)
        dataI = gm.value(subject=obj_restriccions, predicate=DEM.Data_inici)
        dataF = gm.value(subject=obj_restriccions, predicate=DEM.Data_final)
        NumPer = gm.value(subject=obj_restriccions, predicate=DEM.NumPersones)
        preuAllot = gm.value(subject=obj_restriccions, predicate=DEM.Preu)
        data_ini = stringToDate(dataI)
        data_fi = stringToDate(dataF)
        contingut.parse('../../Ontologies/Viatge-RDF.owl', format='xml')
        res = contingut.query(f"""
                        SELECT ?nm ?c ?ta ?preu ?sit ?t ?testn ?ppn
                        WHERE {{
                            ?a rdf:type via:Allotjament .
                            ?a via:Nom ?nm .
                            ?a via:Capacitat ?c .
                            ?a via:TipusAllotjament ?ta .
                            ?a via:val ?p .
                            ?p via:Import ?preu .
                            ?a via:es_troba_a ?ciu .
                            ?ciu via:Nom "{ciutat}" .
                            ?a via:se_situa_a ?s .
                            ?s via:Nom ?sit .
                            ?a via:te_habitacions ?th .
                            ?th via:Nom ?t .
                            ?a via:ofereix ?test .
                            ?test via:Nom ?testn .
                            ?a via:es_popular ?pp .
                            ?pp via:Nom ?ppn .
                        }}""", initNs={"via":VIA})


        dies = data_fi - data_ini
        for row in res:
            if(int(row[1])>=int(NumPer)):
                print(row[3])
                preuTotal = int(NumPer)*int(row[3])*(dies.days)
                print(preuTotal)
                if (preuTotal<=preuAllot):
                    Allotjaments = VIA.Allotjament + "_" + row[0]
                    resultat.add((Allotjaments,RDF.type,VIA.Allotjament))
                    resultat.add((Allotjaments, VIA.Nom , Literal(row[0])))
                    resultat.add((Allotjaments, VIA.Capacitat, Literal(row[1])))
                    resultat.add((Allotjaments, VIA.TipusAllotjament, Literal(row[2])))
                    resultat.add((Allotjaments, VIA.Preu, Literal(preuTotal)))
                    resultat.add((Allotjaments, VIA.Nom + "_Situacio", Literal(row[4])))
                    resultat.add((Allotjaments, VIA.Nom + "_TipusHabitacio", Literal(row[5])))
                    resultat.add((Allotjaments, VIA.Nom + "_TipusEstada", Literal(row[6])))
                    resultat.add((Allotjaments, VIA.Nom + "_Popularitat", Literal(row[7])))
                    resultat.add((Allotjaments, VIA.Data + "_anada", Literal(dataI)))
                    resultat.add((Allotjaments, VIA.Data + "_tornada", Literal(dataF)))

        return resultat

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
