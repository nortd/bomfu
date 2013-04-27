""" BOMfu file Parser

The Bomfu file format is optimized for human editing and parses easily.
The file lists two types: supplier definitions, parts

Supplier definitions 

Part entries consist of one "master" line and two kinds of auxilliary lines.
Latter consist of one or more "supplier" lines and one or more "usage" lines.
Parts are conventionally listed by subsystem and secondarily by part_group.

Within the supplier line there are one or more pricing elements. Each pricing
element is a currency, amount, and optionally an explicit url. 

masterLine
   supplier line (one or more)
   usage line (one or more)

part_name  [part_group]
   @supplier_name   order_num[##package_count[-unit]]   currency[-country] amount [explicit_url]   [cur-amount-url triplet] [...]
   [another_supplier_line]
   [...]
   quantity   subsystem   specific_use

The parser outputs to an intermediary json format. By default this output
format lists parts the same way as the imput file. Similarly the following
attributes are optional: part_group, url

[
  [ part_name, part_group,
    [ [supplier_name, order_num, package_count, package_units, [[currency, amount, explicit_url], [another triplet], ...] ],
      [another supplier],
        ...
      ]
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


def get_new_from_legacy():
    import bomfu_parser
    subsystems = ['frame-gantry','frame-table','frame-outer',
                  'frame-door','y-cart','y-drive', 'x-cart','x-drive','electronics',
                  'optics-laser','frame-panels','air-assist', 'extra']
    bom_json_old = bomfu_to_json_old(bom_legacy)
    bom_json = convert_old_to_new(bom_json_old)
    bom = bomfu_parser.dump(bom_json)
    return bom


def bomfu_to_json_old(bomfu_string):
    """
    returns a list of:
     ['cable tie, 2.5x100mm, white',
      'Mouser',
      'BT1M-M10',
      {'EUR': [0.05,
               'http://uk.mouser.com/Search/Refine.aspx?Keyword=BT1M-M10'],
       'USD': [0.06,
               'http://us.mouser.com/Search/Refine.aspx?Keyword=BT1M-M10']},
      [[4, 'y-drive', 'belt to cart'],
       [4, 'x-drive', 'belt to cart'],
       [16, 'optics-laser', 'cable and hose to laser tube']]]
    """

    lines = bomfu_string.split('\n')

    stats_num_items = {'USD':0, 'EUR':0}
    # first parse supplierdefs
    # supplierdef   supplier   currency url_pattern   [currency url_pattern]   ...
    supplierdefs = {};  # {supplier: {currency:url, ...}, ...}
    for line in lines:
        if line[:12] == "!supplierdef":
            def_parts = line.split("   ")
            supplier_name = def_parts[1].strip()
            supplierdefs[supplier_name] = {}
            for l in range(2,len(def_parts)):
                loc_pair = def_parts[l].split(" ");
                currency = loc_pair[0].strip()
                url_pattern = loc_pair[1].strip()
                supplierdefs[supplier_name][currency] = url_pattern;
    # pprint(supplierdefs)

    # then parse parts lines
    # which consist out of a master line and one or more auxilliary lines
    parts = [];  # list of [item, supplier, order#, {'EUR':[price,url]}, [[num,subsystem,use],[num,subsystem,use],...]]
    for line in lines:
        if line and line[0] != '#' and line[0] != '!' and len(line) > 12:
            masterLine = []
            if line[:3] == '   ':
                # we are dealing with an auxilliary line
                # "num   subsystem   use"
                masterLine = parts[-1]  # get latest entry
                if len(masterLine) == tSUBSYSTEMUSE+1:
                    usage_parts = line[3:].split("   ")
                    for i in range(len(usage_parts)):  #strip
                        usage_parts[i] = usage_parts[i].strip()
                        if "   " in usage_parts[i]:  # sanity check
                            log.error('got smashed items')
                            log.error(line)
                            return
                        if i == 0:
                            usage_parts[i] = int(usage_parts[i])
                    masterLine[tSUBSYSTEMUSE].append(usage_parts)
                else:
                    log.error('aux line without proper preceding master line')
                    log.error(line)
                    return
            else:
                # new item line
                # "item   supplier   order#   currency price [url] [currency price [url]]    ..."
                parts.append([])
                masterLine = parts[-1]  # get new entry
                masterLineParts = line.split("   ")
                for mlpart in masterLineParts:  # sanity check
                    if "   " in mlpart:  
                        log.error('got smashed items')
                        log.error(line)
                        return                      
                if len(masterLineParts) >= 4:
                    # a master line has at least 4 parts and can have multiple locations
                    masterLine.append(masterLineParts[tITEM].strip())
                    masterLine.append(masterLineParts[tSUPPLIER].strip())
                    masterLine.append(masterLineParts[tORDERNUM].strip())
                    # parse locations
                    locs = {}
                    for k in range(3,len(masterLineParts)):
                        # for each location component extract 
                        # "currency price [url]"
                        location_parts = masterLineParts[k].split(" ")
                        if len(location_parts) >= 2:
                            cur = location_parts[0].strip().upper()
                            amount = float(location_parts[1].strip())
                            url = ""
                            if len(location_parts) >= 3:
                                url = location_parts[2].strip()
                            else:
                                pass
                                # # use url pattern from supplierdef
                                # if masterLine[tSUPPLIER] in supplierdefs:
                                #   if cur in supplierdefs[masterLine[tSUPPLIER]]:
                                #       url_pattern = supplierdefs[masterLine[tSUPPLIER]][cur]
                                #       url = url_pattern.replace('%%', masterLineParts[tORDERNUM])                                     
                                #   else:
                                #       log.error("currency not defined in supplierdef")
                                #       log.error(line)
                                #       return
                                # else:
                                #   log.error("supplier not defined in supplierdefs: " + masterLine[tSUPPLIER])
                                #   log.error(line)
                            if cur in stats_num_items:
                                stats_num_items[cur] += 1
                            if cur not in locs:
                                locs[cur] = [amount, url]
                            else:
                                log.error("repetitive currencies")
                                log.error(line)
                                return                              
                        else:
                            log.error("too few master line location parts")
                            log.error(line)
                            return
                    masterLine.append(locs)  # locations
                    masterLine.append([])    # masterLine[tSUBSYSTEMUSE]
                else:
                    log.error("too few master line parts")
                    log.error(line)
                    return  
    # pprint(parts)
    # pprint(stats_num_items)
    return parts




def convert_old_to_new(old_json):
    """
    old_json:
     ['cable tie, 2.5x100mm, white',
      'Mouser',
      'BT1M-M10',
      {'EUR': [0.05,
               'http://uk.mouser.com/Search/Refine.aspx?Keyword=BT1M-M10'],
       'USD': [0.06,
               'http://us.mouser.com/Search/Refine.aspx?Keyword=BT1M-M10']},
      [[4, 'y-drive', 'belt to cart'],
       [4, 'x-drive', 'belt to cart'],
       [16, 'optics-laser', 'cable and hose to laser tube']]]

    returns:
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

    new_json = []
    for part in old_json:
        name = part[tITEM]
        supplier = part[tSUPPLIER]
        order_num = part[tORDERNUM]
        sources = part[tLOCATIONS]
        usage = part[tSUBSYSTEMUSE]

        new_part = []
        new_part.append(name)
        new_part.append('')

        sources_list = []
        for currency, price_url in sources.items():
            url = None
            if len(price_url) == 1:
                url = ''
            elif len(price_url) == 2:
                url = price_url[1]
            else:
                log.error("invalid pricing dict entry")
                break
            sources_list.append([supplier, order_num, 1, '', currency, '', price_url[0], url])
        new_part.append(sources_list)

        usage_list = []
        for usage_ in usage:
            usage_list.append(usage_)
        new_part.append(usage_list)

        new_json.append(new_part)

    # return json.dumps(new_json, indent=2, sort_keys=True)
    return new_json


    # # sort by supplier
    # by_supplier = {}
    # for part in new_json:
    #     sources = part[2]
    #     local_suppliers = []
    #     for source in sources:
    #         supplier = source[0]
    #         if supplier in local_suppliers:
    #             log.error("repetitive supplier lines")
    #             break
    #         local_suppliers.append(supplier)
    #         if supplier not in by_supplier:
    #             by_supplier[supplier] = []
    #         by_supplier[supplier].append(part)





