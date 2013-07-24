# -*- coding: utf-8 -*-

"""Add example Bom."""

import logging as log
from google.appengine.ext import ndb

from boilerplate.lib.basehandler import BaseHandler
from boilerplate.lib.basehandler import user_required

from web.models import Bom, Part, AuthWriterError


# logging system
log.basicConfig(level=log.DEBUG)
# debug, info, warn, error, fatal, basicConfig



class BomExample(BaseHandler):
    @user_required
    def get(self):
        """Add new test BOM from file.

        Parsed BOM format:
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
        try:
            from web.bomfu_parser import parse
            bom_parsed = parse(example_simple)
            # bom_parsed = parse(example)
        except bomfu_parser.ParseError as ex:
            self.add_message("%s" % ex, 'error')

        try:
            bom = Bom.new('')
            bom.name = "lasersaur-" + str(bom.public_id)
            bom.put(self.user_id, makeowner=True)

            for p in bom_parsed:
                part = bom.new_part(p[0])
                part.quantity_units = p[1]
                part.part_group = p[2]
                part.note_list = p[3]
                part.designator_list = p[4]
                for manufacturer in p[5]:
                    part.manufacturer_names.append(manufacturer[0])
                    part.manufacturer_partnums.append(manufacturer[1])
                for supplier in p[6]:
                    part.supplier_names.append(supplier[0])
                    part.supplier_ordernums.append(supplier[1])
                    part.supplier_packagecounts.append(supplier[2])
                    part.supplier_currencies.append(supplier[3])
                    part.supplier_countries.append(supplier[4])
                    part.supplier_prices.append(supplier[5])
                    part.supplier_urls.append(supplier[6])
                for usage in p[7]:
                    part.subsystem_quantities.append(usage[0])
                    part.subsystem_names.append(usage[1])
                    part.subsystem_specificuses.append(usage[2])
                part.put(self.user_id)
        except AuthWriterError as ex:
            self.add_message("%s" % ex, 'error')

        self.redirect(self.uri_for('bom-edit', public_id=bom.public_id))



example_simple = """
MechParts Aluminum   
   $ NortdLabs   la-mpk   USD 245.00
   $ NortdLabs   la-mpk   EUR 225.00
   1   electronics   2x door sensor mounts
   0   y-drive   2x shaft bearing mounts, 1x limit sensor mount, 1x motor mount
   0   x-cart   2x roller/optics mounts
   0   x-drive   1x motor mount, 2x limit sensor mounts
   0   optics-laser   4x laser tube mounts

Mount Panels   
   $ NortdLabs   la-mpan   USD 75.00
   $ NortdLabs   la-mpan   EUR 70.00
   1   electronics   DriveBoard and 24V/5V PSU mount
   0   electronics   C14 power socket mount
   0   frame-panels   rear bottom right

NEMA 17 Stepper   
   $ Nanotec   ST4118M1206-A   EUR 27.00
   1   electronics   x-drive

NEMA 17 Stepper   
   $ LinEngineering   WO-4118S-01F   USD 53.00
   1   electronics   x-drive

NEMA 23 Stepper + rear shaft   
   $ Nanotec   ST5918M3008-B   EUR 42.00
   1   electronics   y-drive

NEMA 23 Stepper + rear shaft   
   $ LinEngineering   WO-5718M-02ED   USD 78.00
   1   electronics   y-drive

RJ45-port, shielded   
   $ Mouser   GDLX-S-88K   USD 1.00
   $ Mouser   GDLX-S-88K   EUR 1.00
   15   electronics   DriveBoard component

air tube, ODxID 6x4mm, 10m   
   $ Misumi   PUT6-10-CB   USD 12.00
   $ Misumi   PUT6-10-CB   EUR 10.00
   1   air-assist   entry panel to laser head

aluminum bracket extrusion   
   $ Misumi   HFLBS5-650   USD 2.00
   $ Misumi   HFLBS5-650   EUR 2.00
   1   x-drive   cable carrier base

angle bracket, double   
   $ Misumi   HBLFSD5   USD 2.30
   $ Misumi   HBLFSD5   EUR 1.95
   27   frame-outer   25x side columns, 2x side edges
   4   frame-door   door connections
   1   optics-laser   mirror1
   6   extra   extra

angle bracket, double, heavy   
   $ Misumi   HBLFSDW5   USD 3.15
   $ Misumi   HBLFSDW5   EUR 2.10
   4   frame-gantry   gantry frame corners
   2   optics-laser   laser mounts

angle bracket, double, light   
   $ Misumi   HBLSD5   USD 1.32
   $ Misumi   HBLSD5   EUR 0.88
   2   y-drive   pulley
   2   extra   extra

laser power supply (specify 220V or 110V)   
   $ ColeTech   100WPowerSupply   USD 600.00   http://www.cncoletech.com/Laser%20power%20supply.html
   $ ColeTech   100WPowerSupply   EUR 500.00   http://www.cncoletech.com/Laser%20power%20supply.html
   1   optics-laser   main laser

laser tube   
   $ ColeTech   100WLongLifeLaserTube   USD 1200.00   http://www.cncoletech.com/Laser%20tuber%20long%20life.html
   $ ColeTech   100WLongLifeLaserTube   EUR 1000.00   http://www.cncoletech.com/Laser%20tuber%20long%20life.html
   1   optics-laser   main laser

lens tube 1"   
   $ ThorLabs   SM1M10   USD 16.00
   $ ThorLabs   SM1M10   EUR 13.00
   1   optics-laser   flying optics, head

limit switch   
   $ Mouser   D2SW-3L2MS   USD 5.20
   $ Mouser   D2SW-3L2MS   EUR 5.00
   6   electronics   4x limit for x/y-axis, 2x door
   1   extra   extra

lock ring, outer   
   $ ThorLabs   SM1NT   USD 8.00
   $ ThorLabs   SM1NT   EUR 7.00
   2   optics-laser   laser head, nozzle

