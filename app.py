import os
import re
# from tkinter import SE
# from urllib import response
from flask import Flask, render_template, request, redirect, url_for
import requests
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
db = SQLAlchemy(app)

# ランダムな24バイトのsecret_keyを生成
app.secret_key = os.urandom(24)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



# User model
# class User(UserMixin):
#     def __init__(self, id, username , password):
#         self.id = id
#         self.username = username
#         self.password = password
# sqlalchemyのモデルを作成
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    @property
    def is_active(self):
        # ここに無効化の条件を追加する
        return True
    
    def get_id(self):
        return str(self.id)

# 現在の登録データをdbから取得
def get_all_users():
    return User.query.all()

# Create a new user
def add_user(username, password):
    # Create a new User object
    new_user = User(username=username, password=password)
    
    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    
    # Return the newly created user
    return new_user


# Simple in-memory user store
# In a real application, you would use a database
# users = {
#     1: User(1, "user1", "pass"),
#     2: User(2, "user2", "pass"),
#     3: User(3, "", "tlPd8v"),
# }

# #パスワードのハッシュ化
# for user in users.values():
#     user.password = generate_password_hash(user.password)


@login_manager.user_loader
def load_user(user_id):
    # Flask-Login uses this callback to reload the user object from the user ID stored in the session
    return User.query.get(int(user_id))
    # return users.get(int(user_id))