bom_legacy = """
#   item   supplier   order#   currency price [url]   [currency price [url]]   ...
#   num   subsystem   use


!supplierdef   NortdLabs   EUR /lasersaur/store#%%   USD /lasersaur/store#%%
!supplierdef   Misumi   EUR http://uk.misumi-ec.com/eu/EcSearchView.html?kw=%%   USD http://us.misumi-ec.com/us/EcSearchView.html?kw=%%
!supplierdef   ThorLabs   EUR http://www.thorlabs.com/search/thorsearch.cfm?search=%%   USD http://www.thorlabs.com/search/thorsearch.cfm?search=%%
!supplierdef   Mouser   EUR http://uk.mouser.com/Search/Refine.aspx?Keyword=%%   USD http://us.mouser.com/Search/Refine.aspx?Keyword=%%
!supplierdef   McMaster   EUR http://www.mcmaster.com/#%%   USD http://www.mcmaster.com/#%%


### NortdLabs
Lasersaur DriveBoard PCB   NortdLabs   la-dbp   USD 138.0   EUR 115.0
   1   electronics   controller board
MechParts Aluminum   NortdLabs   la-mpk   USD 285.0   EUR 235.0
   1   electronics   2x door sensor mounts
   0   y-drive   2x shaft bearing mounts, 1x limit sensor mount, 1x motor mount
   0   x-cart   2x roller/optics mounts
   0   x-drive   1x motor mount, 2x limit sensor mounts
   0   optics-laser   4x laser tube mounts
Lasersaur Nozzle   NortdLabs   la-noz   USD 110.0   EUR 80.0
   1   optics-laser   laser head
Lens and Mirrors Pack   NortdLabs   la-lmp   USD 295.0   EUR 225.0
   1   optics-laser   laser beam delivery


### Misumi
aluminum bracket extrusion   Misumi   HFLBS5-650   USD 2.0   EUR 2.0
   1   x-drive   cable carrier base
angle bracket, single   Misumi   HBLFSN5   USD 0.75   EUR 0.63
   26   frame-outer   6x front columns, 8x separation columns, 10x rear box
   8   frame-door   door connections
   1   optics-laser   mirror2
   8   extra   extra
angle bracket, single, black   Misumi   HBLFSNB5   USD 1.98   EUR 1.32
   8   frame-outer   bottom cross
   12   frame-table   table frame
   2   extra   extra
angle bracket, single, light   Misumi   HBLSS5   USD 1.02   EUR 0.7
   4   x-cart   extrusion connection
   2   extra   extra
angle bracket, single, long, narrow   Misumi   HBLTSW5   USD 3.39   EUR 2.26
   1   y-drive   motor
angle bracket, double   Misumi   HBLFSD5   USD 2.3   EUR 1.95
   27   frame-outer   25x side columns, 2x side edges
   4   frame-door   door connections
   1   optics-laser   mirror1
   6   extra   extra
angle bracket, double, light   Misumi   HBLSD5   USD 1.32   EUR 0.88
   2   y-drive   pulley
   2   extra   extra
angle bracket, double, heavy   Misumi   HBLFSDW5   USD 3.15   EUR 2.1
   4   frame-gantry   gantry frame corners
   2   optics-laser   laser mounts
ball bearing 5x19x6mm   Misumi   B635ZZ   USD 5.18   EUR 1.4
   4   y-drive   idler
   2   x-drive   idler
ball bearing 6x19x6mm   Misumi   B626ZZ   USD 2.53   EUR 1.7
   2   y-drive   2x shaft mount
ball bearing roller 4x13x5mm   Misumi   EB13   USD 11.28   EUR 10.1
   8   y-cart   roller
   6   x-cart   roller
   1   extra   extra
cable carrier, 20 links   Misumi   MHPKS101-19-20-S   USD 19.88   EUR 19.30
   2   x-drive   gas assist
cable carrier, 23 links   Misumi   MHPUS102-19-23-S   USD 29.57   EUR 29.0
   1   y-drive   life line
gas spring   Misumi   FGSS22150B   USD 23.88   EUR 19
   2   frame-door   door
hinges   Misumi   HHPSN5   USD 3.8   EUR 3.6
   3   frame-door   door
metal sheet 1166x356x0.8mm   Misumi   PDSPHC4H-1166-356-0.8-F1110-G340-N5-UN10-XC8-YC8   USD 44   EUR 41
   1   frame-panels   left side
metal sheet 1166x847x0.8mm   Misumi   PDSPHC4H-1166-847-0.8-F1150-G790-N5-UN10-XC8-YC9   USD 58   EUR 54
   2   frame-panels   bottom
metal sheet 247x216x0.8mm   Misumi   PDSPHC4H-247-216-0.8-F190-G200-N5-UN10-XC9-YC8   USD 25   EUR 24
   1   frame-panels   right side
metal sheet 847x200x0.8mm   Misumi   PDSPHC4H-847-200-0.8-F790-G180-N5-UN10-XC48-YC8   USD 35   EUR 33
   2   frame-panels   front
metal sheet 847x268x0.8mm   Misumi   PDSPHC4H-847-268-0.8-F790-G250-N5-UN10-XC48-YC8   USD 35   EUR 33
   2   frame-panels   rear top
metal sheet 847x356x0.8mm   Misumi   PDSPHC4H-847-356-0.8-F790-G340-N5-UN10-XC48-YC8   USD 38   EUR 36
   2   frame-panels   rear
metal sheet 917x356x0.8mm   Misumi   PDSPHC4H-917-356-0.8-F900-G340-N5-UN10-XC8-YC8   USD 40   EUR 38
   1   frame-panels   right side
nut DIN934-like, M3   Misumi   LBNR3   USD 0.08   EUR 0.28
   1   x-drive   1x cable carrier
   6   electronics   2x power entry module, 4x driveboard
   8   extra    extra
nut DIN985-like, lock, M4, 100 pack   Misumi   PACK-UNUT4   USD 14.6   EUR 14.6
   1   y-cart   16x roller
   0   y-drive   4x bearing clamps
   0   x-cart   11x roller
   0   optics-laser   4x laser tube mount
nut DIN985-like, lock, M5, 100 pack   Misumi   PACK-UNUT5   USD 15   EUR 15
   1   y-drive   6x motor mount, 4x pulley mount, 4x limit switch
   0   x-cart   4x custom part connection
   0   x-drive   1x motor mount
   0   optics-laser   8x laser mount
panel clamps 6m   Misumi   HSCP3H-B-6   USD 24   EUR 20
   1   frame-outer   framing support for separation panels
planar bracket, double   Misumi   SHPTSD5   USD 1.75   EUR 1.2
   4   frame-gantry   gantry frame y-rails
   2   frame-outer   middle column, separation
platic handles   Misumi   UPCN19-B-36   USD 5.8   EUR 4.8
   2   frame-door   door
polycarbonate sheet 170x130x3mm   Misumi   PCTBA-170-130-3   USD 7   EUR 5
   2   frame-outer   compartment separation, sides, bottom
polycarbonate sheet 600x130x3mm   Misumi   PCTBA-600-130-3   USD 21   EUR 18
   2   frame-outer   compartment separation, bottom
polycarbonate sheet 800x110x3mm   Misumi   PCTBA-800-110-3   USD 27   EUR 22
   2   frame-outer   compartment separation, top
polycarbonate sheet 807x60x3mm   Misumi   PCTBA-807-60-3   USD 14   EUR 11
   2   frame-door   door slit cover
polycarbonate sheet 847x156x3mm   Misumi   PCTBA-847-156-3   USD 29   EUR 24
   2   frame-panels   door cover front
polycarbonate sheet 892x847x3mm   Misumi   PCTBA-892-847-3   USD 135   EUR 100
   2   frame-panels   door cover top
rotary shaft with step   Misumi   SFAC8-692-F24-P6   USD 37.0   EUR 23.0
   2   y-drive   motor to pulley
screw DIN912-like, M2.5x12   Misumi   CB2.5-12   USD 1   EUR 1
   4   x-drive   limit switch
   4   y-drive   limit switch
   4   electronics   door switch
screw DIN912-like, M3x06   Misumi   CB3-6   USD 0.13   EUR 0.13
   1   x-drive   cable carrier
   4   electronics   psu mount
   1   extra    extra
screw DIN912-like, M3x10   Misumi   CB3-10   USD 0.13   EUR 0.13
   5   x-drive   4x motor mount, 1x cable carrier
   2   air-assist   e-valve mount
   5   extra    extra
screw DIN912-like, M3x16   Misumi   CB3-16   USD 0.13   EUR 0.13
   10   electronics   6x power entry module, 4x driveboard mount
screw DIN912-like, M3x25   Misumi   CB3-25   USD 0.13   EUR 0.13
   1   air-assist   e-valve mount
screw DIN912-like, M3x30   Misumi   CB3-30   USD 0.13   EUR 0.13
   4   electronics   driveboard mount
screw DIN912-like, adhesive, M4x15   Misumi   LB4-15   USD 0.14   EUR 0.14
   4   y-drive   4x bearing clamps
   1   x-cart   roller
   4   extra    extra
screw DIN912-like, adhesive, M4x25   Misumi   SUSLB4-25   USD 0.5   EUR 0.4
   8   y-cart   roller
   5   x-cart   roller
   2   optics-laser   4x laser tube mount
   3   extra   extra
screw DIN912-like, M5x08   Misumi   CB5-8   USD 0.13   EUR 0.10
   16   frame-gantry   16x planar bracket
   8   frame-outer   8x planar bracket
   38   frame-panels   22x door top, 16x door front
   8   frame-door   8x door slit cover
   6   y-drive   4x shaft mount, 2x limit switch
   4   x-cart   angle connection
   4   electronics   panel mount
   40   extra    extra
screw DIN912-like, M5x10   Misumi   CB5-10   USD 0.10   EUR 0.08
   32   frame-gantry   32x angle brackets
   190   frame-outer   190x frame connections
   32   frame-door   32x angel brackets
   24   frame-table   angle brackets
   2   y-drive   2x motor
   14   optics-laser   4x mirror1, 2x mirror2, 8x laser mount
   80   extra    extra
screw DIN912-like, M5x12   Misumi   CB5-12   USD 0.12   EUR 0.12
   4   electronics   door switch
   5   x-drive   1x motor mount, 4x limit switch
   4   frame-door   4x door handle
   5   extra    extra
screw DIN912-like, M5x16   Misumi   CB5-16   USD 0.13   EUR 0.13
   8   y-drive   4x shaft mount, 4x limit switch
   4   x-cart    custom part connection
   1   x-drive   motor mount
   10   extra    extra
screw DIN912-like, M5x20   Misumi   CB5-20   USD 0.13   EUR 0.13
   4   frame-door   gas spring mount
   4   y-cart   4x cart-bar
   6   y-drive   motor
   10   optics-laser   8x laser mount, 2x mirror1
   8   extra    extra
screw DIN912-like, adhesive, M5x25   Misumi   SUSLB5-25   USD 0.5   EUR 0.4
   4   y-cart   4x cart bar
   2   y-drive   2x idler shaft
   2   x-cart   2x cart bar
   1   x-drive   1x idler shaft
   2   extra   extra
screw ISO7380-like, button, M5x06   Misumi   BCB5-6   USD 0.11   EUR 0.11
   100   frame-panels   100x metal sheets
   2   y-drive   cable carrier
   4   optics-laser   4x laser PSU
   60   extra    extra
screw DIN7991-like, sunk, M5x08   Misumi   SFB5-8   USD 0.66   EUR 1.1
   12   frame-door   door hinges
screw DIN7991-like, sunk, M5x12   Misumi   SFB5-12   USD 1.3   EUR 1.3
   2   x-drive   cable carrier base
screw DIN7984-like, low, M5x16   Misumi   CBSS5-16   USD 0.5   EUR 0.5
   4   y-drive   belt attachment
   2   x-drive   belt attachment
shaft coupling, 6.35 to 8mm   Misumi   MCKSC20-6.35-8   USD 29   EUR 23.4
   2   y-drive   motor to shaft
slide washer   Misumi   SWSPT25-10-1.0   USD 3.72   EUR 4.60
   2   y-drive   idler
   1   x-drive   idler
timing belt XL, 350 teeth, 1780mm   Misumi   TBO-XL025-350   USD 28   EUR 24
   2   y-drive   drive belt left/right
timing belt XL, 600 teeth, 3050mm   Misumi   TBO-XL025-600   USD 48   EUR 42
   1   x-drive   drive belt
timing pulley XL, 12 teeth, bore 5mm   Misumi   ATP12XL025-B-P5   USD 12   EUR 16
   1   x-drive   motor pulley
timing pulley XL, 12 teeth, bore 6mm   Misumi   ATP12XL025-B-P6   USD 12   EUR 11.9
   2   y-drive   pulley left/right, set screw
extrusion 2020, 1564mm   Misumi   HFS5-2020-1564   USD 8.91   EUR 7.4
   1   frame-door   door front bottom
extrusion 2020, 60mm, 45deg   Misumi   HFS5-2020-60-LAT45   USD 6.9   EUR 6.5
   1   optics-laser   mirror2
extrusion 2020, 80mm   Misumi   HFS5-2020-80   USD 3   EUR 2.5
   2   frame-door   door front
extrusion 2040, 100mm   Misumi   HFS5-2040-100   USD 4.6   EUR 4
   1   frame-outer   rear middle top column
extrusion 2040, 1130mm   Misumi   HFS5-2040-1130   USD 12   EUR 15
   2   frame-outer   frame side bottom
extrusion 2040, 120mm, black   Misumi   HFSB5-2040-120   USD 5   EUR 4.6
   2   frame-outer   columns
extrusion 2040, 124mm, + mount holes   Misumi   HFS5-2040-124-Z5-YA43   USD 7.66   EUR 5.0
   1   x-cart   cart-bar
extrusion 2040, 1260mm, black   Misumi   HFSB5-2040-1260   USD 21   EUR 17.66
   5   frame-table   table wide
extrusion 2040, 140mm, + mount holes   Misumi   HFS5-2040-140-Z5-YA20-YB94   USD 12.5   EUR 8.0
   1   y-cart   cart-bar
extrusion 2040, 1564mm   Misumi   HFS5-2040-1564   USD 17   EUR 14
   1   frame-door   door front
extrusion 2040, 1620mm   Misumi   HFS5-2040-1620   USD 16.5   EUR 17
   4   frame-outer   frame front, middle, 2x back
extrusion 2040, 190mm   Misumi   HFS5-2040-190   USD 3   EUR 3
   4   frame-outer   2x rear middle top, bottom, 2x laser psu mount
extrusion 2040, 320mm   Misumi   HFS5-2040-320   USD 3.5   EUR 3
   1   frame-outer   back middle
extrusion 2040, 62mm, + mount holes   Misumi   HFS5-2040-62-Z5-YA10   USD 7.66   EUR 5.0
   1   optics-laser   mirror1
extrusion 2040, 750mm, black   Misumi   HFSB5-2040-750   USD 12.5   EUR 8
   1   frame-outer   bottom cross right
extrusion 2040, 75mm   Misumi   HFS5-2040-75-LTP   USD 6.5   EUR 7.0
   1   x-cart   cart-bar
extrusion 2040, 790mm, balck   Misumi   HFSB5-2040-790   USD 13.2   EUR 8
   1   frame-outer   bottom cross left
extrusion 2040, 80mm   Misumi   HFS5-2040-80   USD 2.6   EUR 2.9
   1   frame-door   door front
extrusion 2040, 80mm, 45deg   Misumi   HFS5-2040-80-LAT45   USD 6.7   EUR 3.8
   1   optics-laser   mirror1
extrusion 2040, 830mm   Misumi   HFS5-2040-830   USD 9   EUR 8
   3   frame-door   door top
extrusion 2040, 858mm, black   Misumi   HFSB5-2040-858   USD 14.4   EUR 12.08
   2   frame-table   table short
extrusion 2040, 860mm   Misumi   HFS5-2040-860   USD 9.3   EUR 8
   1   frame-outer   cable carrier mount
   1   extra   extra
extrusion 2040, 860mm, black   Misumi   HFSB5-2040-860   USD 14.36   EUR 8
   1   frame-outer   bottom cross middle
extrusion 2040, 96mm, + mount holes   Misumi   HFS5-2040-96-Z5-YA46-YB76   USD 12.5   EUR 8.0
   1   y-cart   cart-bar
extrusion 2080, 70mm   Misumi   HFS5-2080-70-LTP   USD 13.0   EUR 16.0
   2   y-cart   cart-bar
extrusion 4040, 100mm   Misumi   HFS5-4040-100   USD 4.6   EUR 4
   2   frame-outer   corner top column
extrusion 4040, 1130mm   Misumi   HFS5-4040-1130   USD 17.4   EUR 15
   2   frame-outer   frame side top
extrusion 4040, 120mm   Misumi   HFS5-4040-120   USD 4.6   EUR 4
   6   frame-outer   frame front, middle, corner column
extrusion 4040, 120mm, black   Misumi   HFSB5-4040-120   USD 8   EUR 8.6
   2   frame-outer   columns
extrusion 4040, 1426mm   Misumi   HFS5-4040-1426   USD 22.0   EUR 18.0
   1   y-cart   cart-bar
extrusion 4040, 1564mm   Misumi   HFS5-4040-1564   USD 24   EUR 20
   1   frame-door   door rear
extrusion 4040, 1620mm   Misumi   HFS5-4040-1620   USD 25   EUR 21
   1   frame-outer   frame middle sep
extrusion 4040, 190mm   Misumi   HFS5-4040-190   USD 4.6   EUR 5
   1   frame-outer   rear side
extrusion 4040, 360mm   Misumi   HFS5-4040-360   USD 5.6   EUR 7
   2   frame-outer   corner rear
extrusion 4040, 860mm   Misumi   HFS5-4040-860   USD 13.3   EUR 10.92
   2   frame-gantry   y-rails, left and right
   1   extra   extra
extrusion 4080, 100mm   Misumi   HFS5-4080-100   USD 9.4   EUR 9
   2   frame-outer   side
extrusion 4080, 1620mm   Misumi   HFS5-4080-1620   USD 56   EUR 47
   2   frame-gantry   gantry frame, rear and front
extrusion 4080, 940mm   Misumi   HFS5-4080-940   USD 32.5   EUR 27
   2   frame-gantry   gantry frame, left and right
air tube, ODxID 6x4mm, 10m   Misumi   PUT6-10-CB   USD 12   EUR 10
   1   air-assist   entry panel to laser head
one-touch coupling, 6mm, M5   Misumi   MSELL6-M5   USD 3   EUR 3
   3   air-assist   1x nozzle coupling, 2x e-valve coupling
one-touch panel-mount, 6mm   Misumi   MSBUL6   USD 3   EUR 3
   1   air-assist   entry panel
nut T-slot, post, M3   Misumi   HNTP5-3   USD 0.56   EUR 0.50
   2   x-drive   cable carrier
   1   air-assist   e-valve mount
nut T-slot, pre, M4   Misumi   HNTE5-4   USD 0.46   EUR 0.45
   8   y-cart   8x rollers
   2   x-cart   roller
   3   optics-laser   mirrors
   10   extra   extra
nut T-slot, post, M5, lock   Misumi   HNTPZ5-5   USD 0.69   EUR 0.60
   48   frame-gantry   16x planar brackets, 32x angle brackets
   190   frame-outer   190x frame connections
   138   frame-panels   22x door top, 16x door front, 100x metal sheets
   76   frame-door   32x brackets, 4x gas spring, 12x hinge, 4x door handle, 12x door hinge, 4x gas spring, 8x door slit cover
   8   electronics   4x door switch, 4x panel mount
   24   frame-table   angle brackets
   4   y-cart   4x cart-bar
   20   y-drive   6x pulley/idler, 2x motor, 2x limit switch, 4x belt, 4x shaft mount, 2x cable carrier
   4   x-cart   angle connection
   10   x-drive   1x idler, 1x motor, 2x cable carrier base, 2x belt, 4x limit switch
   20   optics-laser   6x mirror1, 2x mirror2, 8x laser mount, 4x laser PSU
   60   extra   extra
water hose ID 9mm, 10m   Misumi   AHOS9-10   USD 29.6   EUR 21.5
   1   optics-laser   chiller to laser to chiller
washer DIN125-like, form A, M4   Misumi   PWF4   USD 0.13   EUR 0.13
   8   x-cart   roller
   10   extra    extra
washer DIN125-like, form A, M5   Misumi   PWF5   USD 0.13   EUR 0.13
   16   frame-gantry   planar brackets
   12   frame-outer   4x door switch, 8x planar bracket
   20   frame-door   gas spring mount
   38   frame-panels   22x door top, 16x door front
   12   y-drive   8x idler, 6x motor, 2x limit switch
   4   x-cart   custom part connection
   20   x-drive   2x motor mount, 4x idler, 4x limit switch, 10x cable carrier base
   20   extra    extra
washer DIN9021-like, form G, M4, 50 pack   Misumi   PACK-SPWFN4   USD 9.7   EUR 9.7
   1   y-cart   8x roller
   0   y-drive   8x bearing
   0   x-cart   2x roller
   0   optics-laser   2x laser tube mount
   0   extra    20x extra
washer DIN9021-like, form G, M5, 20 pack   Misumi   PACK-SPWFN5   USD 7.6   EUR 9.6
   3   frame-door   20x gas spring mount
   0   y-drive   4x idler, 4x shaft mount
   0   x-drive   2x idler, 1x motor mount
   0   optics-laser   8x laser mount
   0   extra    16x extra
washer Schnorr-like, lock, M3   Misumi   GTS3   USD 0.12   EUR 0.12
   4   y-drive   4x limit switch
   10   x-drive   3x motor, 4x limit switch, 3x cable carrier
   12   electronics   4x door switch, 4x power entry module, 4x psu mount
   1   air-assist   e-valve mount
   12   extra    extra
washer Schnorr-like, lock, M5   Misumi   GTS5   USD 0.13   EUR 0.13
   20   extra    extra


### ThorLabs
mirror mount   ThorLabs   KM100   USD 40   EUR 35.5
   3   optics-laser   flying optics, 1, 2, 3
lens tube 1"   ThorLabs   SM1M10   USD 16   EUR 13.0
   1   optics-laser   flying optics, head
lock ring, outer   ThorLabs   SM1NT   USD 8   EUR 7
   2   optics-laser   laser head, nozzle
safety glasses for 10600nm   ThorLabs   LG6   USD 130   EUR 130
   1   optics-laser   for user's eyes
cleaning tissues   ThorLabs   MC-5   USD 10   EUR 9
   1   optics-laser   optics cleaning
cleaning swabs   ThorLabs   CTA10   USD 5   EUR 4
   1   optics-laser   optics cleaning


### Mouser
screw terminal, 5.08mm, 6pos   Mouser   1729160   USD 2   EUR 2
   4   electronics   DriveBoard component
relay solid state, 5Vto280VAC, SPST-NO   Mouser   PF240D25   USD 22   EUR 18
   1   electronics   DriveBoard component
relays solid state, 5Vto24V   Mouser   AQY212GH   USD 4   EUR 4
   2   electronics   DriveBoard component
diode   Mouser   512-1N4004   USD 0.1   EUR 0.1
   2   electronics   DriveBoard component
RJ45-port, shielded   Mouser   GDLX-S-88K   USD 1   EUR 1
   15   electronics   DriveBoard component
logic gate, 3x3 AND, DIP14   Mouser   MC74AC11NG   USD 0.5   EUR 0.5
   1   electronics   DriveBoard component
logic gate, 3x3 NAND, DIP14   Mouser   MC74AC10NG   USD 0.5   EUR 0.5
   1   electronics   DriveBoard component
Atmega328P, PDIP   Mouser   ATMEGA328P-PU   USD 4.5   EUR 4.5
   1   electronics   DriveBoard component
DIP-28 socket   Mouser   4828-3004-CP   USD 0.4   EUR 0.3
   1   electronics   DriveBoard component
crystal 16MHz   Mouser   FOXSLF/160-20   USD 0.5   EUR 0.5
   1   electronics   DriveBoard component
ceramic cap, 22pF   Mouser   K220J15C0GF53L2   USD 0.3   EUR 0.3
   2   electronics   DriveBoard component
ceramic cap, 100nF   Mouser   K104M15X7RF53L2   USD 0.1   EUR 0.1
   10   electronics   DriveBoard component
electrolytic cap, 47uF   Mouser   EEU-HD1H470B   USD 0.4   EUR 0.3
   1   electronics   DriveBoard component
electrolytic cap, 100uF   Mouser   EEU-HD1H101B   USD 0.5   EUR 0.4
   1   electronics   DriveBoard component
electrolytic cap, 1000uF   Mouser   EEU-HD1H102   USD 1.6   EUR 1.3
   1   electronics   DriveBoard component
resistor 10 KOhm   Mouser   271-10K-RC   USD 0.15   EUR 0.11
   11   electronics   9x input pull-down resistor, 1x voltage divider, 1x driver sensing
   3   extra   extra
resistor 360 Ohm   Mouser   271-360-RC   USD 0.15   EUR 0.11
   2   electronics   ssr limit resistor
   8   extra   extra
resistor 11.5 KOhm   Mouser   271-11.5K-RC   USD 0.15   EUR 0.11
   3   electronics   1x y-axis motor option 1.4A (Gecko + Nanotec:ST5918M1008-B or LinE:WO-5718M-04ED), 1x x-axis motor option 1.35A  (Gecko + LinE:WO-4118S-04E)
   10   extra   extra
resistor 20 KOhm   Mouser   271-20K-RC   USD 0.15   EUR 0.11
   2   electronics   y-axis motor option 2.1A (Gecko + Nanotec:ST5918M3008-B or LinE:WO-5718M-02ED)
   1   extra   extra
resistor 6.49 KOhm   Mouser   271-6.49K-RC   EUR 0.11
   2   electronics   1x voltage divider, 1x x-axis motor option 0.84A (Gecko + Nanotec:ST4118M1206-A)
   10   extra   extra
resistor 12.7 KOhm   Mouser   271-12.7K-RC   USD 0.15
   1   electronics   x-axis motor option 1.5A  (Gecko + LinE:WO-4118S-01)
   10   extra   extra
cable tie, 2.5x100mm, white   Mouser   BT1M-M10   USD 0.06   EUR 0.05
   4   y-drive   belt to cart
   4   x-drive   belt to cart
   16   optics-laser   cable and hose to laser tube
e-stop SPST block   Mouser   642-A0150B   USD 8   EUR 6
   1   electronics   e-stop
e-stop button 40mm   Mouser   642-A01ESSP3   USD 21   EUR 11
   1   electronics   e-stop
heat shrink tubing set   Mouser   526-HS-ASST-9   USD 16   EUR 11.82
   1   electronics   cable to sensor, stepper, laser
limit switch   Mouser   D2SW-3L2MS   USD 5.2   EUR 5
   6   electronics   4x limit for x/y-axis, 2x door
   1   extra   extra
power cable   Mouser   397002-01   USD 7
   2   electronics   1x power cable, 1x wiring internals
power cable   Mouser   364002-D01   EUR 6
   3   electronics   1x power cable, 2x wiring internals
power entry module C-14   Mouser   161-R30148-E   USD 2.5   EUR 2
   3   electronics   1x entry panel, 1x DriveBoard entry, 1x DriveBoard2Laser
rubber tape 0.75"x30mil   Mouser   2155-3/4x22FT-20rls   USD 5   EUR 4
   1   optics-laser   between laser tube and mounts
ethernet entry module   Mouser   PX0833/E   USD 7.85   EUR 6.15
   1   electronics   ethernet panel mount
power supply 5V@12A   Mouser   LS75-5   USD 20   EUR 18
   1   electronics   logic power
power supply 24V@3.2A   Mouser   LS75-24   USD 20   EUR 18
   1   electronics   motor power
headers, 5.08mm, 6pos   Mouser   10-08-1061   USD 1.6   EUR 1.4
   6   electronics   Gecko socket
headers, 2.54mm, 44ps   Mouser   10-89-7442   USD 3.7   EUR 3.2
   2   electronics   BeagleBone socket
BeagleBone   Mouser   595-BEAGLEBONE-000   USD 90   EUR 75
   1   electronics   ethernet interface


### ebay
patch cable SFTP CAT5e 3m shielded 26awg   ebay   patch-cable-generic   USD 2 http://ebay.com   EUR 1.8 http://ebay.co.uk
   11   electronics   sensor, control, and stepper wiring, e-stop
soleniod air valve, 24V, M5, NC   ebay   solenoid-valve-generic   USD 25 http://ebay.com   EUR 20 http://ebay.co.uk
   1   air-assist   compressed air switch valve


### ColeTech
laser power supply (specify 220V or 110V)   ColeTech   100WPowerSupply   USD 600 http://www.cncoletech.com/Laser%20power%20supply.html   EUR 500 http://www.cncoletech.com/Laser%20power%20supply.html
   1   optics-laser   main laser
laser tube   ColeTech   100WLongLifeLaserTube   USD 1200 http://www.cncoletech.com/Laser%20tuber%20long%20life.html   EUR 1000 http://www.cncoletech.com/Laser%20tuber%20long%20life.html
   1   optics-laser   main laser
water chiller (specify 220V or 110V)   ColeTech   WaterChiller   USD 400 http://www.cncoletech.com/Laser%20Water%20Chiller.html   EUR 400 http://www.cncoletech.com/Laser%20Water%20Chiller.html
   1   optics-laser   main laser


### GeckoDrive
GeckoDrive G203V   GeckoDrive   G203V   USD 147 http://www.geckodrive.com/geckodrive-step-motor-drives/g203v.html   EUR 147 www.charter-controls.com/index.php?TASK=search_products&searchStr=11003099
   2   electronics   x/y-drive


### Nanotec
NEMA 17 Stepper   Nanotec   ST4118M1206-A   EUR 27 http://en.nanotec.com/steppermotor_st4118.html
   1   electronics   x-drive
NEMA 23 Stepper + rear shaft   Nanotec   ST5918M3008-B   EUR 42 http://en.nanotec.com/steppermotor_st5918.html
   1   electronics   y-drive


### LinEngineering
NEMA 17 Stepper   LinEngineering   WO-4118S-01F   USD 53 http://www.linengineeringstore.com/products/product_detail.aspx?proID=2
   1   electronics   x-drive
NEMA 23 Stepper + rear shaft   LinEngineering   WO-5718M-02ED   USD 78 http://www.linengineeringstore.com/products/product_detail.aspx?proID=3
   1   electronics   y-drive
"""