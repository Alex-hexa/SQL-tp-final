def get_main_search(search_q, cat_id, min_p, max_p, offset, limit):
    where_clauses = ["1=1"]
    # Utilisation de méthodes sécurisées pour éviter les injections
    if search_q: 
        where_clauses.append(f"sa.title ILIKE '%%{search_q}%%'")
    if cat_id and cat_id.isdigit(): 
        where_clauses.append(f"p.category_id = {cat_id}")
    if min_p and min_p.isdigit(): 
        where_clauses.append(f"sa.price >= {min_p}")
    if max_p and max_p.isdigit(): 
        where_clauses.append(f"sa.price <= {max_p}")
    
    where_str = " AND ".join(where_clauses)
    
    return f"""
    SELECT 
        sa.id, sa.title, sa.price, sa.description,
        p.name as product_name, c.name as category_name,
        (SELECT name FROM picture WHERE sale_ad_id = sa.id LIMIT 1) as first_pic,
        (SELECT COUNT(*) FROM picture WHERE sale_ad_id = sa.id) as nb_photos,
        COUNT(*) OVER() as total_count
    FROM sale_ad sa
    JOIN product p ON sa.product_id = p.id
    JOIN category c ON p.category_id = c.id
    WHERE {where_str}
    ORDER BY sa.id DESC
    LIMIT {limit} OFFSET {offset}
    """

# Requêtes pour le Dashboard
GET_DETAILS = """
SELECT sa.title AS annonce, p.name AS produit, c.name AS categorie, sa.price, u.firstname || ' ' || u.lastname AS vendeur
FROM sale_ad sa
INNER JOIN product p ON sa.product_id = p.id
INNER JOIN category c ON p.category_id = c.id
INNER JOIN "user" u ON sa.user_id = u.id
"""

GET_ORPHANS = "SELECT p.name AS produit_orphelin FROM product p LEFT JOIN sale_ad sa ON p.id = sa.product_id WHERE sa.id IS NULL"

GET_COUNT_BY_CAT = "SELECT c.name AS categorie, COUNT(sa.id) AS nombre_annonces FROM category c JOIN product p ON c.id = p.category_id JOIN sale_ad sa ON p.id = sa.product_id GROUP BY c.name"

GET_MULTI_ROLES = "SELECT u.firstname, u.lastname, COUNT(ut.type_id) AS nb_roles FROM \"user\" u JOIN user_type ut ON u.id = ut.user_id GROUP BY u.id, u.firstname, u.lastname HAVING COUNT(ut.type_id) > 1"

GET_CA_USER = """
SELECT u.firstname, u.lastname, SUM(sa.price) AS chiffre_affaires
FROM "user" u
JOIN sale_ad sa ON u.id = sa.user_id
JOIN command_product cp ON sa.id = cp.sale_ad_id
GROUP BY u.id, u.firstname, u.lastname
ORDER BY chiffre_affaires DESC
"""