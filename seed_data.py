from parser import parse_query
from db.neo4j_client import add_query_to_graph

dummy_queries = [
    # Customers
    "INSERT INTO customers (name, email, credit_limit) VALUES ('Rahul Sharma', 'rahul@mail.com', 50000)",
    "INSERT INTO customers (name, email, credit_limit) VALUES ('Priya Singh', 'priya@mail.com', 30000)",
    "INSERT INTO customers (name, email, credit_limit) VALUES ('Aman Verma', 'aman@mail.com', 20000)",
    "INSERT INTO customers (name, email, credit_limit) VALUES ('Sneha Patil', 'sneha@mail.com', 45000)",
    "INSERT INTO customers (name, email, credit_limit) VALUES ('Karan Mehta', 'karan@mail.com', 60000)",

    # Products
    "INSERT INTO products (name, price, stock) VALUES ('Laptop', 55000, 20)",
    "INSERT INTO products (name, price, stock) VALUES ('Mouse', 500, 100)",
    "INSERT INTO products (name, price, stock) VALUES ('Keyboard', 1200, 80)",
    "INSERT INTO products (name, price, stock) VALUES ('Monitor', 9000, 30)",
    "INSERT INTO products (name, price, stock) VALUES ('Headphones', 2500, 60)",

    # Orders
    "INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES (1, 1, 1, 55000, 'confirmed')",
    "INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES (2, 2, 2, 1000, 'confirmed')",
    "INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES (3, 3, 1, 1200, 'pending')",
    "INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES (4, 4, 1, 9000, 'confirmed')",
    "INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES (5, 5, 3, 7500, 'shipped')",

    # Normal, realistic updates (build up "history" for Gatekeeper to compare against later)
    "UPDATE products SET stock = 19 WHERE id = 1",
    "UPDATE products SET stock = 98 WHERE id = 2",
    "UPDATE orders SET status = 'shipped' WHERE id = 1",
    "UPDATE orders SET status = 'delivered' WHERE id = 2",
    "UPDATE customers SET credit_limit = 55000 WHERE id = 1",
]

for sql in dummy_queries:
    try:
        parsed = parse_query(sql)
        add_query_to_graph(
            raw_sql=parsed["raw_sql"],
            operation=parsed["operation"],
            table=parsed["table"],
            columns=parsed["columns"]
        )
    except Exception as e:
        print(f"Skipped (parse error): {sql} — {e}")

print("Seeding complete — 20 queries processed.")