"""


example = """
Atmega328P, PDIP   
   $ Mouser   ATMEGA328P-PU   USD 4.50
   $ Mouser   ATMEGA328P-PU   EUR 4.50
   1   electronics   DriveBoard component

DIP-28 socket   
   $ Mouser   4828-3004-CP   USD 0.40
   $ Mouser   4828-3004-CP   EUR 0.30
   1   electronics   DriveBoard component

GeckoDrive G203V   
   $ GeckoDrive   G203V   USD 147.00   http://www.geckodrive.com/geckodrive-step-motor-drives/g203v.html
   $ GeckoDrive   G203V   EUR 147.00   www.charter-controls.com/index.php?TASK=search_products&searchStr=11003099
   2   electronics   x/y-drive

Lasersaur DriveBoard PCB   
   $ NortdLabs   la-dbp   USD 98.00
   $ NortdLabs   la-dbp   EUR 93.00
   1   electronics   controller board

Lasersaur Nozzle   
   $ NortdLabs   la-noz   USD 110.00
   $ NortdLabs   la-noz   EUR 102.00
   1   optics-laser   laser head

LasersaurBBB (BeagleBoneBlack, Wifi, configured)   
   $ NortdLabs   la-bbb   USD 99.00
   $ NortdLabs   la-bbb   EUR 94.00
   1   electronics   controller board

Lens and Mirrors Pack   
   $ NortdLabs   la-lmp   USD 295.00
   $ NortdLabs   la-lmp   EUR 275.00
   1   optics-laser   laser beam delivery

MechParts Aluminum   
   $ NortdLabs   la-mpk   USD 245.00
   $ NortdLabs   la-mpk   EUR 225.00
   1   electronics   2x door sensor mounts
   0   y-drive   2x shaft bearing mounts, 1x limit sensor mount, 1x motor mount
   0   x-cart   2x roller/optics mounts
   0   x-drive   1x motor mount, 2x limit sensor mounts
   0   optics-laser   4x laser tube mounts

Mount Panels   
   $ NortdLabs   la-mpan   USD 75.00
   $ NortdLabs   la-mpan   EUR 70.00
   1   electronics   DriveBoard and 24V/5V PSU mount
   0   electronics   C14 power socket mount
   0   frame-panels   rear bottom right

NEMA 17 Stepper   
   $ Nanotec   ST4118M1206-A   EUR 27.00   http://en.nanotec.com/steppermotor_st4118.html
   1   electronics   x-drive

NEMA 17 Stepper   
   $ LinEngineering   WO-4118S-01F   USD 53.00   http://www.linengineeringstore.com/products/product_detail.aspx?proID=2
   1   electronics   x-drive

NEMA 23 Stepper + rear shaft   
   $ Nanotec   ST5918M3008-B   EUR 42.00   http://en.nanotec.com/steppermotor_st5918.html
   1   electronics   y-drive

NEMA 23 Stepper + rear shaft   
   $ LinEngineering   WO-5718M-02ED   USD 78.00   http://www.linengineeringstore.com/products/product_detail.aspx?proID=3
   1   electronics   y-drive

RJ45-port, shielded   
   $ Mouser   GDLX-S-88K   USD 1.00
   $ Mouser   GDLX-S-88K   EUR 1.00
   15   electronics   DriveBoard component

air tube, ODxID 6x4mm, 10m   
   $ Misumi   PUT6-10-CB   USD 12.00
   $ Misumi   PUT6-10-CB   EUR 10.00
   1   air-assist   entry panel to laser head

aluminum bracket extrusion   
   $ Misumi   HFLBS5-650   USD 2.00
   $ Misumi   HFLBS5-650   EUR 2.00
   1   x-drive   cable carrier base

angle bracket, double   
   $ Misumi   HBLFSD5   USD 2.30
   $ Misumi   HBLFSD5   EUR 1.95
   27   frame-outer   25x side columns, 2x side edges
   4   frame-door   door connections
   1   optics-laser   mirror1
   6   extra   extra

angle bracket, double, heavy   
   $ Misumi   HBLFSDW5   USD 3.15
   $ Misumi   HBLFSDW5   EUR 2.10
   4   frame-gantry   gantry frame corners
   2   optics-laser   laser mounts

angle bracket, double, light   
   $ Misumi   HBLSD5   USD 1.32
   $ Misumi   HBLSD5   EUR 0.88
   2   y-drive   pulley
   2   extra   extra

angle bracket, single   
   $ Misumi   HBLFSN5   USD 0.75
   $ Misumi   HBLFSN5   EUR 0.63
   20   frame-outer   2x front columns, 4x separation columns, 10x rear box
   8   frame-door   door connections
   1   optics-laser   mirror2
   10   extra   extra

angle bracket, single, black   
   $ Misumi   HBLFSNB5   USD 1.98
   $ Misumi   HBLFSNB5   EUR 1.32
   6   frame-outer   bottom cross
   20   frame-table   table frame
   2   extra   extra

angle bracket, single, light   
   $ Misumi   HBLSS5   USD 1.02
   $ Misumi   HBLSS5   EUR 0.70
   4   x-cart   extrusion connection
   2   extra   extra

angle bracket, single, long, narrow   
   $ Misumi   HBLTSW5   USD 3.39
   $ Misumi   HBLTSW5   EUR 2.26
   1   y-drive   motor

ball bearing 5x19x6mm   
   $ Misumi   B635ZZ   USD 5.18
   $ Misumi   B635ZZ   EUR 1.40
   4   y-drive   idler
   2   x-drive   idler

ball bearing 6x19x6mm   
   $ Misumi   B626ZZ   USD 2.53
   $ Misumi   B626ZZ   EUR 1.70
   2   y-drive   2x shaft mount

