# -*- coding: utf-8 -*-

""" Bom edit handling."""

import json
import logging as log
from google.appengine.ext import ndb

from boilerplate.models import User
from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required

from web.models import Bom, Part


import webapp2
from wtforms import fields
from wtforms import Form
from wtforms import validators
from boilerplate.forms import BaseForm

FIELD_MAXLENGTH = 50 # intended to stop maliciously long input

# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig



class EditBomForm(BaseForm):
    name = fields.TextField('Name', [validators.required(), validators.Length(max=FIELD_MAXLENGTH)])
    public = fields.BooleanField('Public', [validators.required()])


class BomEditView(BaseHandler):
    """Show BOM by PartGroup, allow editing."""
    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            parts = Part.query(ancestor=bom.key).order(Part.create_time).fetch()
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
            self.form.process(obj=bom)
            return self.render_template('bom_edit.html', **params)
        else:
            self.abort(404)


    @webapp2.cached_property
    def form(self):
        return EditBomForm(self)



class BomEditFields(BaseHandler):
    def post(self, bom_id):
        pass



class PartAdd(BaseHandler):
    """Handle part additions."""
    def post(self, bom_id):
        pass



class PartEdit(BaseHandler):
    """Handle part edits."""
    def post(self, bom_id, part_id):
        """handle edit and delete requests."""
        self.response.headers.add_header('content-type', 'application/json', 
                                         charset='utf-8')
        bomfu = self.request.get('bomfu')
        if bomfu:
            # part = Part.get_by_id(edit_p)
            part = ndb.Key('Bom', long(bom_id), 'Part', long(part_id)).get()
            if part:
                # log.info(bomfu)
                import bomfu_parser
                try:
                    bom_json = bomfu_parser.parse(bomfu, 1)
                except bomfu_parser.ParseError as ex:
                    ret = {"error":str(ex)}
                    self.response.out.write(json.dumps(ret)) 
                    return
                if len(bom_json) == 1:
                    p = bom_json[0]
                    # write to part
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
                    part.put()
                    self.response.out.write('{"error":false}') 
                else:
                    ret = {"error":"Failed to parse bomfu data: %s" % bomfu}
                    self.response.out.write(json.dumps(ret)) 
            else:
                self.abort(404)
        else:
            self.abort(501)



class PartDelete(BaseHandler):
    """Handle part deletes."""
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
