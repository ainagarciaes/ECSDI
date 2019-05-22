#! /usr/bin/python3

import cgi

# imports per treballar amb agents, mirar quins son necessaris
from multiprocessing import Process, Queue
import socket

import sys
import os

sys.path.append(os.path.relpath("/home/auri/Documents/UNI/ECSDI/Implementations/AgentUtil"))

from rdflib import Namespace, Graph, Literal
from rdflib.namespace import FOAF, RDF
from flask import Flask

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message
from OntoNamespaces import ACL, DSO, RDF, DEM, VIA

print("Content-Type: text/html")     # HTML is following
print()                              # blank line, end of headers

import cgitb
cgitb.enable()

agn = Namespace("http://www.agentes.org#")

hostname = "localhost"
port = 8000

# dades del agent
AgentePlanificador = Agent('AgentePlanificador',
                       agn.AgentePlanificador,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

Client = Agent('Client', agn.Client, '', '')

# llegim el formulari
form = cgi.FieldStorage()

# Restriccions
dep_city = form.getfirst("departurecity", "").upper()
arr_city = form.getfirst("arrivalcity", "").upper()

dep_date = form.getfirst("departuredate", "")
ret_date = form.getfirst("returndate", "")

num_trav = form.getfirst("numtrav", "")

total_budget = int(form.getfirst("budget", ""))

# this is a relative split, to calculate total budget for each part do: 
# totalbudget * ponderation / sum of all ponderations 
transport_budget = int(form.getfirst("transportbudget", ""))
accomodation_budget = int(form.getfirst("accomodationbudget", ""))
activities_budget = int(form.getfirst("activitiesbudget", ""))

total_reparticio = transport_budget + accomodation_budget + activities_budget

# total budget calculation
transport_budget = int(total_budget * transport_budget / total_reparticio)
accomodation_budget = int(total_budget * accomodation_budget / total_reparticio)
activities_budget = int(total_budget * activities_budget / total_reparticio)

# Preferencies
localitzacio = form.getfirst("localitzacio", "")
tipus_estada = form.getfirst("tipusestada", "")
tipus_seient = form.getfirst("tipusseient", "")
tipus_transport = form.getfirst("tipustransport", "")
tipus_activitats = form.getfirst("tipusactivitats", "")

# create graph
content_graph = Graph()

# bind the ontology used (onto1 for the request)
content_graph.bind('dem', DEM)

viatge_obj = agn['viatge']
restr_obj = DEM.Restriccions + '_restriccions'   #URI a la classe restriccions, dins tindrà els parametres definits a la ontologia
pref_obj = DEM.Preferencies + '_preferencies'    #Same per preferencies

# creem base del graph, tipus viatge obj amb restriccions i preferencies
content_graph.add((viatge_obj, RDF.type, DEM.Planificar_viatge))
content_graph.add((viatge_obj, DEM.Restriccions, restr_obj))
content_graph.add((viatge_obj, DEM.Preferencies, pref_obj))

# passem les restriccions al graph
#content_graph.add((restr_obj, DEM.Preu, Literal(total_budget))) -> not needed
content_graph.add((restr_obj, DEM.Origen, Literal(dep_city)))
content_graph.add((restr_obj, DEM.Desti, Literal(arr_city)))
content_graph.add((restr_obj, DEM.NumPersones, Literal(num_trav)))
content_graph.add((restr_obj, DEM.Data_final, Literal(ret_date)))
content_graph.add((restr_obj, DEM.Data_inici, Literal(dep_date)))

restr_allotjament_obj = DEM.Restriccions_hotels + '_restriccions_hotels'        # URIS
restr_transport_obj = DEM.Restriccions_transports + '_restriccions_transports'  # URIS

content_graph.add((restr_obj, DEM.Restriccions_hotels, restr_allotjament_obj))
content_graph.add((restr_obj, DEM.Restriccions_transports, restr_transport_obj))

content_graph.add((restr_allotjament_obj, DEM.Preu, Literal(accomodation_budget)))
content_graph.add((restr_transport_obj, DEM.Preu, Literal(transport_budget)))

# passem les preferencies al graph
pref_transport_obj = DEM.Preferencies_transports + '_preftransport'
pref_allotjament_obj = DEM.Preferencies_hotels + '_prefhotels'

content_graph.add((pref_obj, DEM.Preferencies_hotels, pref_allotjament_obj))
content_graph.add((pref_obj, DEM.Preferencies_transports, pref_transport_obj))

content_graph.add((pref_transport_obj, DEM.Tipus_transport, Literal(tipus_transport)))
content_graph.add((pref_transport_obj, DEM.Tipus_seient, Literal(tipus_seient)))

content_graph.add((pref_allotjament_obj, DEM.Localitzacio, Literal(localitzacio)))
content_graph.add((pref_allotjament_obj, DEM.Tipus_estada, Literal(tipus_estada)))

content_graph.add((pref_obj, DEM.Tipus_activitat, Literal(tipus_activitats)))

# TODO no posades: popularitat i tipus habitacio

gr = Graph()
# building an ACL message
gr = build_message(content_graph, perf=ACL.request, sender=Client.uri, msgcnt=0, receiver=AgentePlanificador.uri, content=viatge_obj)

# sending the message to the agent 
res = send_message(gr, AgentePlanificador.address)

# decoding the ACL return message

# printing the output
# print (res) uncomment this when everything works as expected
print ('R:', dep_city, arr_city, dep_date, ret_date, num_trav, total_budget, transport_budget, accomodation_budget, activities_budget)
print ('\nP:', tipus_estada, tipus_seient, tipus_activitats, tipus_transport, localitzacio)