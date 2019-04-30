#! /usr/bin/python3

import cgi

# imports per treballar amb agents, mirar quins son necessaris
from multiprocessing import Process, Queue
import socket

import sys
import os

sys.path.append(os.path.relpath("/home/auri/Documents/UNI/ECSDI/Implementations/AgentUtil"))

from rdflib import Namespace, Graph
from flask import Flask

from FlaskServer import shutdown_server
from Agent import Agent
from ACLMessages import build_message, send_message
from OntoNamespaces import ACL, DSO, RDF

print("Content-Type: text/html")     # HTML is following
print()                               # blank line, end of headers

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

total_budget = form.getfirst("budget", "")

# this is a relative split, to calculate total budget for each part do: 
# totalbudget * ponderation / sum of all ponderations 
transport_budget = form.getfirst("transportbudget", "")
accomodation_budget = form.getfirst("accomodationbudget", "")
activities_budget = form.getfirst("activitiesbudget", "")

# Preferencies
hotel_vs_apartament = form.getfirst("hotelapartm", "")
centric_vs_outskirts = form.getfirst("centric", "")

bus_vs_plane = form.getfirst("busplane", "")

festiu = form.getfirst("festiu", "")
ludic = form.getfirst("ludic", "")
cultural = form.getfirst("cultural", "")

# create graph
content_graph = Graph()

# bind the ontology used (onto1 for the request)
content_graph.Bind('nomonto', "nom ontologia")

content_graph.add((AgentePlanificador.uri, RDF.type, "nom ontologia.'Organize-trip'"))
# add all parameters according to the ontology

# building an ACL message
gr = build_message(Graph(), perf=ACL.request, sender=Client.uri, msgcnt=0, content=content_graph)

# sending the message to the agent 
res = send_message(gr, AgentePlanificador.address)

# decoding the ACL return message

# printing the output
print (dep_city, arr_city, dep_date, ret_date, num_trav, total_budget, transport_budget, accomodation_budget, activities_budget,hotel_vs_apartament, bus_vs_plane, festiu, ludic, cultural)

