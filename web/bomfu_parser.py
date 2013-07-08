""" BOMfu file Parser

The Bomfu file format is optimized for human editing and parses easily.
The file lists two types: supplier definitions, parts

Supplier definitions ...

Part entries ...
consist of one "master" line and five kinds of auxilliary lines.
The master line lists part name, quantity_units (optional), 
and part_group (optional). Then for each kind of auxilliary line there
can be zero or more entries. The kinds are:
       notes, designators, manufacturers, suppliers, usages

Part Example:

part_name[, units=mm]  [part_group]
   [* notes]
   [# designators]
   [@ manufacturer_name, part_num]
   [$ supplier_name   order_num[##package_count]   currency[-country] amount   [explicit_url] ]
   [quantity   subsystem   specific_use]

The parser outputs to an intermediary json format. By default this output
format lists parts the same way as the imput file.
"""

import re
import json
import logging as log
from pprint import pprint


# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig


def parse(bomstring):
    """
    Reads:

    part_name[, units=mm]  [part_group]
       [* notes]
       [# designators]
       [@ manufacturer_name, part_num]
       [$ supplier_name   order_num[##package_count]   currency[-country] amount   [explicit_url] ]
       [quantity   subsystem   specific_use]

    Returns:

    [
      [ part_name, quantity_units, part_group,
        [ note,
          ...
        ],
        [ designator,
          ...
        ],
        [ [manufacturer, part_num],
          ...
        ],
        [ [supplier_name, order_num, package_count, currency, country, amount, explicit_url], 
          [another supplier],
            ...
        ],
        [ [quantity, subsystem, specific use],
          [another usage],
            ...
        ]
      ],
      [ another part ],
        ...
    ]
    """
    lines = bomstring.split('\n')

    stats_num_items = {'USD':0, 'EUR':0}
    # first parse supplierdefs
    # !supplierdef   supplier   currency[-country] url_pattern   [currency url_pattern]   ...
    supplierdefs = {};  # {supplier: {currency:url, ...}, ...}
    for line in lines:
        if line[:12] == "!supplierdef":
            def_parts = line.split("   ")
            supplier_name = def_parts[1].strip()
            supplierdefs[supplier_name] = {}
            for l in range(2,len(def_parts)):
                loc_pair = def_parts[l].split(" ");
                location = loc_pair[0].strip()
                url_pattern = loc_pair[1].strip()
                supplierdefs[supplier_name][location] = url_pattern;
    # pprint(supplierdefs)

    # then parse parts lines
    # which consist out of a master line and one or more auxilliary lines
    parts = [];  # list of [name, quantity_units, group, notes, designators, manufacturers suppliers, usages]
    part_entry_notes = None
    part_entry_designators = None
    part_entry_manufacturers = None
    part_entry_suppliers = None
    part_entry_usages = None
    for line in lines:
        if line and line[0] != '#' and line[0] != '!':
            if line[:3] == '   ':  # auxilliary line
                auxline = line[3:].strip()
                if auxline[0] == '*':  # note line
                    note = auxline.strip()[1:].strip()
                    part_entry_notes.append(note)
                elif auxline[0] == '#':  # designator line
                    designator = auxline.strip()[1:].strip()
                    part_entry_designators.append(designator)
                elif auxline[0] == '@':  # manufacturer line
                    manu_parts = auxline.split('   ')
                    if len(manu_parts) == 2:
                        manufacturer = manu_parts[0].strip()[1:].strip()
                        part_num = manu_parts[1].strip()
                        part_entry_manufacturers.append([manufacturer, part_num])
                    else:
                        log.error("invalid manufacturer line")
                        break
                elif auxline[0] == '$':  # supplier line
                    # @ supplier_name   order_num[##package_count]   currency[-country] amount   [explicit_url]
                    supplier_parts = auxline.split('   ')
                    if len(supplier_parts) == 3 or len(supplier_parts) == 4:
                        supplier = supplier_parts[0].strip()[1:].strip()
                        order_num = supplier_parts[1].strip()
                        pricing = supplier_parts[2].strip()
                        explicit_url = ''
                        if len(supplier_parts) == 4:
                            explicit_url = supplier_parts[3].strip()

                        # order num options
                        package_count = 1
                        ordernum_parts = order_num.split('##')
                        if len(ordernum_parts) == 1 or len(ordernum_parts) == 2:
                            order_num = ordernum_parts[0]
                            if len(ordernum_parts) == 2:
                                package_count = int(ordernum_parts[1])
                        else:
                            log.error("invalid order_num")
                            break

                        # pricing
                        amount = None
                        currency = None
                        country = ''
                        pricing_parts = pricing.split(' ')
                        if len(pricing_parts) == 2:
                            location = pricing_parts[0]
                            amount = float(pricing_parts[1])
                            location_parts = location.split('-')
                            if len(location_parts) == 1 or len(location_parts) == 2:
                                currency = location_parts[0]
                                if len(location_parts) == 2:
                                    country = location_parts[1]
                            else:
                                log.error("invalid location")
                                break
                        else:
                            log.error("invalid pricing")
                            break

                        part_entry_suppliers.append([supplier, order_num, package_count, currency, country, amount, explicit_url])
                    else:
                        log.error("invalid supplier line")
                        break                    
                elif auxline[0] in ('0','1','2','3','4','5','6','7','8','9','.'):  # usage line
                    # quantity   subsystem   specific_use
                    usage_components = auxline.split('   ')
                    if len(usage_components) == 3:
                        quantity = float(usage_components[0].strip())
                        subsystem = usage_components[1].strip()
                        specific_use = usage_components[2].strip()
                        part_entry_usages.append([quantity, subsystem, specific_use])
                    else:
                        log.error("invalid usage line")
                        break                     
                else:
                    log.error('invalid auxilliary line')
                    break
            else:  # master line
                # part_name[, units=mm]  [part_group]
                line_parts = line.strip().split("   ")
                if (len(line_parts) == 1 or len(line_parts) == 2) and line_parts[0] != '':
                    if line_parts[0] == '':
                        # was just an empty filler line
                        continue
                    # create an empty part entry
                    # [name, quantity_units, group, notes, designators, manufacturers suppliers, usages]
                    parts.append([None,'','',[],[],[],[],[]])
                    part_entry = parts[-1]  # get new entry
                    part_entry_notes = part_entry[3]
                    part_entry_designators = part_entry[4]
                    part_entry_manufacturers = part_entry[5]
                    part_entry_suppliers = part_entry[6]
                    part_entry_usages = part_entry[7]

                    name_parts = line_parts[0].strip().split('units=')
                    part_name = name_parts[0].strip()
                    if part_name[-1] == ',':
                        part_name = part_name[:-1].strip()
                    quantity_units = ''
                    if len(name_parts) == 2:
                        quantity_units = name_parts[1]
                    part_group = ''
                    if len(line_parts) == 2:
                        part_group = line_parts[1].strip()
                    part_entry[0] = part_name
                    part_entry[1] = quantity_units
                    part_entry[2] = part_group
                else:
                    log.error("invalid master line")
                    break
             
    # pprint(parts)
    # pprint(stats_num_items)
    return parts


