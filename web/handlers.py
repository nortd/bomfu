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
from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required

from web.models import Bom, Part

import logging as log

# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig



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
        self.redirect(self.uri_for('bom-build', public_id=new_bom.public_id))


class BomsHandler(BaseHandler):
    """Show all BOMs."""

    def get(self):
        params = {
            # "bom_id" : bom_id
            }
        return self.render_template('bom_import.html', **params)



class BomBuildHandler(BaseHandler):
    """Show BOM by subsystem."""
    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            raw = []
            for part_by_subsys in bom.get_parts_by_subsystem():
                subsys = part_by_subsys[0]
                raw.append(subsys + '\n')
                for part in part_by_subsys[1]:
                    raw.append('   '+ part.name + '\n')

            params['raw'] = ''.join(raw)
            return self.render_template('bom_raw.html', **params)
            # return self.render_template('bom_build.html', **params)
        else:
            self.abort(404)

        # import lasersaur_bomfu_old
        # import bomfu_parser

        # currency = 'EUR'
        # bomfu_json_old = bomfu_parser.bomfu_to_json_old(lasersaur_bomfu_old.bom)
        # by_subsystem_json = bomfu_parser.sort_by_subsystem(bomfu_json_old, currency)
        # bomfu_json = bomfu_parser.convert_old_to_new(bomfu_json_old)

        # # calculate totals
        # totals_by_subsystem = {}
        # num_items_by_subsystem = {}
        # for subsystem in by_subsystem_json:
        #     total = 0.0
        #     num_items_by_subsystem[subsystem] = len(by_subsystem_json[subsystem])
        #     for part in by_subsystem_json[subsystem]:
        #         total += part[6]
        #     totals_by_subsystem[subsystem] = total

        # params = {
        #     "public_id" : public_id,
        #     # "bom_json" : json.dumps(by_subsystem_json, indent=2, sort_keys=True)
        #     "currency": currency,
        #     "bom_old" : by_subsystem_json,
        #     "subsystems": ['frame-gantry','frame-table','frame-outer',
        #                   'frame-door','y-cart','y-drive', 'x-cart','x-drive','electronics',
        #                   'optics-laser','frame-panels','air-assist', 'extraction', 'extra'],
        #     "num_items_by_subsystem": num_items_by_subsystem,
        #     "totals_by_subsystem": totals_by_subsystem,
        #     "bom": bomfu_json
        #     }
        # return self.render_template('bom_build.html', **params)




class BomOrderHandler(BaseHandler):
    """Show BOM by Supplier."""

    def get(self, public_id, currency):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            raw = []
            for part_by_supplier in bom.get_parts_by_supplier(currency):
                supplier = part_by_supplier[0]
                raw.append(supplier + '\n')
                for part in part_by_supplier[1]:
                    raw.append('   '+ part.name + '\n')

            params['raw'] = ''.join(raw)
            return self.render_template('bom_raw.html', **params)
            # return self.render_template('bom_order.html', **params)
        else:
            self.abort(404)