ball bearing roller 4x13x5mm   
   $ Misumi   EB13   USD 11.28
   $ Misumi   EB13   EUR 10.10
   8   y-cart   roller
   6   x-cart   roller
   1   extra   extra

cable carrier, 20 links   
   $ Misumi   MHPKS101-19-20-S   USD 19.88
   $ Misumi   MHPKS101-19-20-S   EUR 19.30
   2   x-drive   gas assist

cable carrier, 23 links   
   $ Misumi   MHPUS102-19-23-S   USD 29.57
   $ Misumi   MHPUS102-19-23-S   EUR 29.00
   1   y-drive   life line

cable tie, 2.5x100mm, white   
   $ Mouser   BT1M-M10   USD 0.06
   $ Mouser   BT1M-M10   EUR 0.05
   4   y-drive   belt to cart
   4   x-drive   belt to cart
   16   optics-laser   cable and hose to laser tube

ceramic cap, 100nF   
   $ Mouser   K104M15X7RF53L2   USD 0.10
   $ Mouser   K104M15X7RF53L2   EUR 0.10
   10   electronics   DriveBoard component

ceramic cap, 22pF   
   $ Mouser   K220J15C0GF53L2   USD 0.30
   $ Mouser   K220J15C0GF53L2   EUR 0.30
   2   electronics   DriveBoard component

cleaning swabs   
   $ ThorLabs   CTA10   USD 5.00
   $ ThorLabs   CTA10   EUR 4.00
   1   optics-laser   optics cleaning

cleaning tissues   
   $ ThorLabs   MC-5   USD 10.00
   $ ThorLabs   MC-5   EUR 9.00
   1   optics-laser   optics cleaning

crystal 16MHz   
   $ Mouser   FOXSLF/160-20   USD 0.50
   $ Mouser   FOXSLF/160-20   EUR 0.50
   1   electronics   DriveBoard component

diode   
   $ Mouser   512-1N4004   USD 0.10
   $ Mouser   512-1N4004   EUR 0.10
   2   electronics   DriveBoard component

e-stop SPST block   
   $ Mouser   642-A0150B   USD 8.00
   $ Mouser   642-A0150B   EUR 6.00
   1   electronics   e-stop

e-stop button 40mm   
   $ Mouser   642-A01ESSP3   USD 21.00
   $ Mouser   642-A01ESSP3   EUR 11.00
   1   electronics   e-stop

electrolytic cap, 1000uF   
   $ Mouser   EEU-HD1H102   USD 1.60
   $ Mouser   EEU-HD1H102   EUR 1.30
   1   electronics   DriveBoard component

electrolytic cap, 100uF   
   $ Mouser   EEU-HD1H101B   USD 0.50
   $ Mouser   EEU-HD1H101B   EUR 0.40
   1   electronics   DriveBoard component

electrolytic cap, 47uF   
   $ Mouser   EEU-HD1H470B   USD 0.40
   $ Mouser   EEU-HD1H470B   EUR 0.30
   1   electronics   DriveBoard component

ethernet entry module   
   $ Mouser   PX0833/E   USD 7.85
   $ Mouser   PX0833/E   EUR 6.15
   1   electronics   ethernet panel mount

extrusion 2020, 1564mm   
   $ Misumi   HFS5-2020-1564   USD 8.91
   $ Misumi   HFS5-2020-1564   EUR 7.40
   1   frame-door   door front bottom

extrusion 2020, 60mm, 45deg   
   $ Misumi   HFS5-2020-60-LAT45   USD 6.90
   $ Misumi   HFS5-2020-60-LAT45   EUR 6.50
   1   optics-laser   mirror2

extrusion 2020, 80mm   
   $ Misumi   HFS5-2020-80   USD 3.00
   $ Misumi   HFS5-2020-80   EUR 2.50
   2   frame-door   door front

extrusion 2040, 100mm   
   $ Misumi   HFS5-2040-100   USD 4.60
   $ Misumi   HFS5-2040-100   EUR 4.00
   1   frame-outer   rear middle top column

extrusion 2040, 1130mm   
   $ Misumi   HFS5-2040-1130   USD 12.00
   $ Misumi   HFS5-2040-1130   EUR 15.00
   2   frame-outer   frame side bottom

extrusion 2040, 120mm, black   
   $ Misumi   HFSB5-2040-120   USD 5.00
   $ Misumi   HFSB5-2040-120   EUR 4.60
   2   frame-table   table columns

extrusion 2040, 124mm, + mount holes   
   $ Misumi   HFS5-2040-124-Z5-YA43   USD 7.66
   $ Misumi   HFS5-2040-124-Z5-YA43   EUR 5.00
   1   x-cart   cart-bar

extrusion 2040, 1260mm, black   
   $ Misumi   HFSB5-2040-1260   USD 21.00
   $ Misumi   HFSB5-2040-1260   EUR 17.66
   5   frame-table   table wide

extrusion 2040, 140mm, + mount holes   
   $ Misumi   HFS5-2040-140-Z5-YA20-YB94   USD 12.50
   $ Misumi   HFS5-2040-140-Z5-YA20-YB94   EUR 8.00
   1   y-cart   cart-bar

extrusion 2040, 1564mm   
   $ Misumi   HFS5-2040-1564   USD 17.00
   $ Misumi   HFS5-2040-1564   EUR 14.00
   1   frame-door   door front

extrusion 2040, 1620mm   
   $ Misumi   HFS5-2040-1620   USD 16.50
   $ Misumi   HFS5-2040-1620   EUR 17.00
   4   frame-outer   frame front, middle, 2x back

extrusion 2040, 190mm   
   $ Misumi   HFS5-2040-190   USD 3.00
   $ Misumi   HFS5-2040-190   EUR 3.00
   4   frame-outer   2x rear middle top, bottom, 2x laser psu mount

extrusion 2040, 320mm   
   $ Misumi   HFS5-2040-320   USD 3.50
   $ Misumi   HFS5-2040-320   EUR 3.00
   1   frame-outer   back middle

