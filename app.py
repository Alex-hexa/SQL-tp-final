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
    search_query = request.args.get('q', '')
    category_id = request.args.get('category', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    page = int(request.args.get('page', 1))
    per_page = 6

    try:
        query = supabase.table('sale_ad').select(
            "id, title, price, description, picture(name), product!inner(name, category_id, category(name))", 
            count="exact"
        )

        if search_query:
            query = query.ilike('title', f"%{search_query}%")
        if category_id:
            query = query.eq('product.category_id', category_id)
        if min_price:
            query = query.gte('price', min_price)
        if max_price:
            query = query.lte('price', max_price)

        start = (page - 1) * per_page
        end = start + per_page - 1
        query = query.range(start, end).order('id', desc=True)

        res = query.execute()
        ads = res.data
        total_count = res.count if res.count else 0
        total_pages = math.ceil(total_count / per_page)

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

@app.route('/sql')
@app.route('/sql/<string:query_id>')
def sql_dashboard(query_id=None):
    res_data = []
    error = None
    
    try:
        if query_id == 'details':
            res = supabase.table('sale_ad').select("title, price, product(name, category(name)), user(firstname, lastname)").execute()
            for row in res.data:
                res_data.append({
                    'annonce': row.get('title'),
                    'produit': row.get('product', {}).get('name') if row.get('product') else None,
                    'categorie': row.get('product', {}).get('category', {}).get('name') if row.get('product') and row.get('product').get('category') else None,
                    'price': row.get('price'),
                    'vendeur': f"{row.get('user', {}).get('firstname', '')} {row.get('user', {}).get('lastname', '')}".strip()
                })

        elif query_id == 'orphelins':
            res = supabase.table('product').select("name, sale_ad(id)").execute()
            for row in res.data:
                if not row.get('sale_ad'):
                    res_data.append({'produit_orphelin': row.get('name')})

        elif query_id == 'count_cat':
            res = supabase.table('category').select("name, product(sale_ad(id))").execute()
            for row in res.data:
                count = sum(len(p.get('sale_ad', [])) for p in row.get('product', []))
                res_data.append({
                    'categorie': row.get('name'),
                    'nombre_annonces': count
                })

        elif query_id == 'multi_role':
            res = supabase.table('user').select("firstname, lastname, user_type(type_id)").execute()
            for row in res.data:
                nb_roles = len(row.get('user_type', []))
                if nb_roles > 1:
                    res_data.append({
                        'firstname': row.get('firstname'),
                        'lastname': row.get('lastname'),
                        'nb_roles': nb_roles
                    })

        elif query_id == 'ca_user':
            res = supabase.table('user').select("firstname, lastname, sale_ad(price, command_product(command_id))").execute()
            for row in res.data:
                total_ca = 0
                for ad in row.get('sale_ad', []):
                    price = float(ad.get('price', 0))
                    count = len(ad.get('command_product', []))
                    total_ca += (price * count)
                res_data.append({
                    'firstname': row.get('firstname'),
                    'lastname': row.get('lastname'),
                    'chiffre_affaires': f"{total_ca:.2f}"
                })
            res_data = sorted(res_data, key=lambda x: float(x['chiffre_affaires']), reverse=True)

    except Exception as e:
        error = f"Erreur d'exécution : {str(e)}"
        
    return render_template('sql.html', result=res_data, active_query=query_id, error=error)

if __name__ == '__main__':
    app.run(debug=True)