def sort_by_subsystem(bom, currency):
    # sort by subsystem
    # {subsystem: [ part_name, part_group,
    #               [[supplier_name, order_num, package_count, package_units, currency, country, amount, explicit_url]], 
    #               {subsystem: [quantity, specific_use], subsystem_: [..], ...} ]
    by_subsystem = {}
    for part in bom:

        part_entry = []
        part_entry.append(part[0])
        part_entry.append(part[1])
        # add first applicable source
        source_list_filtered = []
        # print part[2]
        for source in part[2]:
            if source[4] == currency:
                source_list_filtered.append(source)
        if not source_list_filtered:  # no applicable source
            # skip this part
            continue
        part_entry.append(source_list_filtered)

        # assemble subsystem dictionary
        usages = part[3]
        subsystems = {}
        local_subsystems = []
        for usage in usages:
            subsys = usage[1]
            if subsys in local_subsystems:
                log.error("repetitive subsystem lines")
                break
            local_subsystems.append(subsys)
            if subsys not in subsystems:
                subsystems[subsys] = []
            subsystems[subsys] = [usage[0], usage[2]]
        part_entry.append(subsystems)

        # reference under applicable subsystems
        for subsys in subsystems:
            if subsys not in by_subsystem:
                by_subsystem[subsys] = []
            by_subsystem[subsys].append(part_entry)

    return by_subsystem



