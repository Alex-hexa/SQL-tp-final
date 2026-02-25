import os
import math
from flask import Flask, render_template, request
from supabase import create_client, Client
from dotenv import load_dotenv
import queries 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SUPABASE_KEY")

# Initialisation du client Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    """Route principale : Recherche, Filtres et Pagination en SQL brut"""
    # Récupération des filtres depuis l'URL
    search_query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    page = int(request.args.get('page', 1))
    
    per_page = 6
    offset = (page - 1) * per_page

    try:
        # Exécution de la recherche principale via queries.py
        sql_main = queries.get_main_search(search_query, category_id, min_price, max_price, offset, per_page)
        res = supabase.rpc('exec_sql', {'query_text': sql_main}).execute()
        
        ads = res.data if res.data else []
        
        # Récupération du total pour la pagination (inclus dans la requête via COUNT(*) OVER())
        total_count = ads[0]['total_count'] if ads else 0
        total_pages = math.ceil(total_count / per_page)

        # Récupération des catégories pour le filtre
        sql_cats = "SELECT id, name FROM category ORDER BY name"
        cats_res = supabase.rpc('exec_sql', {'query_text': sql_cats}).execute()
        categories = cats_res.data if cats_res.data else []

        return render_template(
            'index.html', 
            ads=ads, 
            categories=categories, 
            current_category=category_id,
            search_query=search_query,
            min_price=min_price,
            max_price=max_price,
            page=page, 
            total_pages=total_pages
        )

    except Exception as e:
        return f"Erreur de base de données : {str(e)}"

@app.route('/sql')
@app.route('/sql/<string:query_id>')
def sql_dashboard(query_id=None):
    """Route Admin : Exécution des requêtes SQL imposées"""
    res_data = []
    error = None
    
    # Mapping des IDs vers les constantes SQL de queries.py
    sql_map = {
        'details': queries.GET_DETAILS,
        'orphelins': queries.GET_ORPHANS,
        'count_cat': queries.GET_COUNT_BY_CAT,
        'multi_role': queries.GET_MULTI_ROLES,
        'ca_user': queries.GET_CA_USER
    }

    if query_id in sql_map:
        try:
            # Appel de la fonction stockée avec la requête SQL brute
            res = supabase.rpc('exec_sql', {'query_text': sql_map[query_id]}).execute()
            res_data = res.data if res.data else []
        except Exception as e:
            error = f"Erreur d'exécution SQL : {str(e)}"
        
    return render_template('sql.html', result=res_data, active_query=query_id, error=error)

if __name__ == '__main__':
    app.run(debug=True)