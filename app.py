import os
from flask import Flask, render_template
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
    return render_template('index.html')

@app.route('/query/<string:query_id>')
def execute_query(query_id):
    try:
        res_data = []
        
        if query_id == 'details':
            # On ajoute "picture(id)" pour pouvoir compter les photos liées à l'annonce
            res = supabase.table('sale_ad').select("title, price, product(name, category(name)), user(firstname, lastname), picture(id)").execute()
            for row in res.data:
                res_data.append({
                    'annonce': row.get('title'),
                    'produit': row.get('product', {}).get('name') if row.get('product') else None,
                    'categorie': row.get('product', {}).get('category', {}).get('name') if row.get('product') and row.get('product').get('category') else None,
                    'price': row.get('price'),
                    'vendeur': f"{row.get('user', {}).get('firstname', '')} {row.get('user', {}).get('lastname', '')}".strip(),
                    'nb_photo': len(row.get('picture', [])) # Comptage des photos comme le COUNT(pi.id)
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

        elif query_id == 'performance':
            res = supabase.table('category').select("name, product(sale_ad(id, price, command_product(command_id)))").execute()
            for row in res.data:
                nb_annonces = 0
                nb_ventes = 0
                ca_total = 0
                
                for p in row.get('product', []):
                    for ad in p.get('sale_ad', []):
                        nb_annonces += 1
                        ventes_ad = len(ad.get('command_product', []))
                        nb_ventes += ventes_ad
                        ca_total += (float(ad.get('price', 0)) * ventes_ad)
                
                taux = round((nb_ventes / nb_annonces * 100), 2) if nb_annonces > 0 else 0
                
                res_data.append({
                    'categorie': row.get('name'),
                    'nombre_annonces': nb_annonces,
                    'nombre_ventes': nb_ventes,
                    'taux_conversion': f"{taux}%",
                    'ca_total': f"{ca_total:.2f}"
                })
            res_data = sorted(res_data, key=lambda x: float(x['ca_total']), reverse=True)

        elif query_id == 'best_seller':
            res = supabase.table('product').select("name, category(name), sale_ad(command_product(command_id))").execute()
            for row in res.data:
                nb_ventes = 0
                for ad in row.get('sale_ad', []):
                    nb_ventes += len(ad.get('command_product', []))
                
                res_data.append({
                    'nom_produit': row.get('name'),
                    'categorie': row.get('category', {}).get('name') if row.get('category') else None,
                    'nombre_de_ventes': nb_ventes
                })
            res_data = sorted(res_data, key=lambda x: x['nombre_de_ventes'], reverse=True)[:1]

        return render_template('index.html', result=res_data, active_query=query_id)
    
    except Exception as e:
        return f"Erreur lors de l'exécution : {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)