# データベース情報を表示
@app.route('/profile' , methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', users=get_all_users())

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # 入力されたユーザ名がすでに登録されているかを確認
        if next((u for u in get_all_users() if u.username == username), None):
            msg = "このユーザー名はすでに登録されています(重複しないユーザー名を入力してください)"
        else:
            add_user(username, generate_password_hash(password))
            msg = "登録が完了しました： " + username
    return render_template('signup.html', msg=msg)

# ユーザーを削除
@app.route('/delete', methods=['POST'])
@login_required
def delete():
    user_id = request.form['user_id']
    user = User.query.filter_by(id=user_id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
         # 入力されたパスワードが登録されているパスワードハッシュと一致するかを確認
        user = next((u for u in get_all_users() if u.username == username and check_password_hash(u.password, password)), None)
        # 管理者ユーザーの場合は、管理者ページにリダイレクト
        if user and user.username == "master":
            login_user(user)
            return redirect(url_for('profile'))
        # ユーザー名とパスワードが一致した場合は、ログイン
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            msg = "ユーザー名またはパスワードが間違っています"
    return render_template('login.html', msg=msg)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/protected')
@login_required
def protected():
    return f'Hello, {current_user.username}! This is a protected page. <a href="/logout">Logout</a>'




SPARQL_ENDPOINT = "https://ja.dbpedia.org/sparql"
query = "山陽本線"
# { id:"center", label: '姫路城', title: 'This is center node' ,font: {size: 50}},
#             { from: "中央", to: 1, arrows: 'to , middle' },
# graph_data_list = {"nodes": [ { "id" : "中央" , "label" : "姫路城" , "title" : "This is center node" , "font" : {"size" : 50} }] , "edges" : [ { "from" : "中央" , "to" : 1 , "arrows" : "to , middle" } ]}



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
               {"weight" : -0.1 , "p" : "http://www.w3.org/2002/07/owl#sameAs"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            #    {"weight" : 0.1 , "p" : "http://xmlns.com/foaf/0.1/name"},
            ]
@app.route('/', methods=['GET' , 'POST'])
@login_required
def index(query=query):
    if request.method == 'POST':
        # input check
        while request.form['query'] == "" or len(request.form['query']) > 20 or re.compile(r"[!-/:-@[-`{-~]").search(request.form['query']):
            print("error: invalid input")
            return redirect('/top')
        query = request.form['query']

        return redirect('/results')
    return render_template('top.html')



@app.route('/results', methods=['GET', 'POST'])
@login_required
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
            graph_nodes.append({"id" : "中央" , "label" : query[:7]+"..." , "title" : query , "font" : {"size" : 50} , "wikipedia_url" : wikipedia_url , "google_scholar_url" : google_scholar_url , "color" : {"background" : "#f79e9e","border" : "black"}})
        else:
            graph_nodes.append({"id" : "中央" , "label" : query , "title" : query , "font" : {"size" : 50} , "wikipedia_url" : wikipedia_url , "google_scholar_url" : google_scholar_url , "color" : {"background" : "#f79e9e","border" : "black"}})

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
        results = [{"o" : {"value" : trim_node_name(result["o"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        if results == []:
            return results
        else:
            return_results = [result for result in results if result["o"]["value"] not in graph_name_list]
            return return_results
    

    
    if response_s1.status_code == 200:
        data = response_s1.json()
        results_s1 = [{"s" : {"value" : trim_node_name(result["s"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        node_list_1st_s = sorted([{"name" : result["s"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"s" : result["s"]["value"] , "p_list" : [line["p"]["value"] for line in results_s1 if line["s"]["value"] == result["s"]["value"]]} for result in results_s1]], key=lambda x:x["weight"], reverse=True)
        if len(node_list_1st_s) > 9:
            node_list_1st_s = node_list_1st_s[:9]
        for i in range(len(node_list_1st_s)):
            graph_name_list.append(node_list_1st_s[i]["name"])
            new_node_id = "リンク先_" + str(i+1) + "位"
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
                graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title + "AND"  + query,"color" : "lightblue"})
                # もし一つ前のnodeも追加されているのなら矢印のないエッジで、それぞれのnode間も結ぶ
                # { from: 1, to: 2, arrows: { to: { enabled: false } } },
                # if i > 0 and "リンク先_" + str(i) + "位" in [node["id"] for node in graph_nodes]:
                #     graph_edges.append({"from" : "リンク先_" + str(i) + "位" , "to" : new_node_id , "arrows" : {"to" : {"enabled" : "false"}}})

            graph_edges.append({"from" : "中央" , "to" : new_node_id , "arrows" : "to , middle"})

    else:
        results_s1 = []
        print("error: response_s1.status_code = ", response_s1.status_code)
    
    if response_o1.status_code == 200:
        data = response_o1.json()
        results_o1 = [{"o" : {"value" : trim_node_name(result["o"]["value"])} , "p" : {"value" : result["p"]["value"]} } for result in data.get('results', {}).get('bindings', {})]
        node_list_1st_o = sorted([{"name" : result["o"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"o" : result["o"]["value"] , "p_list" : [line["p"]["value"] for line in results_o1 if line["o"]["value"] == result["o"]["value"]]} for result in results_o1]], key=lambda x:x["weight"], reverse=True)
        if len(node_list_1st_o) > 9:
            node_list_1st_o = node_list_1st_o[:9]
        for i in range(len(node_list_1st_o)):
            graph_name_list.append(node_list_1st_o[i]["name"])
            new_node_id = "リンク元_" + str(i+1) + "位"
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
                graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title + "AND"  + query})
                # もし一つ前のnodeも追加されているのなら矢印のないエッジで、それぞれのnode間も結ぶ
                # if i > 0 and "リンク元_" + str(i) + "位" in [node["id"] for node in graph_nodes]:
                #     graph_edges.append({"from" : "リンク元_" + str(i) + "位" , "to" : new_node_id , "arrows" : {"to" : {"enabled" : "false" }}})

            graph_edges.append({"from" : new_node_id , "to" : "中央" , "arrows" : "to , middle"})
    else:
        results_o1 = []
        print("error: response_o1.status_code = ", response_o1.status_code)


    if node_list_1st_s != [] and response_s1.status_code == 200:
        parent_node_index = -1
        for node in node_list_1st_s:
            parent_node_index += 1
            parent_node_id = "リンク先_" + str(parent_node_index + 1) + "位"
            parent_node_label = node["name"]
            # parent_node_title = node["name"]
            if len(node["name"]) > 7:
                parent_node_label = node["name"][:7]+"..."
            if parent_node_label in [node["label"] for node in graph_nodes]:
                parent_node_id = [node["id"] for node in graph_nodes if node["label"] == parent_node_label][0]
            
            results_s2 = get_results_s2(node["name"],graph_name_list)
            if results_s2 != []:
                node_list_2nd_s = sorted([{"name" : result["s"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"s" : result["s"]["value"] , "p_list" : [line["p"]["value"] for line in results_s1 if line["s"]["value"] == result["s"]["value"]]} for result in results_s2]], key=lambda x:x["weight"], reverse=True)
                # nodeCountDepth2 = len(node_list_2nd_s)
                if len(node_list_2nd_s) > 4:
                    node_list_2nd_s = node_list_2nd_s[:4]
                for i in range(len(node_list_2nd_s)):
                    graph_name_list.append(node_list_2nd_s[i]["name"])
                    new_node_id = "リンク先_" + str(parent_node_index + 1) + "位の" + str(i+1) + "位"
                    new_node_label = node_list_2nd_s[i]["name"]
                    new_node_title = node_list_2nd_s[i]["name"]
                    if len(node_list_2nd_s[i]["name"]) > 7:
                        new_node_label = node_list_2nd_s[i]["name"][:7]+"..."
                    if new_node_label in [node["label"] for node in graph_nodes]:
                        new_node_id = [node["id"] for node in graph_nodes if node["label"] == new_node_label][0]
                    else:
                        graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title + "AND"  + query,"color" : "lightblue"})
                    graph_edges.append({"from" : parent_node_id , "to" : new_node_id , "arrows" : "to , middle"})
            else:
                node_list_2nd_s = []

    if node_list_1st_o != [] and response_o1.status_code == 200:
        parent_node_id = -1
        for node in node_list_1st_o:
            parent_node_index += 1
            parent_node_id = "リンク元_" + str(parent_node_index + 1) + "位"
            parent_node_label = node["name"]
            # parent_node_title = node["name"]
            if len(node["name"]) > 7:
                parent_node_label = node["name"][:7]+"..."
            if parent_node_label in [node["label"] for node in graph_nodes]:
                parent_node_id = [node["id"] for node in graph_nodes if node["label"] == parent_node_label][0]

            results_o2 = get_results_o2(node["name"],graph_name_list)
            if results_o2 != []:
                node_list_2nd_o = sorted([{"name" : result["o"] , "weight" : sum([1 + sum([(weight["weight"] - 1) for weight in weight_list if weight["p"] == p]) for p in result["p_list"]])} for result in [{"o" : result["o"]["value"] , "p_list" : [line["p"]["value"] for line in results_o1 if line["o"]["value"] == result["o"]["value"]]} for result in results_o2]], key=lambda x:x["weight"], reverse=True)
                # nodeCountDepth2 = len(node_list_2nd_o)
                if len(node_list_2nd_o) > 4:
                    node_list_2nd_o = node_list_2nd_o[:4]

                for i in range(len(node_list_2nd_o)):
                    graph_name_list.append(node_list_2nd_o[i]["name"])
                    new_node_id = "リンク元_" + str(parent_node_index + 1) + "位の" + str(i+1) + "位"
                    new_node_label = node_list_2nd_o[i]["name"]
                    new_node_title = node_list_2nd_o[i]["name"]
                    if len(node_list_2nd_o[i]["name"]) > 7:
                        new_node_label = node_list_2nd_o[i]["name"][:7]+"..."
                    if new_node_label in [node["label"] for node in graph_nodes]:
                        new_node_id = [node["id"] for node in graph_nodes if node["label"] == new_node_label][0]
                    else:
                        graph_nodes.append({"id" : new_node_id , "label" : new_node_label , "title" : new_node_title , "font" : {"size" : 20}, "wikipedia_url" : "https://ja.wikipedia.org/wiki/" + new_node_title , "google_scholar_url" : "https://scholar.google.com/scholar?hl=ja&as_sdt=0%2C5&q=" + new_node_title + "AND"  + query})
                    graph_edges.append({"from" : new_node_id , "to" : parent_node_id , "arrows" : "to , middle"})
            else:
                node_list_2nd_o = []




    

    
    return render_template('index.html', query=query, results=results_s1 , node_list_1st_s=node_list_1st_s , node_list_1st_o=node_list_1st_o, graph_name_list=graph_name_list,graph_nodes=graph_nodes,graph_edges=graph_edges)

    

if __name__ == '__main__':
    # Create all database tables
    with app.app_context():
        db.create_all()
    server_port = os.environ.get('PORT', '8080')
    app.run(debug=False, port=server_port, host='0.0.0.0')