extrusion 2040, 62mm, + mount holes   
   $ Misumi   HFS5-2040-62-Z5-YA10   USD 7.66
   $ Misumi   HFS5-2040-62-Z5-YA10   EUR 5.00
   1   optics-laser   mirror1

extrusion 2040, 750mm, black   
   $ Misumi   HFSB5-2040-750   USD 12.50
   $ Misumi   HFSB5-2040-750   EUR 8.00
   1   frame-outer   bottom cross right

extrusion 2040, 75mm   
   $ Misumi   HFS5-2040-75-LTP   USD 6.50
   $ Misumi   HFS5-2040-75-LTP   EUR 7.00
   1   x-cart   cart-bar

extrusion 2040, 790mm, balck   
   $ Misumi   HFSB5-2040-790   USD 13.20
   $ Misumi   HFSB5-2040-790   EUR 8.00
   1   frame-outer   bottom cross left

extrusion 2040, 80mm   
   $ Misumi   HFS5-2040-80   USD 2.60
   $ Misumi   HFS5-2040-80   EUR 2.90
   1   frame-door   door front

extrusion 2040, 80mm, 45deg   
   $ Misumi   HFS5-2040-80-LAT45   USD 6.70
   $ Misumi   HFS5-2040-80-LAT45   EUR 3.80
   1   optics-laser   mirror1

extrusion 2040, 830mm   
   $ Misumi   HFS5-2040-830   USD 9.00
   $ Misumi   HFS5-2040-830   EUR 8.00
   3   frame-door   door top

extrusion 2040, 858mm, black   
   $ Misumi   HFSB5-2040-858   USD 14.40
   $ Misumi   HFSB5-2040-858   EUR 12.08
   2   frame-table   table short

extrusion 2040, 860mm   
   $ Misumi   HFS5-2040-860   USD 9.30
   $ Misumi   HFS5-2040-860   EUR 8.00
   1   frame-outer   cable carrier mount
   1   extra   extra

extrusion 2040, 860mm, black   
   $ Misumi   HFSB5-2040-860   USD 14.36
   $ Misumi   HFSB5-2040-860   EUR 8.00
   1   frame-outer   bottom cross middle

extrusion 2040, 96mm, + mount holes   
   $ Misumi   HFS5-2040-96-Z5-YA46-YB76   USD 12.50
   $ Misumi   HFS5-2040-96-Z5-YA46-YB76   EUR 8.00
   1   y-cart   cart-bar

extrusion 2080, 70mm   
   $ Misumi   HFS5-2080-70-LTP   USD 13.00
   $ Misumi   HFS5-2080-70-LTP   EUR 16.00
   2   y-cart   cart-bar

extrusion 4040, 100mm   
   $ Misumi   HFS5-4040-100   USD 4.60
   $ Misumi   HFS5-4040-100   EUR 4.00
   2   frame-outer   corner top column

extrusion 4040, 1130mm   
   $ Misumi   HFS5-4040-1130   USD 17.40
   $ Misumi   HFS5-4040-1130   EUR 15.00
   2   frame-outer   frame side top

extrusion 4040, 120mm   
   $ Misumi   HFS5-4040-120   USD 4.60
   $ Misumi   HFS5-4040-120   EUR 4.00
   6   frame-outer   frame front, middle, corner column

extrusion 4040, 120mm, black   
   $ Misumi   HFSB5-4040-120   USD 8.00
   $ Misumi   HFSB5-4040-120   EUR 8.60
   2   frame-table   table columns

extrusion 4040, 1426mm   
   $ Misumi   HFS5-4040-1426   USD 22.00
   $ Misumi   HFS5-4040-1426   EUR 18.00
   1   y-cart   cart-bar

extrusion 4040, 1564mm   
   $ Misumi   HFS5-4040-1564   USD 24.00
   $ Misumi   HFS5-4040-1564   EUR 20.00
   1   frame-door   door rear

extrusion 4040, 1620mm   
   $ Misumi   HFS5-4040-1620   USD 25.00
   $ Misumi   HFS5-4040-1620   EUR 21.00
   1   frame-outer   frame middle sep

extrusion 4040, 190mm   
   $ Misumi   HFS5-4040-190   USD 4.60
   $ Misumi   HFS5-4040-190   EUR 5.00
   1   frame-outer   rear side

extrusion 4040, 360mm   
   $ Misumi   HFS5-4040-360   USD 5.60
   $ Misumi   HFS5-4040-360   EUR 7.00
   2   frame-outer   corner rear

extrusion 4040, 860mm   
   $ Misumi   HFS5-4040-860   USD 13.30
   $ Misumi   HFS5-4040-860   EUR 10.92
   2   frame-gantry   y-rails, left and right
   1   extra   extra

extrusion 4080, 100mm   
   $ Misumi   HFS5-4080-100   USD 9.40
   $ Misumi   HFS5-4080-100   EUR 9.00
   2   frame-outer   side

extrusion 4080, 1620mm   
   $ Misumi   HFS5-4080-1620   USD 56.00
   $ Misumi   HFS5-4080-1620   EUR 47.00
   2   frame-gantry   gantry frame, rear and front

extrusion 4080, 940mm   
   $ Misumi   HFS5-4080-940   USD 32.50
   $ Misumi   HFS5-4080-940   EUR 27.00
   2   frame-gantry   gantry frame, left and right

gas spring   
   $ Misumi   FGSS22150B   USD 23.88
   $ Misumi   FGSS22150B   EUR 19.00
   2   frame-door   door

headers, 2.54mm, 44ps   
   $ Mouser   10-89-7442   USD 3.70
   $ Mouser   10-89-7442   EUR 3.20
   2   electronics   BeagleBone socket

headers, 5.08mm, 6pos   
   $ Mouser   10-08-1061   USD 1.60
   $ Mouser   10-08-1061   EUR 1.40
   6   electronics   Gecko socket

