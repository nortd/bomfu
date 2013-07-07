from webapp2_extras.routes import RedirectRoute
from webapp2_extras.routes import PathPrefixRoute
import users
import boms


_routes = [
    PathPrefixRoute('/admin', [
        RedirectRoute('/logout/', users.Logout, name='admin-logout', strict_slash=True),
        RedirectRoute('/geochart/', users.Geochart, name='geochart', strict_slash=True),
        RedirectRoute('/users/', users.List, name='user-list', strict_slash=True),
        RedirectRoute('/users/<user_id>/', users.Edit, name='user-edit', strict_slash=True, handler_method='edit'),
        RedirectRoute('/bom/', boms.List, name='boms-admin', strict_slash=True),
        RedirectRoute('/bom/edit/<bom_id>', boms.Edit, name='bom-admin-edit', strict_slash=True, handler_method='edit'),
        RedirectRoute('/bom/delete/<bom_id>', boms.Delete, name='bom-admin-delete', strict_slash=True)
    ])
]

def get_routes():
    return _routes

def add_routes(app):
    for r in _routes:
        app.router.add(r)
