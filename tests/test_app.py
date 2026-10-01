import json
import pytest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app


@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client


def test_health_check(client):
    """Verify the /health probe returns HTTP 200 and UP status."""
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'UP'
    assert data['database'] == 'connected'


def test_index_page(client):
    """Verify the root UI page loads successfully."""
    res = client.get('/')
    assert res.status_code == 200
    assert b"Digital Library Portal" in res.data


def test_dashboard_stats(client):
    """Verify aggregated dashboard metrics."""
    res = client.get('/api/dashboard/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert 'total' in data
    assert 'available' in data
    assert 'checked_out' in data
    assert 'categories' in data
    assert 'authors' in data


def test_list_and_search_books(client):
    """Verify listing books and query filtering."""
    # List all
    res = client.get('/api/books')
    assert res.status_code == 200
    data = res.get_json()
    assert data['count'] >= 1

    # Search keyword
    res_search = client.get('/api/books?q=DevOps')
    assert res_search.status_code == 200
    search_data = res_search.get_json()
    assert search_data['count'] >= 1


def test_create_book_validation(client):
    """Verify validation when creating new books."""
    # Missing required field
    res_missing = client.post('/api/books', json={'title': 'Incomplete'})
    assert res_missing.status_code == 400

    # Invalid ISBN
    res_bad_isbn = client.post('/api/books', json={
        'title': 'Bad ISBN Book',
        'author': 'Tester',
        'isbn': '999'
    })
    assert res_bad_isbn.status_code == 400

    # Successful creation
    unique_isbn = "978-9999999991"
    res_ok = client.post('/api/books', json={
        'title': 'CI/CD Pipeline Design Patterns',
        'author': 'Jenkins Automation Agent',
        'isbn': unique_isbn,
        'category': 'DevOps',
        'status': 'Available'
    })
    assert res_ok.status_code == 201
    new_id = res_ok.get_json()['id']

    # Duplicate ISBN
    res_dup = client.post('/api/books', json={
        'title': 'Duplicate Book',
        'author': 'Tester',
        'isbn': unique_isbn
    })
    assert res_dup.status_code == 409

    # Clean up created book
    res_del = client.delete(f'/api/books/{new_id}')
    assert res_del.status_code == 200
