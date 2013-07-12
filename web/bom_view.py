# -*- coding: utf-8 -*-

"""Handling of BOM views."""

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





class BomBuildHandler(BaseHandler):
    """Show BOM by subsystem."""

    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            raw = []
            for subsys, parts in bom.get_parts_by_subsystem().iteritems():
                raw.append(subsys + '\n')
                for part in parts:
                    raw.append('   '+ part.name + '\n')

            params['raw'] = ''.join(raw)
            return self.render_template('bom_build.html', **params)
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
            for supplier, parts in bom.get_parts_by_supplier(currency).iteritems():
                raw.append(supplier + '\n')
                for part in parts:
                    raw.append('   '+ part.name + '\n')

            params['raw'] = ''.join(raw)
            return self.render_template('bom_order.html', **params)
        else:
            self.abort(404)



class BomRawHandler(BaseHandler):
    """Show BOM as in file format."""
    def get(self, public_id):
        params = {}
        bom = Bom.query(Bom.public_id == public_id).get()
        if bom:
            parts = Part.query(ancestor=bom.key).order(Part.name).fetch()
            raw = []
            for part in parts:
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
                raw.append('\n')
            params['raw'] = ''.join(raw)
            return self.render_template('bom_raw.html', **params)
        else:
            self.abort(404)

