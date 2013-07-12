# -*- coding: utf-8 -*-

""" Bom edit handling."""

import json
import time
import logging as log
from google.appengine.ext import ndb

from boilerplate.models import User
from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required

from web.models import Bom, Part, AuthWriterError


# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig



def parse_and_add(bomfu, bom_id, user_id, part_ids=[]):
    """Parse a bomfu string and add Parts.

    If part_ids are specified only these parts are edited in place
    with any bomfu data. Parsing is limited to len(part_ids).

    Returns: error string on error, otherwise None
    """
    import bomfu_parser
    try:
        if part_ids:
            # limit parsing to how many part_ids we got
            bom_json = bomfu_parser.parse(bomfu, len(part_ids))
        else:
            bom_json = bomfu_parser.parse(bomfu)
    except bomfu_parser.ParseError as ex:
        return str(ex)
    i = 0
    for p in bom_json:
        if part_ids:
            if i >= len(part_ids):
                return "Parse error, got more part data than part_ids."
            # edit part
            part = ndb.Key('Bom', long(bom_id), 'Part', long(part_ids[i])).get()
            i += 1
        else:
            # add part
            part = Part.new(ndb.Key('Bom', long(bom_id)), '')

        if part:
            part.name = p[0]
            part.quantity_units = p[1]
            part.part_group = p[2]
            part.note_list = p[3]
            part.designator_list = p[4]
            part.manufacturer_names = []
            part.manufacturer_partnums = []
            for manu in p[5]:
                part.manufacturer_names.append(manu[0])
                part.manufacturer_partnums.append(manu[1])
            part.supplier_names = []
            part.supplier_ordernums = []
            part.supplier_packagecounts = []
            part.supplier_currencies = []
            part.supplier_countries = []
            part.supplier_prices = []
            part.supplier_urls = []
            for supplier in p[6]:
                part.supplier_names.append(supplier[0])
                part.supplier_ordernums.append(supplier[1])
                part.supplier_packagecounts.append(supplier[2])
                part.supplier_currencies.append(supplier[3])
                part.supplier_countries.append(supplier[4])
                part.supplier_prices.append(supplier[5])
                part.supplier_urls.append(supplier[6])
            part.subsystem_quantities = []
            part.subsystem_names = []
            part.subsystem_specificuses = []
            for subsys in p[7]:
                part.subsystem_quantities.append(subsys[0])
                part.subsystem_names.append(subsys[1])
                part.subsystem_specificuses.append(subsys[2])
            part.put(user_id)
        else:
            return "Failed to instance part."



class BomCreate(BaseHandler):
    """Creates new BOM."""

    @user_required
    def get(self):
        bom = Bom.new('newbom')
        bom.name = 'bom-' + bom.public_id
        bom.put(self.user_id, makeowner=True)
        time.sleep(0.6)  # give db some time to write
        self.add_message("New BOM created!", 'success')
        return self.redirect_to('bom-edit', public_id=bom.public_id)



class BomImport(BaseHandler):
    """Handler to import BOM from .bomfu file."""

    @user_required
    def get(self):
        params = {}
        return self.render_template('bom_import.html', **params)

    @user_required
    def post(self):
        bomfu = self.request.get('bomfu')
        if bomfu:
            self.response.headers.add_header('content-type', 'application/json', 
                                             charset='utf-8')
            bom = Bom.new('newbom')
            bom.name = 'bom-imported-' + bom.public_id
            bom.put(self.user_id, makeowner=True)
            ret = parse_and_add(bomfu, bom.key.id(), self.user_id)
            if ret:  # fail
                bom.key.delete()  # FIXME: refactor parse_and_add
                self.response.out.write(json.dumps({"error":ret})) 
            else:    # ok
                self.response.out.write('{"error":false, "public_id":"'+bom.public_id+'"}')
            # self.redirect(self.uri_for('bom-edit', public_id=bom.public_id))
        else:
            self.abort(501)



class BomDelete(BaseHandler):
    """Delete a BOM."""

    @user_required
    def get(self, bom_id):
        # TODO:
        #   check user
        bom = Bom.get_by_id(long(bom_id))
        if bom:
            bom.delete()
            time.sleep(0.5)  # give db some time to write
            self.add_message('BOM deleted!', 'success')
            self.redirect(self.uri_for('boms'))
        else:
            self.abort(404)


class BomEditView(BaseHandler):
    """Show BOM, allow editing."""

    @user_required
    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            parts = Part.query(ancestor=bom.key).order(-Part.create_time).fetch()
            rawparts = []
            for part in parts:
                raw = []
                quantity_units = ''
                if part.quantity_units:
                    quantity_units = ', units='+part.quantity_units
                raw.append(part.name+quantity_units+'   '+part.part_group+'\n')
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
            # prime form
            # self.form.process(obj=bom)
            return self.render_template('bom_edit.html', **params)
        else:
            self.abort(404)



class BomEditFields(BaseHandler):

    @user_required
    def post(self, bom_id):
        name = self.request.get('name')
        public = self.request.get('public')
        bom = Bom.get_by_id(long(bom_id))
        if bom:
            self.response.headers.add_header('content-type', 'application/json', 
                                             charset='utf-8')
            ret = 'false'
            if name:
                bom.name = name
            if public:
                if public == 'true':
                    bom.public = True
                elif public == 'false':
                    bom.public = False
            if name or public:
                try:
                    bom.put(self.user_id)
                except AuthWriterError as ex:
                    ret = str(ex)
            self.response.out.write('{"error":'+ret+'}')
        else:
            self.abort(404)



class PartEdit(BaseHandler):
    """Handle part edits, adds when part_id == null."""

    @user_required
    def post(self, bom_id, part_id):
        """handle edit and delete requests."""
        self.response.headers.add_header('content-type', 'application/json', 
                                         charset='utf-8')
        bomfu = self.request.get('bomfu')
        if bomfu:
            if part_id == 'null':
                # new part
                ret = parse_and_add(bomfu, bom_id, self.user_id)
            else:
                ret = parse_and_add(bomfu, bom_id, self.user_id, [part_id])
            if ret:
                self.response.out.write(json.dumps({"error":ret})) 
            else:
                self.response.out.write('{"error":false}')
        else:
            self.abort(501)



class PartDelete(BaseHandler):
    """Handle part deletes."""

    @user_required
    def post(self, bom_id, part_id):
        self.response.headers.add_header('content-type', 'application/json', 
                                         charset='utf-8')
        # delete part
        part = ndb.Key('Bom', long(bom_id), 'Part', long(part_id)).get()
        if part:
            part.delete()
            self.response.out.write('{"error":false}') 
        else:
            self.abort(404)
