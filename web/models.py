
import math
import uuid
from collections import OrderedDict

from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.api.images import get_serving_url

from boilerplate.models import User




class AuthError(Exception):
    """Exception raised for ungranted data-access."""
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "AuthError: %s " % self.msg

class AuthReaderError(AuthError):
    """Exception raised for ungranted data-access."""
    def __str__(self):
        return "AuthReaderError: %s " % self.msg

class AuthWriterError(AuthError):
    """Exception raised for ungranted data-access."""
    def __str__(self):
        return "AuthWriterError: %s " % self.msg

class AuthOwnerError(AuthError):
    """Exception raised for ungranted data-access."""
    def __str__(self):
        return "AuthOwnerError: %s " % self.msg



class PublicBomIdCounter(ndb.Model):
  bomid = ndb.IntegerProperty()
  
  @classmethod 
  def getNextId(cls):
    ret = 10001;
    counter = PublicBomIdCounter.query().get()
    if counter:
       ret = counter.bomid = counter.bomid + 1
       counter.put()
    else:
      PublicBomIdCounter(
        bomid = 10001,
      ).put()
    return ret







class Bom(ndb.Model):
    parent_key = ndb.KeyProperty(kind='Bom')
    public_id = ndb.StringProperty(required=True)
    name = ndb.StringProperty()
    uuid = ndb.StringProperty(required=True)
    images = ndb.BlobKeyProperty(repeated=True)
    public = ndb.BooleanProperty(default=False)
    frozen = ndb.BooleanProperty(default=False)
    tag_name = ndb.StringProperty()
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    change_time = ndb.DateTimeProperty(auto_now=True)
    # permissions
    owners = ndb.KeyProperty(repeated=True)
    writers = ndb.KeyProperty(repeated=True)
    readers = ndb.KeyProperty(repeated=True)  # only relevant if not public
    # voting
    like_count_cached = ndb.IntegerProperty()
    watch_count_cached = ndb.IntegerProperty()
    rough_count_cached = ndb.IntegerProperty()


    @classmethod
    def new(cls, name):
        return cls(public_id=str(PublicBomIdCounter.getNextId()),
                   uuid=str(uuid.uuid4()),
                   name=name
                  )


    def put(self, user_id, makeowner=False):
        """Save, check/set permissions.

        To edit a bom the user must have owner or writer permission.
        A bom without permissions set will get "owned" by this user.

        AuthWriteError will get raised if user is not owner or writer.
        """
        if not user_id:
            raise AuthWriterError("invalid user")
        # check writer creds
        user_key = ndb.Key('User', long(user_id))
        if makeowner:
            if user_key not in self.owners:
                self.owners.append(user_key)
                self._put()
        else:
            if user_key in self.owners or user_key in self.writers:
                # permission granted, edit bom
                self._put()
            else:
                # permission declined, do not edit bom
                raise AuthWriterError("user not allowed to write this bom")

    def _put(self):
        if self.frozen:
            raise AuthWriterError("bom is frozen")

        # like_count_cached
        qry = BomLikes.query(ancestor=self.key)
        self.like_count_cached = qry.count()

        # watch_count_cached
        qry = BomWatches.query(ancestor=self.key)
        self.like_count_cached = qry.count()

        # rough_count_cached
        qry = BomRoughs.query(ancestor=self.key)
        self.like_count_cached = qry.count()

        super(Bom, self).put()


    def delete(self):
        # collect all dependant entities
        keys_to_del = []
        keys_to_del.extend(BomLikes.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(BomWatches.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(BomRoughs.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(Part.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(PartGroups.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(Manufacturers.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(Suppliers.query(ancestor=self.key).fetch(keys_only=True))
        keys_to_del.extend(Subsystems.query(ancestor=self.key).fetch(keys_only=True))

        @ndb.transactional()
        def del_in_transaction():
            ndb.delete_multi(keys_to_del)
            self.key.delete()

        del_in_transaction()


    def new_part(self, name):
        return Part.new(self.key, name)


    def get_parts_by_partgroup(self):
        """Return list of Parts by part_group, ordered by name.

        The format is a list of tuples:
        [(group1, [part,part,..]), (group2, [part,part,..]), ]
        """
        by_partgroup = []
        qry = PartGroups.query(ancestor=self.key).order(PartGroups.name)
        for group in qry.iter():
            partlist = []
            q = Part.query(Part.part_group == group.name, ancestor=self.key)\
                    .order(Part.name)
            for part in q.iter():
                partlist.append(part)
            by_partgroup.append((group.name,partlist))
        return by_partgroup


    def get_parts_by_manufacturer(self):
        """Return list of Parts by manufacturer, ordered by name.

        One part can be shown under multiple manufacturers.
        The format is a list of tuples:
        [(manu1, [part,part,..]), (manu2, [part,part,..]), ]
        """
        by_manufacturer = []
        qry = Manufacturers.query(ancestor=self.key).order(Manufacturers.name)
        for manu in qry.iter():
            partlist = []
            q = Part.query(Part.manufacturer_names == manu.name, ancestor=self.key)\
                    .order(Part.name)
            for part in q.iter():
                partlist.append(part)
            by_manufacturer.append((manu.name,partlist))
        return by_manufacturer


    def get_parts_by_supplier(self, currency):
        """Return list of Parts by supplier and currency, ordered by name.

        Returns: OrderedDict, suppliers are keys, values are part lists.
        FIXME: The Part query is a bit inefficient when the parts have
        many alternative suppliers. Too many queries, too many filtered out.
        """
        by_supplier = OrderedDict()
        parts_collected = set()  # probably redundant, not necessary
        qry = Suppliers.query(ancestor=self.key).order(Suppliers.name)
        for supplier in qry.iter():
            partlist = []
            q = Part.query(Part.supplier_names == supplier.name, 
                           Part.supplier_currencies == currency, 
                           ancestor=self.key)\
                    .order(Part.name)
            for part in q.iter():
                # make sure each part is added only once
                if part.uuid not in parts_collected:
                    # check if supplier_name matches currency
                    # looking for one pair where supplier and currency matches
                    got_match = False
                    for i in range(len(part.supplier_names)):
                        if part.supplier_names[i] == supplier.name and \
                        part.supplier_currencies[i] == currency:
                            got_match = True
                            break
                    if got_match:
                        # supplier actually matches currency
                        parts_collected.add(part.uuid)
                        if not by_supplier.has_key(supplier.name):
                            by_supplier[supplier.name] = []
                        by_supplier[supplier.name].append(part)
        return by_supplier


    def get_parts_by_subsystem(self):
        """Return list of Parts by subsystem, ordered by name.

        One part can be shown under multiple subsystems.
        Returns: OrderedDict, suppliers are keys, values are part lists.
        """
        by_subsystem = OrderedDict()
        qry = Subsystems.query(ancestor=self.key).order(Subsystems.name)
        for subsys in qry.iter():
            partlist = []
            q = Part.query(Part.subsystem_names == subsys.name, ancestor=self.key)\
                    .order(Part.name)
            for part in q.iter():
                if not by_subsystem.has_key(subsys.name):
                    by_subsystem[subsys.name] = []
                by_subsystem[subsys.name].append(part)
        return by_subsystem




class BomLikes(ndb.Model):
    user_key = ndb.KeyProperty(kind=User, required=True)
    bom_key = ndb.KeyProperty(kind=Bom, required=True)

    @classmethod
    def new(cls, user_key, bom_key):
        return cls(parent=bom_key, bom_key=bom_key, user_key=user_key)


class BomWatches(ndb.Model):
    user_key = ndb.KeyProperty(kind=User, required=True)
    bom_key = ndb.KeyProperty(kind=Bom, required=True)

    @classmethod
    def new(cls, user_key, bom_key):
        return cls(parent=bom_key, bom_key=bom_key, user_key=user_key)


class BomRoughs(ndb.Model):
    user_key = ndb.KeyProperty(kind=User, required=True)
    bom_key = ndb.KeyProperty(kind=Bom, required=True)

    @classmethod
    def new(cls, user_key, bom_key):
        return cls(parent=bom_key, bom_key=bom_key, user_key=user_key)




class Part(ndb.Model):
    bom_key = ndb.KeyProperty(kind=Bom, required=True)
    name = ndb.StringProperty(required=True)
    uuid = ndb.StringProperty(required=True)
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    change_time = ndb.DateTimeProperty(auto_now=True)
    quantity_cached = ndb.FloatProperty()
    pricepoints_cached = ndb.FloatProperty(repeated=True)  # index matches supplier_names, supplier_currencies
    part_group = ndb.StringProperty()
    quantity_units = ndb.StringProperty()  # None means pieces
    # notes
    note_list = ndb.StringProperty(repeated=True)
    # designators
    designator_list = ndb.StringProperty(repeated=True)
    # manufacturers
    manufacturer_names = ndb.StringProperty(repeated=True)
    manufacturer_partnums = ndb.StringProperty(repeated=True)
    # suppliers
    supplier_names = ndb.StringProperty(repeated=True)
    supplier_ordernums = ndb.StringProperty(repeated=True)
    supplier_packagecounts = ndb.FloatProperty(repeated=True)
    supplier_currencies = ndb.StringProperty(repeated=True)
    supplier_countries = ndb.StringProperty(repeated=True)
    supplier_prices = ndb.FloatProperty(repeated=True)
    supplier_urls = ndb.StringProperty(repeated=True)
    # subsystems
    subsystem_quantities = ndb.FloatProperty(repeated=True)
    subsystem_names = ndb.StringProperty(repeated=True)
    subsystem_specificuses = ndb.StringProperty(repeated=True)

    @classmethod
    def new(cls, bom_key, name):
        return cls(parent=bom_key, 
                   bom_key=bom_key, 
                   name=name,
                   uuid=str(uuid.uuid4())
                  )

    def put(self, user_id):
        """Save and also set refs.

        Refs and creates the following as necessary:
        partgroup, manufacturer, suppier, subsystem

        FIXME: seems to add multiples of:
        PartGroups, Manufacturers, Suppliers, Subsystems
        """

        # quantity_cached
        self.quantity_cached = 0 
        for quantity in self.subsystem_quantities:
            self.quantity_cached += quantity

        # pricepoints_cached
        # one for each supplier
        self.pricepoints_cached = []
        for i in range(len(self.supplier_names)):
            price = self.supplier_prices[i]
            package_count = self.supplier_packagecounts[i]
            if package_count == None or package_count <= 0:
                package_count = 1
            packs_needed = math.ceil(self.quantity_cached/package_count)
            self.pricepoints_cached.append(price * packs_needed)

        items_to_put = []

        # PartGroups
        qry = PartGroups.query(PartGroups.name == self.part_group, ancestor=self.bom_key)
        item = qry.fetch(1)
        if not item:  # non-existent -> create
            newitem = PartGroups.new(self.bom_key, self.part_group)
            items_to_put.append(newitem)

        # Manufacturers
        for name in self.manufacturer_names:
            qry = Manufacturers.query(Manufacturers.name == name, ancestor=self.bom_key)
            item = qry.fetch(1)
            if not item:  # non-existent -> create
                newitem = Manufacturers.new(self.bom_key, name)
                items_to_put.append(newitem)

        # Suppliers
        for name in self.supplier_names:
            qry = Suppliers.query(Suppliers.name == name, ancestor=self.bom_key)
            item = qry.fetch(1)
            if not item:  # non-existent -> create
                newitem = Suppliers.new(self.bom_key, name)
                items_to_put.append(newitem)

        # Subsystems
        for name in self.subsystem_names:
            qry = Subsystems.query(Subsystems.name == name, ancestor=self.bom_key)
            item = qry.fetch(1)
            if not item:  # non-existent -> create
                newitem = Subsystems.new(self.bom_key, name)
                items_to_put.append(newitem)
        
        @ndb.transactional()
        def put_in_transaction():
            ndb.put_multi(items_to_put)
            super(Part, self).put()
            # update bom change_time
            self.bom_key.get().put(user_id)

        # print '>>>>>>>', self, '<<<<<'
        put_in_transaction()


    def delete(self):
        """Delete Part and clean up.

        Deletes partgroup, manufacturer, suppier, subsystem
        if they only refer to this part. Also deletes any ref entities.
        """
        keys_to_del = []

        # PartGroups
        qry = Part.query(Part.part_group == self.part_group, ancestor=self.bom_key)
        if qry.count() == 1:
            # this partgroup is only ref'd by this part -> delete
            q = PartGroups.query(PartGroups.name == self.part_group, ancestor=self.bom_key)
            keys_to_del.extend(q.fetch(keys_only=True))

        # Manufacturers
        for name in self.manufacturer_names:
            qry = Part.query(Part.manufacturer_names == name, ancestor=self.bom_key)
            if qry.count() == 1:
                # this manufacturer is only ref'd by this part -> delete
                q = Manufacturers.query(Manufacturers.name == name, ancestor=self.bom_key)
                keys_to_del.extend(q.fetch(keys_only=True))

        # Suppliers
        for name in self.supplier_names:
            qry = Part.query(Part.supplier_names == name, ancestor=self.bom_key)
            if qry.count() == 1:
                # this supplier is only ref'd by this part -> delete
                q = Suppliers.query(Suppliers.name == name, ancestor=self.bom_key)
                keys_to_del.extend(q.fetch(keys_only=True))

        # Subsystems
        for name in self.subsystem_names:
            qry = Part.query(Part.subsystem_names == name, ancestor=self.bom_key)
            if qry.count() == 1:
                # this subsystem is only ref'd by this part -> delete
                q = Subsystems.query(Subsystems.name == name, ancestor=self.bom_key)
                keys_to_del.extend(q.fetch(keys_only=True))

        @ndb.transactional()
        def del_in_transaction():
            ndb.delete_multi(keys_to_del)                                    
            self.key.delete()
            # update bom change_time
            self.bom_key.get().put()

        del_in_transaction()


    ### Adders & Removers ###########################################
    ################################################################# 
    def add_manufacturer(self, name, part_num):
        try:
            i = self.manufacturer_names.index(name)
        except ValueError:
            i = -1
        if i == -1:  # add
            self.manufacturer_names.append(name)
            self.manufacturer_partnums.append(part_num)
        else:       # update
            self.manufacturer_partnums[i] = part_num

    def remove_manufacturer(self, name):
        i = 0
        while i < len(self.manufacturer_names):
            if self.manufacturer_names[i] == name:
                self.manufacturer_names.pop(i)
                self.manufacturer_partnums.pop(i)
            else:
                i += 1

    def add_supplier(self, name, order_num, package_count, currency, country, price, url):
        try:
            i = self.supplier_names.index(name)
        except ValueError:
            i = -1
        if i == -1:  # add
            self.supplier_names.append(name)
            self.supplier_ordernums.append(order_num)
            self.supplier_packagecounts.append(package_count)
            self.supplier_currencies.append(currency)
            self.supplier_countries.append(country)
            self.supplier_prices.append(price)
            self.supplier_urls.append(url)
        else:       # update
            self.supplier_ordernums[i] = order_num
            self.supplier_packagecounts[i] = package_count
            self.supplier_currencies[i] = currency
            self.supplier_countries[i] = country
            self.supplier_prices[i] = price
            self.supplier_urls[i] = url

    def remove_supplier(self, name):
        i = 0
        while i < len(self.supplier_names):
            if self.supplier_names[i] == name:
                self.supplier_names.pop(i)
                self.supplier_ordernums.pop(i)
                self.supplier_packagecounts.pop(i)
                self.supplier_currencies.pop(i)
                self.supplier_countries.pop(i)
                self.supplier_prices.pop(i)
                self.supplier_urls.pop(i)
            else:
                i += 1

    def add_subsystem(self, name, quantity, specific_use):
        try:
            i = self.subsystem_names.index(name)
        except ValueError:
            i = -1
        if i == -1:  # add
            self.subsystem_names.append(name)
            self.subsystem_quantities.append(quantity)
            self.subsystem_specificuses.append(specific_use)
        else:       # update
            self.subsystem_quantities[i] = quantity
            self.subsystem_specificuses[i] = specific_use

    def remove_subsystem(self, name):
        i = 0
        while i < len(self.subsystem_names):
            if self.subsystem_names[i] == name:
                self.subsystem_names.pop(i)
                self.subsystem_quantities.pop(i)
                self.subsystem_specificuses.pop(i)
            else:
                i += 1






class PartGroups(ndb.Model):
    bom_key = ndb.KeyProperty(kind=Bom, required=True)
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty()
    # for sorting
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    change_time = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def new(cls, bom_key, name):
        return cls(parent=bom_key, bom_key=bom_key, name=name)


class Manufacturers(ndb.Model):
    bom_key = ndb.KeyProperty(kind=Bom, required=True)
    name = ndb.StringProperty(required=True)
    # for sorting
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    change_time = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def new(cls, bom_key, name):
        return cls(parent=bom_key, bom_key=bom_key, name=name)


class Suppliers(ndb.Model):
    bom_key = ndb.KeyProperty(kind=Bom, required=True)
    name = ndb.StringProperty(required=True)
    note = ndb.StringProperty()
    currency_list = ndb.StringProperty(repeated=True)
    country_list = ndb.StringProperty(repeated=True)
    search_url_pattern = ndb.StringProperty()
    # for sorting
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    change_time = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def new(cls, bom_key, name):
        return cls(parent=bom_key, bom_key=bom_key, name=name)


class Subsystems(ndb.Model):
    bom_key = ndb.KeyProperty(kind=Bom, required=True)
    name = ndb.StringProperty(required=True)
    images = ndb.BlobKeyProperty(repeated=True)
    description = ndb.StringProperty()
    # for sorting
    create_time = ndb.DateTimeProperty(auto_now_add=True)
    change_time = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def new(cls, bom_key, name):
        return cls(parent=bom_key, bom_key=bom_key, name=name)
