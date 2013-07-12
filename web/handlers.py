# -*- coding: utf-8 -*-

"""
    A real simple app for using webapp2 with auth and session.

    It just covers the basics. Creating a user, login, logout
    and a decorator for protecting certain handlers.

    Routes are setup in routes.py and added in main.py
"""
import json
import httpagentparser
from google.appengine.ext import ndb

from boilerplate.models import User
from boilerplate.handlers import RegisterBaseHandler
from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required

from web.models import Bom, Part

import logging as log

# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig





class HomeRequestHandler(RegisterBaseHandler):
    """
    Handler to show the home page
    """

    def get(self):
        """ Returns a simple HTML form for home """            
        params = {}
        return self.render_template('home.html', **params)



class ConvertBomHandler(BaseHandler):
    """
    Converts legacy lasersaur boms to bomfu.
    """
    def get(self):
        from web.bomfu_parser_legacy import get_new_from_legacy
        bom_file = get_new_from_legacy()
        params = {'raw': bom_file }
        return self.render_template('bom_raw_view.html', **params)

        # from bomfu_parser_legacy import get_new_from_legacy
        # import bomfu_parser

        # bom_file = get_new_from_legacy()
        # bom_by_subsystem = bomfu_parser.parse(bom_file)

        # # # calculate totals
        # # totals_by_subsystem = {}
        # # num_items_by_subsystem = {}
        # # for subsystem in bom_by_subsystem:
        # #     total = 0.0
        # #     num_items_by_subsystem[subsystem] = len(bom_by_subsystem[subsystem])
        # #     for part in bom_by_subsystem[subsystem]:
        # #         total += part[6]
        # #     totals_by_subsystem[subsystem] = total

        # params = {
        #     # "bom": bomfu_parser.parse(bom_old)
        #     "subsystems": ['frame-gantry','frame-table','frame-outer',
        #                   'frame-door','y-cart','y-drive', 'x-cart','x-drive','electronics',
        #                   'optics-laser','frame-panels','air-assist', 'extra'],
        #     "num_items_by_subsystem": 0,
        #     "totals_by_subsystem": 0,
        #     "bom": bomfu_parser.sort_by_subsystem(bom_by_subsystem, 'EUR'),
        #     # "bom_file": bom_file
        #     }
        # return self.render_template('convert_bom.html', **params)



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
