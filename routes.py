"""
Using redirect route instead of simple routes since it supports strict_slash
Simple route: http://webapp-improved.appspot.com/guide/routing.html#simple-routes
RedirectRoute: http://webapp-improved.appspot.com/api/webapp2_extras/routes.html#webapp2_extras.routes.RedirectRoute
"""

from webapp2_extras.routes import RedirectRoute
from web import handlers
from web.boms import BomsHandler
from web.bom_edit import BomEditView, BomEditFields, PartEdit, PartDelete

secure_scheme = 'https'

_routes = [
    RedirectRoute('/create', handlers.BomCreateHandler, name='bom_create', strict_slash=True),
    RedirectRoute('/import', handlers.BomImportHandler, name='bom_import', strict_slash=True),
    # bom views
    RedirectRoute('/b', BomsHandler, name='boms', strict_slash=True),
    RedirectRoute('/b/<public_id>', handlers.BomBuildHandler, name='bom-build', strict_slash=True),
    RedirectRoute('/b/<public_id>/order/<currency>', handlers.BomOrderHandler, name='bom-order', strict_slash=True),
    RedirectRoute('/b/<public_id>/raw', handlers.BomRawHandler, name='bom-raw', strict_slash=True),
    RedirectRoute('/b/<public_id>/edit', BomEditView, name='bom-edit-view', strict_slash=True),
    # bom editing
    RedirectRoute('/b/<bom_id>/editfields', BomEditFields, name='bom-edit-fields', strict_slash=True),
    RedirectRoute('/p/<bom_id>/edit/<part_id>', PartEdit, name='part-edit', strict_slash=True),
    RedirectRoute('/p/<bom_id>/delete/<part_id>', PartDelete, name='part-delete', strict_slash=True),
    # stuff
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