import pytest
from app import create_app, db
from app.models import Task


@pytest.fixture
def app():
    """Create application with in-memory test database."""
    test_app = create_app()
    test_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret',
    })
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_task(app):
    """Insert one task for read/update/delete tests."""
    with app.app_context():
        task = Task(title='Sample Task', description='A test task', priority='medium', status='todo')
        db.session.add(task)
        db.session.commit()
        return task.id  # return id so tests can query fresh


# ── CREATE ────────────────────────────────────────────────────────────────────

class TestCreate:
    def test_create_page_loads(self, client):
        response = client.get('/tasks/create')
        assert response.status_code == 200
        assert b'Create New Task' in response.data

    def test_create_valid_task(self, client):
        response = client.post('/tasks/create', data={
            'title': 'Buy groceries',
            'description': 'Milk, eggs, bread',
            'priority': 'low',
            'status': 'todo',
            'due_date': '',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Buy groceries' in response.data

    def test_create_missing_title(self, client):
        response = client.post('/tasks/create', data={
            'title': '',
            'priority': 'medium',
            'status': 'todo',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Title is required' in response.data

    def test_create_title_too_long(self, client):
        response = client.post('/tasks/create', data={
            'title': 'A' * 101,
            'priority': 'medium',
            'status': 'todo',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'100 characters' in response.data

    def test_create_invalid_priority(self, client):
        response = client.post('/tasks/create', data={
            'title': 'Test Task',
            'priority': 'urgent',
            'status': 'todo',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid priority' in response.data

    def test_create_invalid_status(self, client):
        response = client.post('/tasks/create', data={
            'title': 'Test Task',
            'priority': 'medium',
            'status': 'invalid',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid status' in response.data

    def test_create_invalid_due_date(self, client):
        response = client.post('/tasks/create', data={
            'title': 'Test Task',
            'priority': 'medium',
            'status': 'todo',
            'due_date': 'not-a-date',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Invalid due date' in response.data


# ── READ ──────────────────────────────────────────────────────────────────────

class TestRead:
    def test_index_loads(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_index_shows_task(self, client, sample_task):
        response = client.get('/')
        assert response.status_code == 200
        assert b'Sample Task' in response.data

    def test_view_existing_task(self, client, sample_task):
        response = client.get(f'/tasks/{sample_task}')
        assert response.status_code == 200
        assert b'Sample Task' in response.data
        assert b'Task Details' in response.data

    def test_view_nonexistent_task(self, client):
        response = client.get('/tasks/9999')
        assert response.status_code == 404

    def test_index_status_filter(self, client, sample_task):
        response = client.get('/?status=todo')
        assert response.status_code == 200
        assert b'Sample Task' in response.data

    def test_index_priority_filter(self, client, sample_task):
        response = client.get('/?priority=medium')
        assert response.status_code == 200
        assert b'Sample Task' in response.data


# ── UPDATE ────────────────────────────────────────────────────────────────────

class TestUpdate:
    def test_edit_page_loads(self, client, sample_task):
        response = client.get(f'/tasks/{sample_task}/edit')
        assert response.status_code == 200
        assert b'Edit Task' in response.data

    def test_edit_valid(self, client, sample_task):
        response = client.post(f'/tasks/{sample_task}/edit', data={
            'title': 'Updated Task',
            'description': 'Updated description',
            'priority': 'high',
            'status': 'in-progress',
            'due_date': '',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Updated Task' in response.data

    def test_edit_missing_title(self, client, sample_task):
        response = client.post(f'/tasks/{sample_task}/edit', data={
            'title': '',
            'priority': 'medium',
            'status': 'todo',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Title is required' in response.data

    def test_edit_nonexistent_task(self, client):
        response = client.post('/tasks/9999/edit', data={
            'title': 'X',
            'priority': 'low',
            'status': 'todo',
        })
        assert response.status_code == 404


# ── DELETE ────────────────────────────────────────────────────────────────────

class TestDelete:
    def test_delete_existing_task(self, client, sample_task):
        response = client.post(f'/tasks/{sample_task}/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'deleted successfully' in response.data

    def test_delete_nonexistent_task(self, client):
        response = client.post('/tasks/9999/delete')
        assert response.status_code == 404

    def test_deleted_task_not_found(self, client, sample_task):
        client.post(f'/tasks/{sample_task}/delete')
        response = client.get(f'/tasks/{sample_task}')
        assert response.status_code == 404


# ── SECURITY ──────────────────────────────────────────────────────────────────

class TestSecurityHeaders:
    """Verify HTTP security headers are present on every response."""

    def _check_headers(self, response):
        headers = response.headers
        assert headers.get('X-Content-Type-Options') == 'nosniff', \
            'X-Content-Type-Options header missing or wrong'
        assert headers.get('X-Frame-Options') == 'SAMEORIGIN', \
            'X-Frame-Options header missing or wrong'
        assert 'strict-origin-when-cross-origin' in headers.get('Referrer-Policy', ''), \
            'Referrer-Policy header missing or wrong'
        csp = headers.get('Content-Security-Policy', '')
        assert "default-src 'self'" in csp, 'CSP default-src missing'
        assert "frame-ancestors 'none'" in csp, 'CSP frame-ancestors missing'
        assert "form-action 'self'" in csp, 'CSP form-action missing'
        # Must NOT include unsafe-inline to prevent XSS
        assert "'unsafe-inline'" not in csp, 'CSP must not allow unsafe-inline'

    def test_index_security_headers(self, client):
        self._check_headers(client.get('/'))

    def test_create_page_security_headers(self, client):
        self._check_headers(client.get('/tasks/create'))

    def test_404_page_security_headers(self, client):
        response = client.get('/does-not-exist-at-all')
        assert response.status_code == 404
        self._check_headers(response)

    def test_404_returns_custom_page(self, client):
        response = client.get('/tasks/999999')
        assert response.status_code == 404
        # Must NOT leak a raw Flask/Werkzeug traceback
        assert b'Traceback' not in response.data
        assert b'werkzeug' not in response.data.lower()

    def test_delete_requires_post(self, client, sample_task):
        """DELETE endpoint must reject GET requests (method not allowed)."""
        response = client.get(f'/tasks/{sample_task}/delete')
        assert response.status_code == 405


class TestInputSanitization:
    """Verify that user-supplied content is escaped and not executed."""

    def test_xss_title_is_escaped(self, client, app):
        """A title containing an XSS payload must be HTML-escaped in responses."""
        xss_payload = '<script>alert("xss")</script>'
        client.post('/tasks/create', data={
            'title': xss_payload,
            'priority': 'medium',
            'status': 'todo',
        })
        response = client.get('/')
        assert b'<script>alert' not in response.data, \
            'Raw <script> tag found in index – Jinja2 auto-escaping not working'
        assert b'&lt;script&gt;' in response.data or xss_payload.encode() not in response.data

    def test_invalid_status_filter_ignored(self, client):
        """An invalid status query parameter must not cause a 500."""
        response = client.get('/?status=<evil>')
        assert response.status_code == 200

    def test_invalid_priority_filter_ignored(self, client):
        """An invalid priority query parameter must not cause a 500."""
        response = client.get('/?priority=\' OR 1=1--')
        assert response.status_code == 200

    def test_create_description_length_limit(self, client):
        """Description beyond 1000 chars must be rejected."""
        response = client.post('/tasks/create', data={
            'title': 'Long Desc Task',
            'description': 'x' * 1001,
            'priority': 'medium',
            'status': 'todo',
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'1000 characters' in response.data


class TestCSRFIntegration:
    """Verify CSRF protection is configured but disabled correctly for tests."""

    def test_csrf_token_present_in_create_form(self, client):
        """The create form HTML must contain a csrf_token field."""
        response = client.get('/tasks/create')
        assert b'csrf_token' in response.data, \
            'Create form is missing CSRF token input'

    def test_csrf_token_present_in_edit_form(self, client, sample_task):
        """The edit form HTML must contain a csrf_token field."""
        response = client.get(f'/tasks/{sample_task}/edit')
        assert b'csrf_token' in response.data, \
            'Edit form is missing CSRF token input'
