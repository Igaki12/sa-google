import re
from tkinter import SE
from flask import Flask, render_template, request
import requests

app = Flask(__name__)

SPARQL_ENDPOINT = "https://ja.dbpedia.org/sparql"
SEARCH_WORD = "東京都"

weight_list = [{"weight" : 0.9 , "p" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" }, 
               {"weight" : 1 , "p" : "http://dbpedia.org/ontology/wikiPageWikiLink"} , 
               {"weight" : -0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
               {"weight" : -1 , "p" : "http://dbpedia.org/ontology/wikiPageRevisionID"},
               {"weight" : -0.1 , "p" : "http://dbpedia.org/ontology/commonName"},
               {"weight" : -0.1 , "p" : "http://dbpedia.org/ontology/postalCode"},
               {"weight" : -0.1 , "p" : "http://dbpedia.org/ontology/wikiPageExternalLink"},
               {"weight" : -0.1 , "p" : "http://ja.dbpedia.org/property/外部リンク"},
               {"weight" : -1 , "p" : 'http://dbpedia.org/ontology/wikiPageID'},
               {"weight" : -0.1 , "p" : "http://www.w3.org/2000/01/rdf-schema#label"},
               {"weight" : -0.1 , "p" : "http://www.w3.org/2004/02/skos/core#prefLabel"},
               {"weight" : 0.1 , "p" : "http://purl.org/dc/terms/subject"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            ]

@app.route('/', methods=['GET', 'POST'])
def index():
    query = SEARCH_WORD
    if request.method == 'POST':
        # query = request.form['query']
        query = request.form['query']

    response_s1 = requests.get(SPARQL_ENDPOINT, params={
        'default-graph-uri': 'http://ja.dbpedia.org',
        'query': "select distinct * where { ?s ?p <http://ja.dbpedia.org/resource/" + query + "> . }",
        'format': 'application/sparql-results+json',
        'timeout': 0,
        'signal_void': 'on'
    })
    response_o1 = requests.get(SPARQL_ENDPOINT, params={
        'default-graph-uri': 'http://ja.dbpedia.org',
        'query': "select distinct * where { <http://ja.dbpedia.org/resource/" + query + "> ?p ?o . }",
        'format': 'application/sparql-results+json',
        'timeout': 0,
        'signal_void': 'on'
    })
    graph_name_list = []
    def get_results_s2(input,graph_name_list):
        response_s2 = requests.get(SPARQL_ENDPOINT, params={
            'default-graph-uri': 'http://ja.dbpedia.org',
            'query': "select distinct * where { <http://ja.dbpedia.org/resource/" + input + "> ?p ?o . }",
            'format': 'application/sparql-results+json',
            'timeout': 0,
            'signal_void': 'on'
        })
        data = response_s2.json()
        results = data.get('results', {}).get('bindings', [])
        if results == []:
            return results
        else:
            return_results = [result for result in results if result["s"]["value"] not in graph_name_list]
            return return_results

    
    if response_s1.status_code == 200:
        data = response_s1.json()
        results_s1 = data.get('results', {}).get('bindings', [])
        node_list_1st_s = sorted([{"name" : result["s"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"s" : result["s"]["value"] , "p_list" : [line["p"]["value"] for line in results_s1 if line["s"]["value"] == result["s"]["value"]]} for result in results_s1]], key=lambda x:x["weight"], reverse=True)
        if len(node_list_1st_s) > 10:
            node_list_1st_s = node_list_1st_s[:10]
        for node in node_list_1st_s:
            graph_name_list.append(node["name"])
            
    else:
        results_s1 = []
        print("error: response_s1.status_code = ", response_s1.status_code)
    
    if response_o1.status_code == 200:
        data = response_o1.json()
        results_o1 = data.get('results', {}).get('bindings', [])
        node_list_1st_o = sorted([{"name" : result["o"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"o" : result["o"]["value"] , "p_list" : [line["p"]["value"] for line in results_o1 if line["o"]["value"] == result["o"]["value"]]} for result in results_o1]], key=lambda x:x["weight"], reverse=True)
        if len(node_list_1st_o) > 10:
            node_list_1st_o = node_list_1st_o[:10]
        for node in node_list_1st_o:
            graph_name_list.append(node["name"])
    else:
        results_o1 = []
        print("error: response_o1.status_code = ", response_o1.status_code)

    

    
    return render_template('index.html', query=query, results=results_s1 , node_list_1st_s=node_list_1st_s , node_list_1st_o=node_list_1st_o)

if __name__ == '__main__':
    app.run(debug=True)
