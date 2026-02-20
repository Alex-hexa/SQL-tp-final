import os
import math
from flask import Flask, render_template, request
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SUPABASE_KEY")

url: str = os.environ.get("SUPABASE_URL")
key: str = app.secret_key
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    # 1. Récupération des paramètres de recherche (Filtres)
    search_query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    page = int(request.args.get('page', 1))
    
    per_page = 6 # Nombre d'annonces par page

    try:
        # 2. Construction de la requête Supabase
        # On utilise !inner sur product pour pouvoir filtrer sur les colonnes de la table jointe
        query = supabase.table('sale_ad').select(
            "id, title, price, description, picture(name), product!inner(name, category_id, category(name))", 
            count="exact"
        )

        # Application des filtres conditionnels
        if search_query:
            query = query.ilike('title', f"%{search_query}%")
        
        if category_id:
            query = query.eq('product.category_id', category_id)
            
        if min_price:
            query = query.gte('price', min_price)
            
        if max_price:
            query = query.lte('price', max_price)

        # 3. Pagination & Tri
        start = (page - 1) * per_page
        end = start + per_page - 1
        query = query.range(start, end).order('id', desc=True)

        # 4. Exécution
        res = query.execute()
        ads = res.data
        total_count = res.count if res.count else 0
        total_pages = math.ceil(total_count / per_page)

        # 5. Récupération des catégories pour remplir le menu déroulant
        cats_res = supabase.table('category').select('id, name').order('name').execute()
        categories = cats_res.data

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

if __name__ == '__main__':
    app.run(debug=True)