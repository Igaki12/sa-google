import os
import re
# from tkinter import SE
# from urllib import response
from flask import Flask, render_template, request , redirect
import requests

app = Flask(__name__)
app.debug = True

SPARQL_ENDPOINT = "https://ja.dbpedia.org/sparql"
query = "東京都"
# { id:"center", label: '姫路城', title: 'This is center node' ,font: {size: 50}},
#             { from: "center", to: 1, arrows: 'to , middle' },
# graph_data_list = {"nodes": [ { "id" : "center" , "label" : "姫路城" , "title" : "This is center node" , "font" : {"size" : 50} }] , "edges" : [ { "from" : "center" , "to" : 1 , "arrows" : "to , middle" } ]}



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
@app.route('/', methods=['GET' , 'POST'])
def index(query=query):
    if request.method == 'POST':
        # input check
        while request.form['query'] == "" or len(request.form['query']) > 20 or re.compile(r"[!-/:-@[-`{-~]").search(request.form['query']):
            print("error: invalid input")
            return redirect('/')
        query = request.form['query']

        return redirect('/results')
    return render_template('top.html')






# @app.route('/', methods=['GET', 'POST'])
@app.route('/results', methods=['GET', 'POST'])
def results(query=query):
    graph_nodes = []
    graph_edges = []
    if request.method == 'GET':
        return redirect('/')
    if request.method == 'POST':
        # input check
        while request.form['query'] == "" or len(request.form['query']) > 30 or re.compile(r"[!-/:-@[-`{-~]").search(request.form['query']):
            print("error: invalid input")
        query = request.form['query']
        wikipedia_url = "https://ja.wikipedia.org/wiki/" + query
        google_scholar_url = "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + query

                # もし文字数が7文字以上の場合は、ラベルには7文字までを表示する
        if len(query) > 7:
            graph_nodes.append({"id" : "center" , "label" : query[:7]+"..." , "title" : query , "font" : {"size" : 40} , "wikipedia_url" : wikipedia_url , "google_scholar_url" : google_scholar_url , "color" : "lightblue"})
        else:
            graph_nodes.append({"id" : "center" , "label" : query , "title" : query , "font" : {"size" : 40} , "wikipedia_url" : wikipedia_url , "google_scholar_url" : google_scholar_url , "color" : "lightblue","border" : "blue","hover": "white"})

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
        if input == "http://ja.dbpedia.org/resource/" or len(input) > 20:
            return []
        response_s2 = requests.get(SPARQL_ENDPOINT, params={
            'default-graph-uri': 'http://ja.dbpedia.org',
            'query': "select distinct * where { ?s ?p <http://ja.dbpedia.org/resource/" + input + "> . }",
            'format': 'application/sparql-results+json',
            'timeout': 0,
            'signal_void': 'on'
        })
        print(response_s2.url)
        print(response_s2.status_code)
        print(response_s2.text)
        print(response_s2.json())

        data = response_s2.json()
        if response_s2.status_code != 200:
            print("error: response_s2.status_code = ", response_s2.status_code)
            return []
        # results = data.get('results', {}).get('bindings', [])
        results = [{"s" : {"value" : trim_node_name(result["s"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        if results == []:
            return results
        else:
            return_results = [result for result in results if result["s"]["value"] not in graph_name_list]
            return return_results
        
    def trim_node_name(name):
        return name.replace("http://ja.dbpedia.org/resource/","").replace("http://dbpedia.org/resource/","").replace("http://ja.wikipedia.org/wiki/","").replace("http://www.w3.org/2002/07/owl#Thing","").replace("http://wikidata.dbpedia.org/resource/","").replace("http://rdf.freebase.com/ns/","").replace("Category:","").replace("Template:","").replace("Property:","")
        
    def get_results_o2(input,graph_name_list):
        if input == "http://ja.dbpedia.org/resource/" or len(input) > 20:
            return []
        response_o2 = requests.get(SPARQL_ENDPOINT, params={
            'default-graph-uri': 'http://ja.dbpedia.org',
            'query': "select distinct * where { <http://ja.dbpedia.org/resource/" + input + "> ?p ?o . }",
            'format': 'application/sparql-results+json',
            'timeout': 0,
            'signal_void': 'on'
        })
        print(response_o2)
        data = response_o2.json()
        if response_o2.status_code != 200:
            print("error: response_o2.status_code = ", response_o2.status_code)
            return []
        # results = data.get('results', {}).get('bindings', [])
        results = [{"o" : {"value" : trim_node_name(result["o"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        if results == []:
            return results
        else:
            return_results = [result for result in results if result["o"]["value"] not in graph_name_list]
            return return_results
    

    
    if response_s1.status_code == 200:
        data = response_s1.json()
        # results_s1 = data.get('results', {}).get('bindings', [])
        results_s1 = [{"s" : {"value" : trim_node_name(result["s"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        node_list_1st_s = sorted([{"name" : result["s"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"s" : result["s"]["value"] , "p_list" : [line["p"]["value"] for line in results_s1 if line["s"]["value"] == result["s"]["value"]]} for result in results_s1]], key=lambda x:x["weight"], reverse=True)
        if len(node_list_1st_s) > 9:
            node_list_1st_s = node_list_1st_s[:9]
        # for node in node_list_1st_s:
        for i in range(len(node_list_1st_s)):
            graph_name_list.append(node_list_1st_s[i]["name"])
            new_node_id = "subject_" + str(i+1) + "位"
            new_node_label = node_list_1st_s[i]["name"]
            new_node_title = node_list_1st_s[i]["name"]
            # もし7文字以上なら、7文字までに減らす。余分な 部分をカットする。
            if len(node_list_1st_s[i]["name"]) > 7:
                new_node_label = node_list_1st_s[i]["name"][:7]+"..."
            # 名前に被りがある場合は、nodeを追加せず、 IDだけ取得する
            if new_node_label in [node["label"] for node in graph_nodes]:
                new_node_id = [node["id"] for node in graph_nodes if node["label"] == new_node_label][0]
                # かぶりは、出ないはずなので、この[0]のコードは要らないかもしれない
            else:
                graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title,"color" : "lightblue"})
                # もし一つ前のnodeも追加されているのなら矢印のないエッジで、それぞれのnode間も結ぶ
                # { from: 1, to: 2, arrows: { to: { enabled: false } } },
                # if i > 0 and "subject_" + str(i) + "位" in [node["id"] for node in graph_nodes]:
                #     graph_edges.append({"from" : "subject_" + str(i) + "位" , "to" : new_node_id , "arrows" : {"to" : {"enabled" : "false"}}})

            graph_edges.append({"from" : "center" , "to" : new_node_id , "arrows" : "to , middle"})

    else:
        results_s1 = []
        print("error: response_s1.status_code = ", response_s1.status_code)
    
    if response_o1.status_code == 200:
        data = response_o1.json()
        # results_o1 = data.get('results', {}).get('bindings', [])
        results_o1 = [{"o" : {"value" : trim_node_name(result["o"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        node_list_1st_o = sorted([{"name" : result["o"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"o" : result["o"]["value"] , "p_list" : [line["p"]["value"] for line in results_o1 if line["o"]["value"] == result["o"]["value"]]} for result in results_o1]], key=lambda x:x["weight"], reverse=True)
        if len(node_list_1st_o) > 9:
            node_list_1st_o = node_list_1st_o[:9]
        # for node in node_list_1st_o:
        for i in range(len(node_list_1st_o)):
            graph_name_list.append(node_list_1st_o[i]["name"])
            new_node_id = "object_" + str(i+1) + "位"
            new_node_label = node_list_1st_o[i]["name"]
            new_node_title = node_list_1st_o[i]["name"]
            # もし7文字以上なら、7文字までに減らす。余分な 部分をカットする。
            if len(node_list_1st_o[i]["name"]) > 7:
                new_node_label = node_list_1st_o[i]["name"][:7]+"..."
            # 名前に被りがある場合は、nodeを追加せず、 IDだけ取得する
            if new_node_label in [node["label"] for node in graph_nodes]:
                new_node_id = [node["id"] for node in graph_nodes if node["label"] == new_node_label][0]
                # かぶりは、出ないはずなので、この[0]のコードは要らないかもしれない
            else:
                graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title})
                # もし一つ前のnodeも追加されているのなら矢印のないエッジで、それぞれのnode間も結ぶ
                # if i > 0 and "object_" + str(i) + "位" in [node["id"] for node in graph_nodes]:
                #     graph_edges.append({"from" : "object_" + str(i) + "位" , "to" : new_node_id , "arrows" : {"to" : {"enabled" : "false" }}})

            graph_edges.append({"from" : new_node_id , "to" : "center" , "arrows" : "to , middle"})
    else:
        results_o1 = []
        print("error: response_o1.status_code = ", response_o1.status_code)


    if node_list_1st_s != [] and response_s1.status_code == 200:
        parent_node_index = -1
        for node in node_list_1st_s:
            parent_node_index += 1
            parent_node_id = "subject_" + str(parent_node_index + 1) + "位"
            parent_node_label = node["name"]
            # parent_node_title = node["name"]
            if len(node["name"]) > 7:
                parent_node_label = node["name"][:7]+"..."
            if parent_node_label in [node["label"] for node in graph_nodes]:
                parent_node_id = [node["id"] for node in graph_nodes if node["label"] == parent_node_label][0]
            
            results_s2 = get_results_s2(node["name"],graph_name_list)
            if results_s2 != []:
                node_list_2nd_s = sorted([{"name" : result["s"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"s" : result["s"]["value"] , "p_list" : [line["p"]["value"] for line in results_s1 if line["s"]["value"] == result["s"]["value"]]} for result in results_s2]], key=lambda x:x["weight"], reverse=True)
                if len(node_list_2nd_s) > 1:
                    node_list_2nd_s = node_list_2nd_s[:1]
                # for node in node_list_2nd_s:
                #     graph_name_list.append(node["name"])
                # 深度2についても同様に、graph_nodesとgraph_edgesに追加していく
                for i in range(len(node_list_2nd_s)):
                    graph_name_list.append(node_list_2nd_s[i]["name"])
                    new_node_id = "subject_" + str(parent_node_index + 1) + "位の" + str(i+1) + "位"
                    new_node_label = node_list_2nd_s[i]["name"]
                    new_node_title = node_list_2nd_s[i]["name"]
                    if len(node_list_2nd_s[i]["name"]) > 7:
                        new_node_label = node_list_2nd_s[i]["name"][:7]+"..."
                    if new_node_label in [node["label"] for node in graph_nodes]:
                        new_node_id = [node["id"] for node in graph_nodes if node["label"] == new_node_label][0]
                    else:
                        graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title,"color" : "lightblue"})
                    graph_edges.append({"from" : parent_node_id , "to" : new_node_id , "arrows" : "to , middle"})
            else:
                node_list_2nd_s = []

    if node_list_1st_o != [] and response_o1.status_code == 200:
        parent_node_id = -1
        for node in node_list_1st_o:
            parent_node_index += 1
            parent_node_id = "object_" + str(parent_node_index + 1) + "位"
            parent_node_label = node["name"]
            # parent_node_title = node["name"]
            if len(node["name"]) > 7:
                parent_node_label = node["name"][:7]+"..."
            if parent_node_label in [node["label"] for node in graph_nodes]:
                parent_node_id = [node["id"] for node in graph_nodes if node["label"] == parent_node_label][0]

            results_o2 = get_results_o2(node["name"],graph_name_list)
            if results_o2 != []:
                node_list_2nd_o = sorted([{"name" : result["o"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"o" : result["o"]["value"] , "p_list" : [line["p"]["value"] for line in results_o1 if line["o"]["value"] == result["o"]["value"]]} for result in results_o2]], key=lambda x:x["weight"], reverse=True)
                if len(node_list_2nd_o) > 1:
                    node_list_2nd_o = node_list_2nd_o[:1]
                # for node in node_list_2nd_o:
                #     graph_name_list.append(node["name"])
                # 深度2についても同様に、graph_nodesとgraph_edgesに追加していく
                for i in range(len(node_list_2nd_o)):
                    graph_name_list.append(node_list_2nd_o[i]["name"])
                    new_node_id = "object_" + str(parent_node_index + 1) + "位の" + str(i+1) + "位"
                    new_node_label = node_list_2nd_o[i]["name"]
                    new_node_title = node_list_2nd_o[i]["name"]
                    if len(node_list_2nd_o[i]["name"]) > 7:
                        new_node_label = node_list_2nd_o[i]["name"][:7]+"..."
                    if new_node_label in [node["label"] for node in graph_nodes]:
                        new_node_id = [node["id"] for node in graph_nodes if node["label"] == new_node_label][0]
                    else:
                        graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title})
                    graph_edges.append({"from" : new_node_id , "to" : parent_node_id , "arrows" : "to , middle"})
            else:
                node_list_2nd_o = []




    

    
    return render_template('index.html', query=query, results=results_s1 , node_list_1st_s=node_list_1st_s , node_list_1st_o=node_list_1st_o, graph_name_list=graph_name_list,graph_nodes=graph_nodes,graph_edges=graph_edges)

    

if __name__ == '__main__':
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')







"""
A sample Hello World server.
"""
# import os

# from flask import Flask, render_template

# # pylint: disable=C0103
# app = Flask(__name__)


# @app.route('/')
# def hello():
#     """Return a friendly HTTP greeting."""
#     message = "It's running!"

#     """Get Cloud Run environment variables."""
#     service = os.environ.get('K_SERVICE', 'Unknown service')
#     revision = os.environ.get('K_REVISION', 'Unknown revision')

#     return render_template('index.html',
#         message=message,
#         Service=service,
#         Revision=revision)

# if __name__ == '__main__':
#     server_port = os.environ.get('PORT', '8080')
#     app.run(debug=False, port=server_port, host='0.0.0.0')
