
import uuid
import datetime
from webapp2_extras.appengine.auth.models import User
from google.appengine.ext import db
from google.appengine.ext import ndb

from google.appengine.ext import blobstore
from google.appengine.api.images import get_serving_url


class User(User):
    """
    Universal user model. Can be used with App Engine's default users API,
    own auth or third party authentication methods (OpenID, OAuth etc).
    based on https://gist.github.com/kylefinley
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #: User defined unique name, also used as key_name.
    # Not used by OpenID
    username = ndb.StringProperty()
    #: User Name
    name = ndb.StringProperty()
    #: User Last Name
    last_name = ndb.StringProperty()
    #: User email
    email = ndb.StringProperty()
    #: Hashed password. Only set for own authentication.
    # Not required because third party authentication
    # doesn't use password.
    password = ndb.StringProperty()
    #: User Country
    country = ndb.StringProperty()
    #: Account activation verifies email
    activated = ndb.BooleanProperty(default=False)
    
    @classmethod
    def get_by_email(cls, email):
        """Returns a user object based on an email.

        :param email:
            String representing the user email. Examples:

        :returns:
            A user object.
        """
        return cls.query(cls.email == email).get()

    @classmethod
    def create_resend_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'resend-activation-mail')
        return entity.token

    @classmethod
    def validate_resend_token(cls, user_id, token):
        return cls.validate_token(user_id, 'resend-activation-mail', token)

    @classmethod
    def delete_resend_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'resend-activation-mail', token).delete()

    def get_social_providers_names(self):
        social_user_objects = SocialUser.get_by_user(self.key)
        result = []
#        import logging
        for social_user_object in social_user_objects:
#            logging.error(social_user_object.extra_data['screen_name'])
            result.append(social_user_object.provider)
        return result

    def get_social_providers_info(self):
        providers = self.get_social_providers_names()
        result = {'used': [], 'unused': []}
        for k,v in SocialUser.PROVIDERS_INFO.items():
            if k in providers:
                result['used'].append(v)
            else:
                result['unused'].append(v)
        return result


class LogVisit(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    uastring = ndb.StringProperty()
    ip = ndb.StringProperty()
    timestamp = ndb.StringProperty()


class LogEmail(ndb.Model):
    sender = ndb.StringProperty(
        required=True)
    to = ndb.StringProperty(
        required=True)
    subject = ndb.StringProperty(
        required=True)
    body = ndb.TextProperty()
    when = ndb.DateTimeProperty()


class SocialUser(ndb.Model):
    PROVIDERS_INFO = { # uri is for OpenID only (not OAuth)
        'google': {'name': 'google', 'label': 'Google', 'uri': 'gmail.com'},
        'github': {'name': 'github', 'label': 'Github', 'uri': ''},
        'facebook': {'name': 'facebook', 'label': 'Facebook', 'uri': ''},
        'linkedin': {'name': 'linkedin', 'label': 'LinkedIn', 'uri': ''},
        'myopenid': {'name': 'myopenid', 'label': 'MyOpenid', 'uri': 'myopenid.com'},
        'twitter': {'name': 'twitter', 'label': 'Twitter', 'uri': ''},
        'yahoo': {'name': 'yahoo', 'label': 'Yahoo!', 'uri': 'yahoo.com'},
    }

    user = ndb.KeyProperty(kind=User)
    provider = ndb.StringProperty()
    uid = ndb.StringProperty()
    extra_data = ndb.JsonProperty()

    @classmethod
    def get_by_user(cls, user):
        return cls.query(cls.user == user).fetch()

    @classmethod
    def get_by_user_and_provider(cls, user, provider):
        return cls.query(cls.user == user, cls.provider == provider).get()

    @classmethod
    def get_by_provider_and_uid(cls, provider, uid):
        return cls.query(cls.provider == provider, cls.uid == uid).get()

    @classmethod
    def check_unique_uid(cls, provider, uid):
        # pair (provider, uid) should be unique
        test_unique_provider = cls.get_by_provider_and_uid(provider, uid)
        if test_unique_provider is not None:
            return False
        else:
            return True
    
    @classmethod
    def check_unique_user(cls, provider, user):
        # pair (user, provider) should be unique
        test_unique_user = cls.get_by_user_and_provider(user, provider)
        if test_unique_user is not None:
            return False
        else:
            return True

    @classmethod
    def check_unique(cls, user, provider, uid):
        # pair (provider, uid) should be unique and pair (user, provider) should be unique
        return cls.check_unique_uid(provider, uid) and cls.check_unique_user(provider, user)
    
    @staticmethod
    def open_id_providers():
        return [k for k,v in SocialUser.PROVIDERS_INFO.items() if v['uri']]





class PublicBomIdCounter(db.Model):
  bomid = db.IntegerProperty()
  
  @classmethod 
  def getNextId(cls):
    ret = 10001;
    counter = PublicBomIdCounter.all().get()
    if counter:
       ret = counter.bomid = counter.bomid + 1
       counter.put()
    else:
      PublicBomIdCounter(
        bomid = 10001,
      ).put()
    return ret



# class User(db.Model):
#     uuid = db.StringProperty(required=True)
#     email = db.EmailProperty(verbose_name="Email", required=True)
#     username = db.StringProperty(verbose_name="Username", required=True)
#     password_hash = db.StringProperty(verbose_name="Password", required=True)
#     first_name = db.StringProperty(verbose_name="First Name")
#     last_name = db.StringProperty(verbose_name="Last Name")
#     country = db.StringProperty(verbose_name="Country", default='United States', choices=sorted(countries.values()))
#     currency = db.StringProperty(verbose_name="Currency")
#     create_time = db.DateTimeProperty(verbose_name="Create Time", auto_now_add=True, required=True)
#     touch_time = db.DateTimeProperty(verbose_name="Touch Time", auto_now=True, required=True)



class Bom(db.Model):
    parent_id = db.SelfReferenceProperty()
    uuid = db.StringProperty(required=True)
    public_id = db.IntegerProperty(required=True)
    name = db.StringProperty(verbose_name="Name")
    images = db.ListProperty(blobstore.BlobKey)
    public = db.BooleanProperty(required=True, default=False)
    frozen = db.BooleanProperty(required=True, default=False)
    tag_name = db.StringProperty(verbose_name="Tag Name")
    create_time = db.DateTimeProperty(verbose_name="Create Time", auto_now_add=True, required=True)
    change_time = db.DateTimeProperty(verbose_name="Change Time", auto_now=True, required=True)
    like_count_cache = db.IntegerProperty()
    watch_count_cache = db.IntegerProperty()
    rough_count_cache = db.IntegerProperty()

    @classmethod
    def new(cls):
        return cls(
            uuid=str(uuid.uuid4()),
            public_id=PublicBomIdCounter.getNextId() )

    def get_url(self):
        return "/bom/" + str(self.public_id)

    def delete(self):
        @db.transactional(xg=True)
        def del_in_transaction():
            # User references
            for user2bom in self.user2bom:
                user2bom.delete()
            # Parts
            for part in self.parts:
                part.delete()
            # PartGroups
            for partgroup in self.partgroups:
                partgroup.delete()
            # Manufacturers
            for manufacturer in self.manufacturers:
                manufacturer.delete()
            # Suppliers
            for supplier in self.suppliers:
                supplier.delete()
            # Subsystems
            for subsystem in self.subsystems:
                subsystem.delete()                                    
            # Bom
            super(Bom, self).delete()

        del_in_transaction()



class User2Bom(db.Model):
    # user_id = db. ReferenceProperty(User, collection_name='user2bom', required=True)
    bom_id = db. ReferenceProperty(Bom, collection_name='user2bom', required=True)
    role = db.StringProperty(verbose_name="Role", default="reader", required=True, choices=set(["owner", "writer", "reader"]))
    like_flag = db.BooleanProperty(verbose_name="Like Flag", default=False)
    watch_flag = db.BooleanProperty(verbose_name="Watch Flag", default=False)
    rough_flag = db.BooleanProperty(verbose_name="Rough_Flag", default=False)



class Part(db.Model):
    bom_id = db.ReferenceProperty(Bom, collection_name='parts', required=True)
    uuid = db.StringProperty(required=True)
    name = db.StringProperty(verbose_name="Name", required=True)
    quantity_cached = db.IntegerProperty()
    pricepoint_cached = db.FloatProperty()
    currencies_cached = db.StringListProperty()
    part_group = db.StringProperty(verbose_name="Part Group")
    designator_list = db.StringListProperty()
    note_list = db.StringListProperty()                       # list of notes
    manufacturer_list = db.StringListProperty()               # list of [name,part_num]
    supplier_list = db.StringListProperty(required=True)      # list of [name,order_num,package_count,package_units,currency,price,explicit_url]
    usage_list = db.StringListProperty(required=True)         # list of [subsystem,quantity,specific_use]



class PartGroups(db.Model):
    bom_id = db.ReferenceProperty(Bom, collection_name='partgroups', required=True)
    name = db.StringProperty(verbose_name="Name", required=True)
    description = db.StringProperty(verbose_name="description")



class Manufacturers(db.Model):
    bom_id = db.ReferenceProperty(Bom, collection_name='manufacturers', required=True)
    name = db.StringProperty(verbose_name="Name", required=True)



class Suppliers(db.Model):
    bom_id = db.ReferenceProperty(Bom, collection_name='suppliers', required=True)
    name = db.StringProperty(verbose_name="Name", required=True)
    note = db.StringProperty(verbose_name="Note")
    currency_list = db.StringListProperty()
    country_list = db.StringListProperty()
    search_url_pattern = db.StringProperty(verbose_name="Search URL Pattern")



class Subsystems(db.Model):
    bom_id = db.ReferenceProperty(Bom, collection_name='subsystems', required=True)
    name = db.StringProperty(verbose_name="Name", required=True)
    images = db.ListProperty(blobstore.BlobKey)
    description = db.StringProperty(verbose_name="Description")


