from app import create_app, db
from app.models import Agent, IssuedToken, TaskAuditLog

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Agent': Agent,
        'IssuedToken': IssuedToken,
        'TaskAuditLog': TaskAuditLog
    }

@app.route('/')
def index():
    return """
    <h1>AgenticTrust OAuth Server</h1>
    <p>API endpoints available at /api/</p>
    <p>Admin dashboard at <a href="/api/admin/dashboard">/api/admin/dashboard</a></p>
    """

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 