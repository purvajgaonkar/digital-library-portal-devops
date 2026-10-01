"""Digital Library Search Portal - Application Backend
Phase 2: Feature Development (feature/add-record)
Enterprise-grade CRUD implementation with rigorous input validation and error handling.
"""

import os
import re
import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db')


def get_db_connection():
    """Establish and return an active SQLite connection configured with row access by column name."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables with constraints and default values."""
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

    # Seed initial digital catalog items if table is brand new
    cursor.execute("SELECT COUNT(*) AS count FROM books")
    if cursor.fetchone()['count'] == 0:
        seed_records = [
            ("The DevOps Handbook", "Gene Kim, Jez Humble, Patrick Debois", "978-1942788002", "DevOps", "Available"),
            ("Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "978-0132350884", "Software Engineering", "Checked Out"),
            ("Continuous Delivery: Reliable Software Releases", "Jez Humble, David Farley", "978-0321601919", "DevOps", "Available"),
            ("Designing Data-Intensive Applications", "Martin Kleppmann", "978-1449373320", "Architecture", "Available"),
            ("Site Reliability Engineering: How Google Runs Production Systems", "Niall Richard Murphy, Betsy Beyer", "978-1491929124", "SRE", "Reserved")
        ]
        cursor.executemany('''
            INSERT INTO books (title, author, isbn, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', seed_records)
        conn.commit()

    conn.close()


init_db()


# --------------------------------------------------------------------------
# Validation Helpers
# --------------------------------------------------------------------------
def validate_isbn(isbn_str):
    """Validate standard ISBN format (simple 10 or 13 digits with optional hyphens)."""
    cleaned = re.sub(r'[-\s]', '', isbn_str)
    return len(cleaned) in (10, 13) and cleaned.isalnum()


# --------------------------------------------------------------------------
# Page Routes
# --------------------------------------------------------------------------
@app.route('/')
def index():
    """Serve the primary Digital Library user interface."""
    return render_template('index.html')


@app.route('/health')
def health():
    """DevOps health and readiness probe endpoint."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return jsonify({"status": "UP", "database": "connected", "version": "1.0-MVP"}), 200
    except Exception as exc:
        return jsonify({"status": "DOWN", "error": str(exc)}), 500


# --------------------------------------------------------------------------
# RESTful API Endpoints
# --------------------------------------------------------------------------
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Compute and return real-time catalog aggregates."""
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
    """Retrieve catalog items with optional keyword and status query filtering."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM books WHERE 1=1"
    params = []

    if search_query:
        query += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term])

    if status_filter and status_filter != 'All':
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return jsonify({"count": len(rows), "books": [dict(r) for r in rows]}), 200


@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Retrieve detailed metadata for an individual catalog record."""
    conn = get_db_connection()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()

    if not book:
        return jsonify({"error": f"Book record #{book_id} not found"}), 404
    return jsonify({"book": dict(book)}), 200


@app.route('/api/books', methods=['POST'])
def create_book():
    """
    Deliverable 5: Create Record Workflow.
    Validates mandatory inputs, format integrity, and uniqueness before inserting into SQLite.
    """
    payload = request.get_json() or request.form

    title = str(payload.get('title', '')).strip()
    author = str(payload.get('author', '')).strip()
    isbn = str(payload.get('isbn', '')).strip()
    category = str(payload.get('category', 'General')).strip() or 'General'
    status = str(payload.get('status', 'Available')).strip() or 'Available'

    # 1. Validation: Mandatory fields
    if not title:
        return jsonify({"error": "Validation failed: 'title' is required"}), 400
    if not author:
        return jsonify({"error": "Validation failed: 'author' is required"}), 400
    if not isbn:
        return jsonify({"error": "Validation failed: 'isbn' is required"}), 400

    # 2. Validation: Length constraints
    if len(title) > 200:
        return jsonify({"error": "Title exceeds maximum allowed length of 200 characters"}), 400
    if len(author) > 150:
        return jsonify({"error": "Author exceeds maximum allowed length of 150 characters"}), 400

    # 3. Validation: ISBN format
    if not validate_isbn(isbn):
        return jsonify({"error": f"Invalid ISBN format '{isbn}'. Must be a 10 or 13-digit code."}), 400

    # 4. Validation: Status enum
    valid_statuses = ('Available', 'Checked Out', 'Reserved')
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status '{status}'. Must be one of {valid_statuses}"}), 400

    # 5. Database transaction with uniqueness check
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO books (title, author, isbn, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, author, isbn, category, status))
        conn.commit()
        created_id = cursor.lastrowid
        conn.close()
        return jsonify({
            "message": "Resource successfully registered in library catalog",
            "id": created_id,
            "book": {
                "id": created_id,
                "title": title,
                "author": author,
                "isbn": isbn,
                "category": category,
                "status": status
            }
        }), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": f"Duplicate ISBN: A book with code '{isbn}' already exists in catalog."}), 409
    except Exception as exc:
        conn.close()
        return jsonify({"error": f"Internal server error: {str(exc)}"}), 500


@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """Update status or attributes of a catalog record."""
    data = request.get_json() or request.form
    if not data:
        return jsonify({"error": "No update payload provided"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": f"Book #{book_id} not found"}), 404

    title = data.get('title', existing['title']).strip()
    author = data.get('author', existing['author']).strip()
    category = data.get('category', existing['category']).strip()
    status = data.get('status', existing['status']).strip()

    if status not in ('Available', 'Checked Out', 'Reserved'):
        conn.close()
        return jsonify({"error": "Invalid status value"}), 400

    cursor.execute('''
        UPDATE books
        SET title = ?, author = ?, category = ?, status = ?
        WHERE id = ?
    ''', (title, author, category, status, book_id))
    conn.commit()
    conn.close()

    return jsonify({"message": f"Book #{book_id} updated successfully"}), 200


@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Remove a book from the catalog."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        return jsonify({"error": f"Book #{book_id} not found"}), 404
    return jsonify({"message": f"Book #{book_id} deleted successfully"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
