# -*- coding: utf-8 -*-

"""
    A real simple app for using webapp2 with auth and session.

    It just covers the basics. Creating a user, login, logout
    and a decorator for protecting certain handlers.

    Routes are setup in routes.py and added in main.py
"""
import json
import httpagentparser
from boilerplate.models import User
from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required

from web.models import Bom



class BomCreateHandler(BaseHandler):
    """Handler to create new BOMs."""

    def get(self):
        params = {
            # "bom_id" : bom_id
            }
        return self.render_template('bom_create.html', **params)



class BomImportHandler(BaseHandler):
    """Handler to import BOM from .bomfu file."""

    def get(self):
        params = {
            # "bom_id" : bom_id
            }
        return self.render_template('bom_import.html', **params)


    def post(self):
        new_bom = Bom.new()
        new_bom.name = "aBom-" + str(new_bom.public_id)
        new_bom.put()
        self.redirect(new_bom.get_url())
        self.redirect(self.uri_for('bom_build', public_id=new_bom.public_id))


class BomsHandler(BaseHandler):
    """Show all BOMs."""

    def get(self):
        params = {
            # "bom_id" : bom_id
            }
        return self.render_template('bom_import.html', **params)



class BomBuildViewHandler(BaseHandler):
    """
    Handler for public BOMs in build view, by subsystem.
    """


    def get(self, public_id):
        import lasersaur_bomfu_old
        import bomfu_parser

        currency = 'EUR'
        bomfu_json_old = bomfu_parser.bomfu_to_json_old(lasersaur_bomfu_old.bom)
        by_subsystem_json = bomfu_parser.sort_by_subsystem(bomfu_json_old, currency)
        bomfu_json = bomfu_parser.convert_old_to_new(bomfu_json_old)

        # calculate totals
        totals_by_subsystem = {}
        num_items_by_subsystem = {}
        for subsystem in by_subsystem_json:
            total = 0.0
            num_items_by_subsystem[subsystem] = len(by_subsystem_json[subsystem])
            for part in by_subsystem_json[subsystem]:
                total += part[6]
            totals_by_subsystem[subsystem] = total

        params = {
            "public_id" : public_id,
            # "bom_json" : json.dumps(by_subsystem_json, indent=2, sort_keys=True)
            "currency": currency,
            "bom_old" : by_subsystem_json,
            "subsystems": ['frame-gantry','frame-table','frame-outer',
                          'frame-door','y-cart','y-drive', 'x-cart','x-drive','electronics',
                          'optics-laser','frame-panels','air-assist', 'extraction', 'extra'],
            "num_items_by_subsystem": num_items_by_subsystem,
            "totals_by_subsystem": totals_by_subsystem,
            "bom": bomfu_json
            }
        return self.render_template('bom_build_view.html', **params)


class BomOrderViewHandler(BaseHandler):
    """
    Handler for public BOMs in order view, by supplier.
    """

    def get(self, public_id):
        params = {
            "public_id" : public_id
            }
        return self.render_template('bom_order_view.html', **params)



class ConvertBomHandler(BaseHandler):
    """
    Converts legacy lasersaur boms to bomfu.
    """
    def get(self):
        from bomfu_parser_legacy import get_new_from_legacy
        import bomfu_parser

        bom_file = get_new_from_legacy()
        bom_by_subsystem = bomfu_parser.parse(bom_file)

        # # calculate totals
        # totals_by_subsystem = {}
        # num_items_by_subsystem = {}
        # for subsystem in bom_by_subsystem:
        #     total = 0.0
        #     num_items_by_subsystem[subsystem] = len(bom_by_subsystem[subsystem])
        #     for part in bom_by_subsystem[subsystem]:
        #         total += part[6]
        #     totals_by_subsystem[subsystem] = total

        params = {
            # "bom": bomfu_parser.parse(bom_old)
            "subsystems": ['frame-gantry','frame-table','frame-outer',
                          'frame-door','y-cart','y-drive', 'x-cart','x-drive','electronics',
                          'optics-laser','frame-panels','air-assist', 'extra'],
            "num_items_by_subsystem": 0,
            "totals_by_subsystem": 0,
            "bom": bomfu_parser.sort_by_subsystem(bom_by_subsystem, 'EUR'),
            # "bom_file": bom_file
            }
        return self.render_template('convert_bom.html', **params)



class SecureRequestHandler(BaseHandler):
    """
    Only accessible to users that are logged in
    """

    @user_required
    def get(self, **kwargs):
        user_session = self.user
        user_session_object = self.auth.store.get_session(self.request)

        user_info = User.get_by_id(long( self.user_id ))
        user_info_object = self.auth.store.user_model.get_by_auth_token(
            user_session['user_id'], user_session['token'])

        try:
            params = {
                "user_session" : user_session,
                "user_session_object" : user_session_object,
                "user_info" : user_info,
                "user_info_object" : user_info_object,
                "userinfo_logout-url" : self.auth_config['logout_url'],
                }
            return self.render_template('secure_zone.html', **params)
        except (AttributeError, KeyError), e:
            return "Secure zone error:" + " %s." % e



class TestAllUIHandler(BaseHandler):
    """
    Handler for testing all bootstrap UI widgets.
    """

    def get(self):
        params = {}
        return self.render_template('test_all_ui.html', **params)
