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
import datetime

sys.path.append(os.path.relpath("../AgentUtil"))
sys.path.append(os.path.relpath("../Utils"))

from rdflib import Namespace, Graph, Literal, term
from flask import Flask, request

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message, get_message_properties
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA, FOAF
from StringDateConversions import stringToDate, dateToString

__author__ = 'javier'


# Configuration stuff
#hostname = socket.gethostname()
hostname = "localhost"
ip = 'localhost'
port = 8000

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
AgentePlanificador = Agent('AgentePlanificador',
                       agn.AgentePlanificador,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

AgenteTransporte = Agent('AgenteTransporte',
                       agn.AgenteTransporte,
                       'http://%s:%d/comm' % (ip, 8081),
                       'http://%s:%d/Stop' % (ip, 8081))

AgenteAlojamiento = Agent('AgenteAlojamiento',
                       agn.AgenteAlojamiento,
                       'http://%s:%d/comm' % (ip, 8080),
                       'http://%s:%d/Stop' % (ip, 8080))

AgentActivitats = Agent('AgentActivitats',
                       agn.AgentActivitats,
                       'http://%s:%d/comm' % (ip, 8082),
                       'http://%s:%d/Stop' % (ip, 8082))


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

    #mss_cnt = 0

    def prepare_trip():
        def obtain_transport():
            global mss_cnt
            # 0. extract parameters from the initial request
            obj_restriccions_transport = gm.value(subject=obj_restriccions, predicate=DEM.Restriccions_transports)
            obj_preferencies_transport = gm.value(subject=obj_preferencies, predicate=DEM.Preferencies_transports)
            preu_transport = gm.value(subject=obj_restriccions_transport, predicate=DEM.Preu)

            # preferencies
            mitja_transport = gm.value(subject=obj_preferencies_transport, predicate=DEM.Tipus_transport)
            tipus_seient = gm.value(subject=obj_preferencies_transport, predicate=DEM.Tipus_seient)

            # 1. build graph
            content_transport = Graph()
            content_transport.bind('dem', DEM)

            consultar_transport_obj = DEM.Consultar_transports + '_cons_transp'
            restr_transport_obj = DEM.Restriccions_transports

            content_transport.add((consultar_transport_obj, RDF.type, DEM.Consultar_transports))
            content_transport.add((consultar_transport_obj, DEM.Restriccions_transports, restr_transport_obj))

            content_transport.add((restr_transport_obj, DEM.Preu, Literal(preu_transport)))
            content_transport.add((restr_transport_obj, DEM.Data_inici, Literal(data_inici)))
            content_transport.add((restr_transport_obj, DEM.Data_final, Literal(data_final)))
            content_transport.add((restr_transport_obj, DEM.Origen, Literal(origen)))
            content_transport.add((restr_transport_obj, DEM.Desti, Literal(desti)))
            content_transport.add((restr_transport_obj, DEM.NumPersones, Literal(n_pers)))

            # 2. build && send message to the external agent
            mss_cnt += 1
            gr = build_message(content_transport, perf=ACL.request, sender=AgentePlanificador.uri, msgcnt=mss_cnt, receiver=AgenteTransporte.uri, content=consultar_transport_obj)
            
            # 3. get response
            res = send_message(gr, AgenteTransporte.address)

            row_transport = res.query(f"""
                SELECT ?nt
                WHERE {{
                    ?t rdf:type via:Transport .
                    ?t via:Nom ?nt .
                    ?t via:MitjaTransport "{mitja_transport}" .
                    ?t via:Tipus_seient "{tipus_seient}" .
                }}
                LIMIT 1
                """, initNs={"via":VIA})

            if (len(row_transport) == 0):
                row_transport = res.query(f"""
                    SELECT ?nt
                    WHERE {{
                        ?t rdf:type via:Transport .
                        ?t via:Nom ?nt .
                        ?t via:MitjaTransport "{mitja_transport}" .
                    }}
                    LIMIT 1
                    """, initNs={"via":VIA})

                if (len(row_transport) == 0):
                    row_transport = res.query(f"""
                        SELECT ?nt
                        WHERE {{
                            ?t rdf:type via:Transport .
                            ?t via:Nom ?nt .
                            ?t via:Tipus_seient "{tipus_seient}" .
                        }}
                        LIMIT 1
                        """, initNs={"via":VIA})

                    if (len(row_transport) == 0):
                        row_transport = res.query(f"""
                            SELECT ?nt
                            WHERE {{
                                ?t rdf:type via:Transport .
                                ?t via:Nom ?nt .
                            }}
                            LIMIT 1
                            """, initNs={"via":VIA})

            transport = Graph()
            s = term.URIRef('')

            for row in row_transport:
                nomTransport = row[0]
                s = term.URIRef(VIA.Transport + "_" + nomTransport)
                transport += res.triples((s, None, None))
                # el graph te dos nivells, per tant dos loops
                for s, p, o in transport:
                    aux = Graph()
                    aux += res.triples((o, None, None))
                    for s1, p1, o1 in aux:
                        transport.add((o, p1, o1))
                break            

            # 5. return chosen transport
            return transport, s

        def obtain_hotel():
            global mss_cnt
            # 0. extract parameters from the initial request
            obj_restriccions_allotjament = gm.value(subject=obj_restriccions, predicate=DEM.Restriccions_hotels)
            preu_allotjament = gm.value(subject=obj_restriccions_allotjament, predicate=DEM.Preu)

            # preferencies
            obj_preferencies_allotjament = gm.value(subject=obj_preferencies, predicate=DEM.Preferencies_hotels)
            
            localitzacio = gm.value(subject=obj_preferencies_allotjament, predicate=DEM.Localitzacio)
            t_estada = gm.value(subject=obj_preferencies_allotjament, predicate=DEM.Tipus_estada)

            # 1. build graph
            content_allotjament = Graph()
            content_allotjament.bind('dem', DEM)

            consultar_allotjament_obj = DEM.Consultar_hotels + '_cons_hotels'
            restr_allotjament_obj = DEM.Restriccions_hotels

            content_allotjament.add((consultar_allotjament_obj, RDF.type, DEM.Consultar_hotels))
            content_allotjament.add((consultar_allotjament_obj, DEM.Restriccions_hotels, restr_allotjament_obj))

            content_allotjament.add((restr_allotjament_obj, DEM.Preu, Literal(preu_allotjament)))
            content_allotjament.add((restr_allotjament_obj, DEM.Data_inici, Literal(data_inici)))
            content_allotjament.add((restr_allotjament_obj, DEM.Data_final, Literal(data_final)))
            content_allotjament.add((restr_allotjament_obj, DEM.Ciutat, Literal(desti)))
            content_allotjament.add((restr_allotjament_obj, DEM.NumPersones, Literal(n_pers)))

            # 2. build && send message to the external agent
            mss_cnt += 1
            gr = build_message(content_allotjament, perf=ACL.request, sender=AgentePlanificador.uri, msgcnt=mss_cnt, receiver=AgenteAlojamiento.uri, content=consultar_allotjament_obj)

            # 3. get response
            res = send_message(gr, AgenteAlojamiento.address)
            
            row_allotjament = res.query(f"""
                SELECT ?nt
                WHERE {{
                    ?t rdf:type via:Allotjament .
                    ?t via:Nom ?nt .
                    ?t via:Nom_TipusEstada "{t_estada}" .
                    ?t via:Nom_Situacio "{localitzacio}" .
                }}
                LIMIT 1
                """, initNs={"via":VIA})

            if (len(row_allotjament) == 0):
                row_allotjament = res.query(f"""
                    SELECT ?nt
                    WHERE {{
                        ?t rdf:type via:Allotjament .
                        ?t via:Nom ?nt .
                        ?t via:Nom_TipusEstada "{t_estada}" .
                    }}
                    LIMIT 1
                    """, initNs={"via":VIA})

                if (len(row_allotjament) == 0):
                    row_allotjament = res.query(f"""
                        SELECT ?nt
                        WHERE {{
                            ?t rdf:type via:Allotjament .
                            ?t via:Nom ?nt .
                            ?t via:Nom_Situacio "{localitzacio}" .
                        }}
                        LIMIT 1
                        """, initNs={"via":VIA})

                    if (len(row_allotjament) == 0):
                        row_allotjament = res.query(f"""
                            SELECT ?nt
                            WHERE {{
                                ?t rdf:type via:Allotjament .
                                ?t via:Nom ?nt .
                            }}
                            LIMIT 1
                            """, initNs={"via":VIA})

            allotjament = Graph()
            s = term.URIRef('')

            for row in row_allotjament:
                nomAllotjament = row[0]
                s = term.URIRef(VIA.Allotjament + "_" + nomAllotjament)
                allotjament += res.triples((s, None, None))
                # el graph te dos nivells, per tant dos loops
                for s, p, o in allotjament:
                    aux = Graph()
                    aux += res.triples((o, None, None))
                    for s1, p1, o1 in aux:
                        allotjament.add((o, p1, o1))
                break            

            # 5. return chosen transport
            return allotjament, s

        def obtain_activities():
            print('entering obtain activitites')
            global mss_cnt

            diff = stringToDate(data_final) - stringToDate(data_inici)
            n = diff.days

            # agafar d'aqui el preu de les activitats
            obj_pref = gm.value(subject=content, predicate = DEM.Preferencies)
            tipusViatge = gm.value(subject=obj_pref, predicate=DEM.Tipus_activitat)
            budget_activitat = gm.value(subject=obj_pref, predicate=DEM.Preu)
            b = int(budget_activitat)/(n*3)
            total_activitats = Graph()
            total_activitats.bind('via', VIA)
            total_activitats.bind('foaf', FOAF)

            current_date = stringToDate(data_inici)
            for i in range(0, n):
                # posar dia, franja horaria
                for i in range(0, 3):
                    franja = ''
                    if i == 0:
                        franja = 'MATI'
                    elif i == 1:
                        franja = 'TARDA'
                    else:
                        franja = 'NIT'

                    demana_a = Graph()
                    demana_a.bind('dem', DEM)
                    activitat = agn['activitat']
                    demana_a.add((activitat, RDF.type, DEM.Demanar_activitat))
                    demana_a.add((activitat, DEM.Ciutat, Literal(desti)))
                    demana_a.add((activitat, DEM.Cost, Literal(b)))
                    
                    dateString = dateToString(current_date)
                    demana_a.add((activitat, DEM.Data_activitat, Literal(dateString)))
                    demana_a.add((activitat, DEM.Horari, Literal(franja)))
                    demana_a.add((activitat, DEM.Tipus_activitat, Literal(tipusViatge)))

                    # 2. build && send message to the external agent
                    mss_cnt += 1
                    gr = build_message(demana_a, perf=ACL.request, sender=AgentePlanificador.uri, msgcnt=mss_cnt, receiver=AgentActivitats.uri, content=activitat)

                    # 3. get response
                    a = send_message(gr, AgentActivitats.address)
                    
                    total_activitats += a
                    activitats_noms = Graph()
                    activitats_noms += a.triples((None, RDF.type, VIA.Activitat))
                    print(len(activitats_noms))

                # calculate next date and continue iterating
                current_date += datetime.timedelta(days=1)
            return total_activitats

        content = msgdic['content']

        obj_restriccions = gm.value(subject=content, predicate=DEM.Restriccions)
        data_inici = gm.value(subject=obj_restriccions, predicate=DEM.Data_inici)
        data_final = gm.value(subject=obj_restriccions, predicate=DEM.Data_final)
        n_pers = gm.value(subject=obj_restriccions, predicate=DEM.NumPersones)
        origen = gm.value(subject=obj_restriccions, predicate=DEM.Origen)
        desti = gm.value(subject=obj_restriccions, predicate=DEM.Desti)

        obj_preferencies = gm.value(subject=content, predicate=DEM.Preferencies)

        # Obtenim transport i hotel
        t, t_name = obtain_transport()
        h, h_name = obtain_hotel()
        a = obtain_activities()
        

        content = Graph() # posar el t i h al graf de resultats com toqui
        content.bind('via', VIA)

        viatge_obj = VIA.Viatge + '_viatge'

        content.add((viatge_obj, RDF.type, VIA.Viatge))

        content.add((viatge_obj, VIA.Allotjament, h_name))
        content.add((viatge_obj, VIA.Transport, t_name))

        content = content + h
        content = content + t
        content = content + a

        return content


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
                    gr = build_message(graph_content, ACL['inform'], sender=AgentePlanificador.uri, msgcnt=mss_cnt, content = VIA.Viatge)
                else:
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
    app.run(host='0.0.0.0', port=8000)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print('The End')
