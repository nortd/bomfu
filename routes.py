"""
Using redirect route instead of simple routes since it supports strict_slash
Simple route: http://webapp-improved.appspot.com/guide/routing.html#simple-routes
RedirectRoute: http://webapp-improved.appspot.com/api/webapp2_extras/routes.html#webapp2_extras.routes.RedirectRoute
"""

from webapp2_extras.routes import RedirectRoute
from web import handlers
from web.boms import BomsHandler

secure_scheme = 'https'

_routes = [
    RedirectRoute('/create', handlers.BomCreateHandler, name='bom_create', strict_slash=True),
    RedirectRoute('/import', handlers.BomImportHandler, name='bom_import', strict_slash=True),
    RedirectRoute('/bom', BomsHandler, name='boms', strict_slash=True),
    RedirectRoute('/bom/<bom_id>', handlers.BomBuildViewHandler, name='bom_build', strict_slash=True),
    RedirectRoute('/bom/<bom_id>/order', handlers.BomOrderViewHandler, name='bom_order', strict_slash=True),
    RedirectRoute('/secure/', handlers.SecureRequestHandler, name='secure', strict_slash=True),
    RedirectRoute('/_convert_bom', handlers.ConvertBomHandler, name='convert_bom', strict_slash=True),
    RedirectRoute('/_test_all_ui', handlers.TestAllUIHandler, name='test_all_ui', strict_slash=True),
]

def get_routes():
    return _routes

def add_routes(app):
    if app.debug:
        secure_scheme = 'http'
    for r in _routes:
        app.router.add(r)