heat shrink tubing set   
   $ Mouser   562-Q2ZQK101-180   USD 20.00
   $ Mouser   562-Q2ZQK101-180   EUR 16.00
   1   electronics   cable to sensor, stepper, laser

hinges   
   $ Misumi   HHPSN5   USD 3.80
   $ Misumi   HHPSN5   EUR 3.60
   3   frame-door   door

laser power supply (specify 220V or 110V)   
   $ ColeTech   100WPowerSupply   USD 600.00   http://www.cncoletech.com/Laser%20power%20supply.html
   $ ColeTech   100WPowerSupply   EUR 500.00   http://www.cncoletech.com/Laser%20power%20supply.html
   1   optics-laser   main laser

laser tube   
   $ ColeTech   100WLongLifeLaserTube   USD 1200.00   http://www.cncoletech.com/Laser%20tuber%20long%20life.html
   $ ColeTech   100WLongLifeLaserTube   EUR 1000.00   http://www.cncoletech.com/Laser%20tuber%20long%20life.html
   1   optics-laser   main laser

lens tube 1"   
   $ ThorLabs   SM1M10   USD 16.00
   $ ThorLabs   SM1M10   EUR 13.00
   1   optics-laser   flying optics, head

limit switch   
   $ Mouser   D2SW-3L2MS   USD 5.20
   $ Mouser   D2SW-3L2MS   EUR 5.00
   6   electronics   4x limit for x/y-axis, 2x door
   1   extra   extra

lock ring, outer   
   $ ThorLabs   SM1NT   USD 8.00
   $ ThorLabs   SM1NT   EUR 7.00
   2   optics-laser   laser head, nozzle

logic gate, 3x3 AND, DIP14   
   $ Mouser   MC74AC11NG   USD 0.50
   $ Mouser   MC74AC11NG   EUR 0.50
   1   electronics   DriveBoard component

logic gate, 3x3 NAND, DIP14   
   $ Mouser   MC74AC10NG   USD 0.50
   $ Mouser   MC74AC10NG   EUR 0.50
   1   electronics   DriveBoard component

metal sheet 1166x356x0.8mm   
   $ Misumi   PDSPHC4H-1166-356-0.8-F1110-G340-N5-UN10-XC8-YC8   USD 44.00
   $ Misumi   PDSPHC4H-1166-356-0.8-F1110-G340-N5-UN10-XC8-YC8   EUR 41.00
   1   frame-panels   left side

metal sheet 1166x847x0.8mm   
   $ Misumi   PDSPHC4H-1166-847-0.8-F1150-G790-N5-UN10-XC8-YC9   USD 58.00
   $ Misumi   PDSPHC4H-1166-847-0.8-F1150-G790-N5-UN10-XC8-YC9   EUR 54.00
   2   frame-panels   bottom

metal sheet 247x216x0.8mm   
   $ Misumi   PDSPHC4H-247-216-0.8-F190-G200-N5-UN10-XC9-YC8   USD 25.00
   $ Misumi   PDSPHC4H-247-216-0.8-F190-G200-N5-UN10-XC9-YC8   EUR 24.00
   1   frame-panels   right side

metal sheet 847x200x0.8mm   
   $ Misumi   PDSPHC4H-847-200-0.8-F790-G180-N5-UN10-XC48-YC8   USD 35.00
   $ Misumi   PDSPHC4H-847-200-0.8-F790-G180-N5-UN10-XC48-YC8   EUR 33.00
   2   frame-panels   front

metal sheet 847x268x0.8mm   
   $ Misumi   PDSPHC4H-847-268-0.8-F790-G250-N5-UN10-XC48-YC8   USD 35.00
   $ Misumi   PDSPHC4H-847-268-0.8-F790-G250-N5-UN10-XC48-YC8   EUR 33.00
   2   frame-panels   rear top

metal sheet 847x356x0.8mm   
   $ Misumi   PDSPHC4H-847-356-0.8-F790-G340-N5-UN10-XC48-YC8   USD 38.00
   $ Misumi   PDSPHC4H-847-356-0.8-F790-G340-N5-UN10-XC48-YC8   EUR 36.00
   2   frame-panels   rear

metal sheet 917x356x0.8mm   
   $ Misumi   PDSPHC4H-917-356-0.8-F900-G340-N5-UN10-XC8-YC8   USD 40.00
   $ Misumi   PDSPHC4H-917-356-0.8-F900-G340-N5-UN10-XC8-YC8   EUR 38.00
   1   frame-panels   right side

mirror mount   
   $ ThorLabs   KM100   USD 40.00
   $ ThorLabs   KM100   EUR 35.50
   3   optics-laser   flying optics, 1, 2, 3

nut DIN934-like, M3   
   $ Misumi   LBNR3   USD 0.08
   $ Misumi   LBNR3   EUR 0.28
   1   x-drive   1x cable carrier
   6   electronics   2x power entry module, 4x driveboard
   8   extra   extra

nut DIN985-like, lock, M4, 100 pack   
   $ Misumi   PACK-UNUT4   USD 14.60
   $ Misumi   PACK-UNUT4   EUR 14.60
   1   y-cart   16x roller
   0   y-drive   4x bearing clamps
   0   x-cart   11x roller
   0   optics-laser   4x laser tube mount

nut DIN985-like, lock, M5, 100 pack   
   $ Misumi   PACK-UNUT5   USD 15.00
   $ Misumi   PACK-UNUT5   EUR 15.00
   1   y-drive   6x motor mount, 4x pulley mount, 4x limit switch
   0   x-cart   4x custom part connection
   0   x-drive   1x motor mount
   0   optics-laser   8x laser mount

nut T-slot, post, M3   
   $ Misumi   HNTP5-3   USD 0.56
   $ Misumi   HNTP5-3   EUR 0.50
   2   x-drive   cable carrier
   1   air-assist   e-valve mount
   12   electronics   12x magnetic limit switch

