from app import create_app, db
from app.models import Agent, IssuedToken, TaskAuditLog
import os

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Agent': Agent,
        'IssuedToken': IssuedToken,
        'TaskAuditLog': TaskAuditLog
    }

@app.route('/api/routes', methods=['GET'])
def list_routes():
    """List all registered routes with their endpoints and methods."""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        routes.append({
            'endpoint': str(rule.endpoint),
            'methods': methods,
            'path': str(rule),
            'is_api': str(rule).startswith('/api')
        })
    
    # Sort routes by path
    routes = sorted(routes, key=lambda x: x['path'])
    
    # Group by base path for better organization
    grouped_routes = {}
    for route in routes:
        parts = route['path'].split('/')
        if len(parts) > 1:
            base = f"/{parts[1]}"
            if base not in grouped_routes:
                grouped_routes[base] = []
            grouped_routes[base].append(route)
    
    return {
        'routes': routes,
        'grouped_routes': grouped_routes,
        'total': len(routes)
    }

if __name__ == '__main__':
    # Try loading host and port from config, fall back to defaults
    host = app.config.get('HOST', '127.0.0.1')
    port = app.config.get('PORT', 5001)
    debug = app.config.get('DEBUG', True)
    
    # Allow overriding via environment variables
    host = os.environ.get('FLASK_HOST', host)
    port = int(os.environ.get('FLASK_PORT', port))
    
    with app.app_context():
        db.create_all()
    
    print(f"Server running at http://{host}:{port}")
    print(f"API Routes available at http://{host}:{port}/api/routes")
    app.run(host=host, port=port, debug=debug) 