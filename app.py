import sqlite3
import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db')


def get_db_connection():
    """Establish and return a connection to the SQLite database with dictionary-like row access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the SQLite database schema and seed initial catalog records if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            status TEXT NOT NULL CHECK (status IN ('Available', 'Checked Out', 'Reserved')) DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Seed baseline records if database is fresh
    cursor.execute("SELECT COUNT(*) AS count FROM books")
    row = cursor.fetchone()
    if row['count'] == 0:
        seed_data = [
            ("The DevOps Handbook", "Gene Kim, Jez Humble, Patrick Debois", "978-1942788002", "DevOps", "Available"),
            ("Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "978-0132350884", "Software Engineering", "Checked Out"),
            ("Continuous Delivery: Reliable Software Releases", "Jez Humble, David Farley", "978-0321601919", "DevOps", "Available"),
            ("Designing Data-Intensive Applications", "Martin Kleppmann", "978-1449373320", "Architecture", "Available"),
            ("Site Reliability Engineering: How Google Runs Production Systems", "Niall Richard Murphy, Betsy Beyer", "978-1491929124", "SRE", "Reserved")
        ]
        cursor.executemany('''
            INSERT INTO books (title, author, isbn, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', seed_data)
        conn.commit()

    conn.close()


# Initialize database at startup
init_db()


# --------------------------------------------------------------------------
# Page Routes
# --------------------------------------------------------------------------
@app.route('/')
def index():
    """Render the primary library portal dashboard and catalog user interface."""
    return render_template('index.html')


@app.route('/health')
def health():
    """Application health and readiness probe for CI/CD and monitoring."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "UP", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "DOWN", "error": str(e)}), 500


# --------------------------------------------------------------------------
# RESTful API Endpoints
# --------------------------------------------------------------------------
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Return aggregated metric cards data: total, available, checked out, reserved, categories."""
    conn = get_db_connection()
    cursor = conn.cursor()

    total = cursor.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    available = cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'Available'").fetchone()[0]
    checked_out = cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'Checked Out'").fetchone()[0]
    reserved = cursor.execute("SELECT COUNT(*) FROM books WHERE status = 'Reserved'").fetchone()[0]
    categories = cursor.execute("SELECT COUNT(DISTINCT category) FROM books").fetchone()[0]

    conn.close()
    return jsonify({
        "total": total,
        "available": available,
        "checked_out": checked_out,
        "reserved": reserved,
        "categories": categories
    }), 200


@app.route('/api/books', methods=['GET'])
def list_books():
    """List all books with optional search filter query params (q, status, category)."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if status_filter and status_filter != 'All':
        sql += " AND status = ?"
        params.append(status_filter)

    sql += " ORDER BY id DESC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    books = [dict(row) for row in rows]
    return jsonify({"count": len(books), "books": books}), 200


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Retrieve metadata for an individual book by ID."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"book": dict(row)}), 200


@app.route('/api/books', methods=['POST'])
def create_book():
    """Create a new book entry in the library catalog."""
    data = request.get_json() or request.form

    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    category = data.get('category', 'General').strip() or 'General'
    status = data.get('status', 'Available').strip() or 'Available'

    if not title or not author or not isbn:
        return jsonify({"error": "Title, Author, and ISBN are required fields"}), 400

    if status not in ['Available', 'Checked Out', 'Reserved']:
        return jsonify({"error": "Status must be one of: Available, Checked Out, Reserved"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO books (title, author, isbn, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, author, isbn, category, status))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return jsonify({"message": "Book registered successfully", "id": new_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"A book with ISBN '{isbn}' already exists"}), 409
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update status or metadata of an existing book."""
    data = request.get_json() or request.form
    if not data:
        return jsonify({"error": "No update payload provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"error": "Book not found"}), 404

    title = data.get('title', existing['title'])
    author = data.get('author', existing['author'])
    category = data.get('category', existing['category'])
    status = data.get('status', existing['status'])

    if status not in ['Available', 'Checked Out', 'Reserved']:
        conn.close()
        return jsonify({"error": "Status must be one of: Available, Checked Out, Reserved"}), 400

    cursor.execute('''
        UPDATE books
        SET title = ?, author = ?, category = ?, status = ?
        WHERE id = ?
    ''', (title, author, category, status, book_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Book record updated successfully"}), 200


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book record from the catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"message": "Book removed from catalog"}), 200


if __name__ == '__main__':
    # Local baseline execution
    app.run(host='0.0.0.0', port=5000, debug=True)