nut T-slot, post, M5, lock   
   $ Misumi   HNTPZ5-5   USD 0.69
   $ Misumi   HNTPZ5-5   EUR 0.60
   48   frame-gantry   16x planar brackets, 32x angle brackets
   190   frame-outer   190x frame connections
   138   frame-panels   22x door top, 16x door front, 100x metal sheets
   80   frame-door   32x brackets, 4x gas spring, 12x hinge, 4x door handle, 12x door hinge, 4x gas spring, 8x door slit cover, 4x door switch
   4   electronics   4x panel mount
   24   frame-table   angle brackets
   4   y-cart   4x cart-bar
   20   y-drive   6x pulley/idler, 2x motor, 2x limit switch, 4x belt, 4x shaft mount, 2x cable carrier
   4   x-cart   angle connection
   10   x-drive   1x idler, 1x motor, 2x cable carrier base, 2x belt, 4x limit switch
   20   optics-laser   6x mirror1, 2x mirror2, 8x laser mount, 4x laser PSU
   60   extra   extra

nut T-slot, pre, M4   
   $ Misumi   HNTE5-4   USD 0.46
   $ Misumi   HNTE5-4   EUR 0.45
   8   y-cart   8x rollers
   2   x-cart   roller
   3   optics-laser   mirrors
   10   extra   extra

one-touch coupling, 6mm, M5   
   $ Misumi   MSELL6-M5   USD 3.00
   $ Misumi   MSELL6-M5   EUR 3.00
   3   air-assist   1x nozzle coupling, 2x e-valve coupling

one-touch panel-mount, 6mm   
   $ Misumi   MSBUL6   USD 3.00
   $ Misumi   MSBUL6   EUR 3.00
   1   air-assist   entry panel

panel rubber seal 6m   
   $ Misumi   HSCP3H-B-6   USD 24.00
   $ Misumi   HSCP3H-B-6   EUR 20.00
   1   frame-outer   seal for separation panels
   0   frame-outer   seal for entry panel

patch cable SFTP CAT5e 3m shielded 26awg   
   $ ebay   patch-cable-generic   USD 2.00   http://ebay.com
   $ ebay   patch-cable-generic   EUR 1.80   http://ebay.co.uk
   11   electronics   sensor, control, and stepper wiring, e-stop

planar bracket, double   
   $ Misumi   SHPTSD5   USD 1.75
   $ Misumi   SHPTSD5   EUR 1.20
   4   frame-gantry   gantry frame y-rails
   2   frame-outer   middle column, separation

platic handles   
   $ Misumi   UPCN19-B-36   USD 5.80
   $ Misumi   UPCN19-B-36   EUR 4.80
   2   frame-door   door

polycarbonate sheet 170x130x3mm   
   $ Misumi   PCTBA-170-130-3   USD 7.00
   $ Misumi   PCTBA-170-130-3   EUR 5.00
   2   frame-outer   compartment separation, sides, bottom

polycarbonate sheet 600x130x3mm   
   $ Misumi   PCTBA-600-130-3   USD 21.00
   $ Misumi   PCTBA-600-130-3   EUR 18.00
   2   frame-outer   compartment separation, bottom

polycarbonate sheet 800x110x3mm   
   $ Misumi   PCTBA-800-110-3   USD 27.00
   $ Misumi   PCTBA-800-110-3   EUR 22.00
   2   frame-outer   compartment separation, top

polycarbonate sheet 807x60x3mm   
   $ Misumi   PCTBA-807-60-3   USD 14.00
   $ Misumi   PCTBA-807-60-3   EUR 11.00
   2   frame-door   door slit cover

polycarbonate sheet 847x156x3mm   
   $ Misumi   PCTBA-847-156-3   USD 29.00
   $ Misumi   PCTBA-847-156-3   EUR 24.00
   2   frame-panels   door cover front

polycarbonate sheet 892x847x3mm   
   $ Misumi   PCTBA-892-847-3   USD 135.00
   $ Misumi   PCTBA-892-847-3   EUR 100.00
   2   frame-panels   door cover top

power cable   
   $ Mouser   397002-01   USD 7.00
   2   electronics   1x power cable, 1x wiring internals

power cable   
   $ Mouser   364002-D01   EUR 6.00
   3   electronics   1x power cable, 2x wiring internals

power entry module C-14   
   $ Mouser   161-R30148-E   USD 2.50
   $ Mouser   161-R30148-E   EUR 2.00
   2   electronics   1x DriveBoard entry, 1x DriveBoard2Laser

power entry module C-14, filtered   
   $ Mouser   5110.1033.1   USD 16.00
   $ Mouser   5110.1033.1   EUR 13.00
   1   electronics   1x entry panel

power supply 24V@3.2A   
   $ Mouser   LS75-24   USD 20.00
   $ Mouser   LS75-24   EUR 18.00
   1   electronics   motor power

power supply 5V@12A   
   $ Mouser   LS75-5   USD 20.00
   $ Mouser   LS75-5   EUR 18.00
   1   electronics   logic power

relay solid state, 5Vto280VAC, SPST-NO   
   $ Mouser   PF240D25   USD 22.00
   $ Mouser   PF240D25   EUR 18.00
   1   electronics   DriveBoard component

relays solid state, 5Vto24V   
   $ Mouser   AQY212GH   USD 4.00
   $ Mouser   AQY212GH   EUR 4.00
   2   electronics   DriveBoard component

resistor 10 KOhm   
   $ Mouser   271-10K-RC   USD 0.15
   $ Mouser   271-10K-RC   EUR 0.11
   11   electronics   DriveBoard component (9x input pull-down resistor, 1x voltage divider, 1x driver sensing)
   3   extra   extra

