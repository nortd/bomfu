# -*- coding: utf-8 -*-

"""
    A real simple app for using webapp2 with auth and session.

    It just covers the basics. Creating a user, login, logout
    and a decorator for protecting certain handlers.

    Routes are setup in routes.py and added in main.py
"""
import httpagentparser
from boilerplate import models
from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required


class SecureRequestHandler(BaseHandler):
    """
    Only accessible to users that are logged in
    """

    @user_required
    def get(self, **kwargs):
        user_session = self.user
        user_session_object = self.auth.store.get_session(self.request)

        user_info = models.User.get_by_id(long( self.user_id ))
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


class BomBuildViewHandler(BaseHandler):
    """
    Handler for public BOMs in build view, by subsystem.
    """


    def get(self, bom_id):
        import lasersaur_bomfu
        import bomfu_parser
        # print lasersaur_bomfu.bom
        params = {
            "bom_id" : bom_id,
            "bom_json" : bomfu_parser.bomfu_to_json(lasersaur_bomfu.bom)
            }
        return self.render_template('bom_build_view.html', **params)


class BomOrderViewHandler(BaseHandler):
    """
    Handler for public BOMs in order view, by supplier.
    """

    def get(self, bom_id):
        params = {
            "bom_id" : bom_id
            }
        return self.render_template('bom_order_view.html', **params)