class BomEditHandler(BaseHandler):
    """Show BOM by PartGroup, allow editing."""
    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            parts = Part.query(ancestor=bom.key).order(Part.name).fetch()
            rawparts = []
            for part in parts:
                raw = []
                raw.append(part.name+'   '+part.quantity_units+'   '+part.part_group+'\n')
                for note in part.note_list:
                    raw.append('   * '+note+'\n')
                for designator in part.designator_list:
                    raw.append('   # '+designator+'\n')
                for i in range(len(part.manufacturer_names)):
                    raw.append('   @ '+part.manufacturer_names[i]+
                               '   '+part.manufacturer_partnums[i]+
                               '\n')
                for i in range(len(part.supplier_names)):
                    raw.append('   $ '+part.supplier_names[i]+
                               '   '+part.supplier_ordernums[i])
                    package_count = part.supplier_packagecounts[i]
                    if package_count != 1:
                        if (package_count % 1) == 0:
                            package_count = '%0.0f' % package_count
                        else:
                            package_count = '%0.3f' % package_count
                        raw.append('   '+package_count)
                    raw.append('   '+part.supplier_currencies[i])
                    if part.supplier_countries[i]:
                        raw.append('   '+part.supplier_currencies[i])
                    raw.append(' %0.2f' % part.supplier_prices[i])
                    if part.supplier_urls[i]:
                        raw.append('   '+part.supplier_urls[i])                    
                    raw.append('\n')
                for i in range(len(part.subsystem_names)):
                    quantities = part.subsystem_quantities[i]
                    if (quantities % 1) == 0:
                        quantities = '%0.0f' % quantities
                    else:
                        quantities = '%0.2f' % quantities
                    raw.append('   '+quantities+
                               '   '+part.subsystem_names[i]+
                               '   '+part.subsystem_specificuses[i]+
                               '\n')
                rawparts.append({'id':part.key.id(), 'raw':''.join(raw)[:-1]})
            params['rawparts'] = rawparts
            params['bom'] = bom
            return self.render_template('bom_edit.html', **params)
        else:
            self.abort(404)

    def post(self, public_id):
        """handle edit and delete requests."""
        bom_id = self.request.get('bom_id')  # part to edit
        edit_p = self.request.get('edit_p')  # part to edit
        del_p = self.request.get('del_p')  # part to delete
        if edit_p and bom_id:
            # edit part
            # part = Part.get_by_id(edit_p)
            part = ndb.Key('Bom', long(bom_id), 'Part', long(edit_p)).get()
            if part:
                log.info("got an edit request")
                self.abort(501)
            else:
                self.abort(404)
        elif del_p and bom_id:
            # delete part
            part = ndb.Key('Bom', long(bom_id), 'Part', long(del_p)).get()
            if part:
                part.delete()
                return '__ok__'
            else:
                self.abort(404)
        else:
            self.abort(501)



class BomRawHandler(BaseHandler):
    """Show BOM as in file format."""
    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            parts = Part.query(ancestor=bom.key).order(Part.name).fetch()
            raw = []
            for part in parts:
                raw.append(part.name+'   '+part.quantity_units+'   '+part.part_group+'\n')
                for note in part.note_list:
                    raw.append('   * '+note+'\n')
                for designator in part.designator_list:
                    raw.append('   # '+designator+'\n')
                for i in range(len(part.manufacturer_names)):
                    raw.append('   @ '+part.manufacturer_names[i]+
                               '   '+part.manufacturer_partnums[i]+
                               '\n')
                for i in range(len(part.supplier_names)):
                    raw.append('   $ '+part.supplier_names[i]+
                               '   '+part.supplier_ordernums[i])
                    package_count = part.supplier_packagecounts[i]
                    if package_count != 1:
                        if (package_count % 1) == 0:
                            package_count = '%0.0f' % package_count
                        else:
                            package_count = '%0.3f' % package_count
                        raw.append('   '+package_count)
                    raw.append('   '+part.supplier_currencies[i])
                    if part.supplier_countries[i]:
                        raw.append('   '+part.supplier_currencies[i])
                    raw.append(' %0.2f' % part.supplier_prices[i])
                    if part.supplier_urls[i]:
                        raw.append('   '+part.supplier_urls[i])                    
                    raw.append('\n')
                for i in range(len(part.subsystem_names)):
                    quantities = part.subsystem_quantities[i]
                    if (quantities % 1) == 0:
                        quantities = '%0.0f' % quantities
                    else:
                        quantities = '%0.2f' % quantities
                    raw.append('   '+quantities+
                               '   '+part.subsystem_names[i]+
                               '   '+part.subsystem_specificuses[i]+
                               '\n')
                raw.append('\n')
            params['raw'] = ''.join(raw)
            return self.render_template('bom_raw.html', **params)
        else:
            self.abort(404)




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