resistor 11.5 KOhm   
   $ Mouser   271-11.5K-RC   USD 0.15
   $ Mouser   271-11.5K-RC   EUR 0.11
   3   electronics   DriveBoard component (1x y-axis motor option 1.4A (Gecko + Nanotec:ST5918M1008-B or LinE:WO-5718M-04ED), 1x x-axis motor option 1.35A  (Gecko + LinE:WO-4118S-04E) )
   10   extra   extra

resistor 12.7 KOhm   
   $ Mouser   271-12.7K-RC   USD 0.15
   1   electronics   DriveBoard component (x-axis motor option 1.5A  (Gecko + LinE:WO-4118S-01) )
   10   extra   extra

resistor 20 KOhm   
   $ Mouser   271-20K-RC   USD 0.15
   $ Mouser   271-20K-RC   EUR 0.11
   2   electronics   DriveBoard component (y-axis motor option 2.1A (Gecko + Nanotec:ST5918M3008-B or LinE:WO-5718M-02ED) )
   1   extra   extra

resistor 360 Ohm   
   $ Mouser   271-360-RC   USD 0.15
   $ Mouser   271-360-RC   EUR 0.11
   2   electronics   DriveBoard component (ssr limit resistor)
   8   extra   extra

resistor 6.49 KOhm   
   $ Mouser   271-6.49K-RC   USD 0.15
   $ Mouser   271-6.49K-RC   EUR 0.11
   2   electronics   DriveBoard component (1x voltage divider, 1x x-axis motor option 0.84A (Gecko + Nanotec:ST4118M1206-A))
   10   extra   extra

rotary shaft with step   
   $ Misumi   SFAC8-692-F24-P6   USD 37.00
   $ Misumi   SFAC8-692-F24-P6   EUR 23.00
   2   y-drive   motor to pulley

rubber tape 0.75"x30mil   
   $ Mouser   2155-3/4x22FT-20rls   USD 5.00
   $ Mouser   2155-3/4x22FT-20rls   EUR 4.00
   1   optics-laser   between laser tube and mounts

safety glasses for 10600nm   
   $ ThorLabs   LG6   USD 130.00
   $ ThorLabs   LG6   EUR 130.00
   1   optics-laser   for user's eyes

screw DIN7984-like, low, M5x16   
   $ Misumi   CBSS5-16   USD 0.50
   $ Misumi   CBSS5-16   EUR 0.50
   4   y-drive   belt attachment
   2   x-drive   belt attachment

screw DIN7991-like, sunk, M5x08   
   $ Misumi   SFB5-8   USD 0.66
   $ Misumi   SFB5-8   EUR 1.10
   12   frame-door   door hinges

screw DIN7991-like, sunk, M5x12   
   $ Misumi   SFB5-12   USD 1.30
   $ Misumi   SFB5-12   EUR 1.30
   2   x-drive   cable carrier base

screw DIN912-like, M2.5x12   
   $ Misumi   CB2.5-12   USD 1.00
   $ Misumi   CB2.5-12   EUR 1.00
   4   x-drive   limit switch
   4   y-drive   limit switch
   4   frame-door   door switch

screw DIN912-like, M3x06   
   $ Misumi   CB3-6   USD 0.13
   $ Misumi   CB3-6   EUR 0.13
   1   x-drive   cable carrier
   28   electronics   4x psu mount, 24x magnetic limit switch
   1   extra   extra

screw DIN912-like, M3x10   
   $ Misumi   CB3-10   USD 0.13
   $ Misumi   CB3-10   EUR 0.13
   5   x-drive   4x motor mount, 1x cable carrier
   2   air-assist   e-valve mount
   4   electronics   4x power entry module
   6   extra   extra

screw DIN912-like, M3x16   
   $ Misumi   CB3-16   USD 0.13
   $ Misumi   CB3-16   EUR 0.13
   6   electronics   2x power entry module, 4x driveboard mount
   6   extra   extra

screw DIN912-like, M3x25   
   $ Misumi   CB3-25   USD 0.13
   $ Misumi   CB3-25   EUR 0.13
   1   air-assist   e-valve mount
   4   extra   extra

screw DIN912-like, M3x30   
   $ Misumi   CB3-30   USD 0.13
   $ Misumi   CB3-30   EUR 0.13
   4   electronics   driveboard mount
   4   extra   extra

screw DIN912-like, M5x08   
   $ Misumi   CB5-8   USD 0.13
   $ Misumi   CB5-8   EUR 0.10
   16   frame-gantry   16x planar bracket
   8   frame-outer   8x planar bracket
   38   frame-panels   22x door top, 16x door front
   8   frame-door   8x door slit cover
   6   y-drive   4x shaft mount, 2x limit switch
   4   x-cart   angle connection
   4   optics-laser   4x laser psu mount
   4   electronics   panel mount
   40   extra   extra

screw DIN912-like, M5x10   
   $ Misumi   CB5-10   USD 0.10
   $ Misumi   CB5-10   EUR 0.08
   32   frame-gantry   32x angle brackets
   190   frame-outer   190x frame connections
   32   frame-door   32x angel brackets
   24   frame-table   angle brackets
   2   y-drive   2x motor
   14   optics-laser   4x mirror1, 2x mirror2, 8x laser mount
   80   extra   extra

screw DIN912-like, M5x12   
   $ Misumi   CB5-12   USD 0.12
   $ Misumi   CB5-12   EUR 0.12
   5   x-drive   1x motor mount, 4x limit switch
   8   frame-door   4x door handle, 4x door switch
   5   extra   extra

screw DIN912-like, M5x16   
   $ Misumi   CB5-16   USD 0.13
   $ Misumi   CB5-16   EUR 0.13
   8   y-drive   4x shaft mount, 4x limit switch
   4   x-cart   custom part connection
   1   x-drive   motor mount
   10   extra   extra

