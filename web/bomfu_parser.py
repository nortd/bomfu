""" BOMfu file Parser

The Bomfu file format is optimized for human editing and parses easily.
The file lists two types: supplier definitions, parts

Supplier definitions 

Part entries consist of one "master" line and two kinds of auxilliary lines.
Latter consist of one or more "supplier" lines and one or more "usage" lines.
Parts are conventionally listed by subsystem and secondarily by part_group.

Within the supplier line there are one or more pricing elements. Each pricing
element is a currency, amount, and optionally an explicit url. 

part_name  [part_group]
   @supplier_name   order_num[##package_count[-units]]   currency[-country] amount   [explicit_url]
   [another_supplier_line]
   [...]
   quantity   subsystem   specific_use

The parser outputs to an intermediary json format. By default this output
format lists parts the same way as the imput file. Similarly the following
attributes are optional: part_group, url

[
  [ part_name, part_group,
    [ [supplier_name, order_num, package_count, package_units, currency, country, amount, explicit_url], 
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

import re
import json
import logging as log
from pprint import pprint


# enum for table column names
tITEM =      0;
tSUPPLIER =  1;
tORDERNUM =  2;
tLOCATIONS =  3;
tSUBSYSTEMUSE =  4;

# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig


def parse(bomstring):
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
    parts = [];  # list of [name, group, source_list, usage_list]
    part_entry = None
    for line in lines:
        if line and line[0] != '#' and line[0] != '!' and len(line) > 12:
            if line[:3] == '   ':  # auxilliary line
                # continue
                auxline = line[3:].strip()
                if auxline[0] == '@':  # source line
                    # @supplier_name   order_num[##package_count[-units]]   currency[-country] amount   [explicit_url]
                    supplier_parts = auxline.split('   ')
                    supplier = supplier_parts[0].strip()[1:]
                    order_num = supplier_parts[1].strip()
                    pricing = supplier_parts[2].strip()
                    explicit_url = ''
                    if len(supplier_parts) == 4:
                        explicit_url = supplier_parts[3].strip()

                    # order num options
                    package_count = 1
                    package_units = ''
                    ordernum_parts = order_num.split('##')
                    if len(ordernum_parts) == 1 or len(ordernum_parts) == 2:
                        if len(ordernum_parts) == 2:
                            order_num = ordernum_parts[0]
                            option_parts = ordernum_parts.split('-')
                            if len(option_parts) == 1 or len(option_parts) == 2:
                                package_count = int(option_parts[0])
                                if len(option_parts) == 2:
                                    package_units = option_parts[1]
                            else:
                                log.error("invalid order_num options")
                                break
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
                        amount = pricing_parts[1]
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

                    part_entry[2].append([supplier, order_num, package_count, package_units, currency, country, amount, explicit_url])

                elif auxline[0] in ('0','1','2','3','4','5','6','7','8','9'):  # usage line
                    # quantity   subsystem   specific_use
                    usage_components = auxline.split('   ')
                    quantity = int(usage_components[0].strip())  # TODO parse different quantity formats
                    subsystem = usage_components[1].strip()
                    specific_use = usage_components[2].strip()
                    part_entry[3].append([quantity, subsystem, specific_use])
                else:
                    log.error('invalid auxilliary line')
                    break
            else:  # master line
                # "item   supplier   order#   currency price [url] [currency price [url]]    ..."
                parts.append([])
                part_entry = parts[-1]  # get new entry
                line_parts = line.split("   ")
                if len(line_parts) == 2:
                    part_name = line_parts[0].strip()
                    part_group = line_parts[1].strip()
                    part_entry.append(part_name)
                    part_entry.append(part_group)
                    part_entry.append([])
                    part_entry.append([])
                else:
                    log.error("invalid master line")
             
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
      [ part_name, part_group,
        [ [supplier_name, order_num, package_count, package_units, currency, country, amount, explicit_url], 
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
    part_name  [part_group]
       @supplier_name   order_num[##package_count[-units]]   currency[-country] amount   [explicit_url]
       [another_supplier_line]
       [...]
       quantity   subsystem   specific_use
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
        if len(part) != 4:
            log.error("invalid part entry")
            continue

        part_name = part[0]
        part_group = part[1]
        suppliers = part[2]
        usages = part[3]

        # master line
        out.append(part_name + '   ')
        out.append(part_group)

        # source lines
        for supplier in suppliers:
            order_num = supplier[1]
            package_count = supplier[2]
            package_units = supplier[3]
            currency = supplier[4]
            country = supplier[5]
            amount = supplier[6]
            explicit_url = supplier[7]
            order_num_options = ''
            if package_count != 1:
                order_num_options += '##' + str(package_count)
                if package_units != '':
                    order_num_options += '-' + package_units
            else:
                if package_units != '':
                    order_num_options += '##1-' + package_units

            if country != '':
                country = '-' + country
            if explicit_url != '':
                explicit_url = '   ' + explicit_url

            # TODO consolidate same suppliers/order_num with different locations
            out.append('\n   @' + supplier[0] + '   ' + order_num + order_num_options +
                       '   ' + currency + country + ' ' + str(amount) + explicit_url)

        # usage lines
        for usage in usages:
            quantity = usage[0]
            subsystem = usage[1]
            specific_use = usage[2]
            out.append('\n   ' + str(quantity) + '   ' + subsystem + '   ' + specific_use)

        out.append('\n')

    out_string = ''.join(out)
    return out_string