def dump(bom):
    """
    Convert standard json representation to bomfu file format.

    bomfu_json:
    [
      [ part_name, quantity_units, part_group,
        [ note,
          ...
        ],
        [ designator,
          ...
        ],
        [ [manufacturer, part_num],
          ...
        ],
        [ [supplier_name, order_num, package_count, currency, country, amount, explicit_url], 
          [another supplier],
            ...
        ],
        [ [quantity, subsystem, specific use],
          [another usage],
            ...
        ]
      ],
      [ another part ],
        ...
    ]

    returns:
    part_name[, units=mm]  [part_group]
       [* notes]
       [# designators]
       [@ manufacturer_name, part_num]
       [$ supplier_name   order_num[##package_count]   currency[-country] amount   [explicit_url] ]
       [quantity   subsystem   specific_use]
    """

    # # sort by subsystem
    # by_subsystem = {}
    # for part in bomfu_json:
    #     usages = part[3]
    #     local_subsystems = []
    #     for usage in usages:
    #         subsys = usage[1]
    #         if subsys in local_subsystems:
    #             log.error("repetitive subsystem lines")
    #             break
    #         local_subsystems.append(subsys)
    #         if subsys not in by_subsystem:
    #             by_subsystem[subsys] = []
    #         by_subsystem[subsys].append(part)


    # # check if ordered sussystem list is valid
    # subsys_set = set(subsystems)
    # key_set = set(by_subsystem.keys())
    # if subsys_set != key_set:
    #     log.error("subsystems don't match")
    #     print subsys_set.symmetric_difference(key_set)
    #     return

    out = []
    for part in bom:
        if len(part) != 8:
            log.error("invalid part entry")
            continue

        part_name = part[0]
        quantity_units = part[1]
        part_group = part[2]
        notes = part[3]
        designators = part[4]
        manufacturers = part[5]
        suppliers = part[6]
        usages = part[7]

        # master line
        out.append(part_name)
        if quantity_units:
            out.append(', units=' + str(quantity_units))
        if part_group:
            out.append('   ' + part_group)

        # note lines
        for note in notes:
            out.append('\n   * ' + note)

        # designator lines
        for designator in designators:
            out.append('\n   # ' + designator)

        # manufacturer lines
        for manufacturer in manufacturers:
            out.append('\n   @ ' + manufacturer[0] + '   ' + manufacturer[1])

        # source lines
        for supplier in suppliers:
            order_num = supplier[1]
            package_count = supplier[2]
            currency = supplier[3]
            country = supplier[4]
            amount = supplier[5]
            explicit_url = supplier[6]
            order_num_options = ''
            if package_count != 1:
                order_num_options += '##' + str(package_count)

            if country:
                country = '-' + country
            else:
                country = ''
            if explicit_url:
                explicit_url = '   ' + explicit_url
            else:
                explicit_url = ''

            # TODO consolidate same suppliers/order_num with different locations
            out.append('\n   $ ' + supplier[0] + '   ' + order_num + order_num_options +
                       '   ' + currency + country + ' ' + str(amount) + explicit_url)

        # usage lines
        for usage in usages:
            quantity = usage[0]
            subsystem = usage[1]
            specific_use = usage[2]
            out.append('\n   ' + str(quantity) + '   ' + subsystem + '   ' + specific_use)

        out.append('\n\n')

    out_string = ''.join(out)
    return out_string