screw DIN912-like, M5x20   
   $ Misumi   CB5-20   USD 0.13
   $ Misumi   CB5-20   EUR 0.13
   4   frame-door   gas spring mount
   4   y-cart   4x cart-bar
   6   y-drive   motor
   10   optics-laser   8x laser mount, 2x mirror1
   8   extra   extra

screw DIN912-like, adhesive, M4x15   
   $ Misumi   LB4-15   USD 0.14
   $ Misumi   LB4-15   EUR 0.14
   4   y-drive   4x bearing clamps
   1   x-cart   roller
   4   extra   extra

screw DIN912-like, adhesive, M4x25   
   $ Misumi   SUSLB4-25   USD 0.50
   $ Misumi   SUSLB4-25   EUR 0.40
   8   y-cart   roller
   5   x-cart   roller
   2   optics-laser   4x laser tube mount
   3   extra   extra

screw DIN912-like, adhesive, M5x25   
   $ Misumi   SUSLB5-25   USD 0.50
   $ Misumi   SUSLB5-25   EUR 0.40
   4   y-cart   4x cart bar
   2   y-drive   2x idler shaft
   2   x-cart   2x cart bar
   1   x-drive   1x idler shaft
   2   extra   extra

screw ISO7380-like, button, M5x06   
   $ Misumi   BCB5-6   USD 0.11
   $ Misumi   BCB5-6   EUR 0.11
   100   frame-panels   100x metal sheets
   2   y-drive   cable carrier
   4   optics-laser   4x laser PSU
   60   extra   extra

screw terminal, 5.08mm, 6pos   
   $ Mouser   1729160   USD 2.00
   $ Mouser   1729160   EUR 2.00
   4   electronics   DriveBoard component

shaft coupling, 6.35 to 8mm   
   $ Misumi   MCKSC20-6.35-8   USD 29.00
   $ Misumi   MCKSC20-6.35-8   EUR 23.40
   2   y-drive   motor to shaft

slide washer   
   $ Misumi   SWSPT25-10-1.0   USD 3.72
   $ Misumi   SWSPT25-10-1.0   EUR 4.60
   2   y-drive   idler
   1   x-drive   idler

soleniod air valve, 24V, M5, NC   
   $ ebay   solenoid-valve-generic   USD 25.00   http://ebay.com
   $ ebay   solenoid-valve-generic   EUR 20.00   http://ebay.co.uk
   1   air-assist   compressed air switch valve

timing belt XL, 350 teeth, 1780mm   
   $ Misumi   TBO-XL025-350   USD 28.00
   $ Misumi   TBO-XL025-350   EUR 24.00
   2   y-drive   drive belt left/right

timing belt XL, 600 teeth, 3050mm   
   $ Misumi   TBO-XL025-600   USD 48.00
   $ Misumi   TBO-XL025-600   EUR 42.00
   1   x-drive   drive belt

timing pulley XL, 12 teeth, bore 5mm   
   $ Misumi   ATP12XL025-B-P5   USD 12.00
   $ Misumi   ATP12XL025-B-P5   EUR 16.00
   1   x-drive   motor pulley

timing pulley XL, 12 teeth, bore 6mm   
   $ Misumi   ATP12XL025-B-P6   USD 12.00
   $ Misumi   ATP12XL025-B-P6   EUR 11.90
   2   y-drive   pulley left/right, set screw

washer DIN125-like, form A, M4   
   $ Misumi   PWF4   USD 0.13
   $ Misumi   PWF4   EUR 0.13
   8   x-cart   roller
   10   extra   extra

washer DIN125-like, form A, M5   
   $ Misumi   PWF5   USD 0.13
   $ Misumi   PWF5   EUR 0.13
   16   frame-gantry   planar brackets
   8   frame-outer   8x planar bracket
   24   frame-door   4x door switch, 20gas spring mount
   38   frame-panels   22x door top, 16x door front
   12   y-drive   8x idler, 6x motor, 2x limit switch
   4   x-cart   custom part connection
   20   x-drive   2x motor mount, 4x idler, 4x limit switch, 10x cable carrier base
   20   extra   extra

washer DIN9021-like, form G, M4, 50 pack   
   $ Misumi   PACK-SPWFN4   USD 9.70
   $ Misumi   PACK-SPWFN4   EUR 9.70
   1   y-cart   8x roller
   0   y-drive   8x bearing
   0   x-cart   2x roller
   0   optics-laser   2x laser tube mount
   0   extra   20x extra

washer DIN9021-like, form G, M5, 20 pack   
   $ Misumi   PACK-SPWFN5   USD 7.60
   $ Misumi   PACK-SPWFN5   EUR 9.60
   3   frame-door   20x gas spring mount
   0   y-drive   4x idler, 4x shaft mount
   0   x-drive   2x idler, 1x motor mount
   0   optics-laser   12x laser mount, laser psu mount
   0   extra   16x extra

washer Schnorr-like, lock, M3   
   $ Misumi   GTS3   USD 0.12
   $ Misumi   GTS3   EUR 0.12
   4   y-drive   4x limit switch
   10   x-drive   3x motor, 4x limit switch, 3x cable carrier
   32   electronics   4x power entry module, 4x psu mount, 24 magnetic limit switch
   1   air-assist   e-valve mount
   12   extra   extra

washer Schnorr-like, lock, M5   
   $ Misumi   GTS5   USD 0.13
   $ Misumi   GTS5   EUR 0.13
   20   extra   extra

water chiller (specify 220V or 110V)   
   $ ColeTech   WaterChiller   USD 400.00   http://www.cncoletech.com/Laser%20Water%20Chiller.html
   $ ColeTech   WaterChiller   EUR 400.00   http://www.cncoletech.com/Laser%20Water%20Chiller.html
   1   optics-laser   main laser

water hose ID 9mm, 10m   
   $ Misumi   AHOS9-10   USD 29.60
   $ Misumi   AHOS9-10   EUR 21.50
   1   optics-laser   chiller to laser to chiller
"""