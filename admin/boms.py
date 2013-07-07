# -*- coding: utf-8 -*-
import webapp2
from web.models import Bom
from boilerplate import forms
from boilerplate.handlers import BaseHandler
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb
from google.appengine.api import users
from collections import OrderedDict, Counter
from wtforms import fields



class EditProfileForm(forms.EditProfileForm):
    activated = fields.BooleanField('Activated')



class List(BaseHandler):
    def get(self):
        p = self.request.get('p')
        q = self.request.get('q')
        c = self.request.get('c')
        forward = True if p not in ['prev'] else False
        cursor = Cursor(urlsafe=c)

        if q:
            qry = Bom.query(ndb.OR(Bom.public_id == q,
                                          Bom.name == q,
                                          Bom.tag_name == q))
        else:
            qry = Bom.query()

        PAGE_SIZE = 5
        if forward:
            boms, next_cursor, more = qry.order(Bom.key).fetch_page(PAGE_SIZE, start_cursor=cursor)
            if next_cursor and more:
                self.view.next_cursor = next_cursor
            if c:
                self.view.prev_cursor = cursor.reversed()
        else:
            boms, next_cursor, more = qry.order(-Bom.key).fetch_page(PAGE_SIZE, start_cursor=cursor)
            boms = list(reversed(boms))
            if next_cursor and more:
                self.view.prev_cursor = next_cursor
            self.view.next_cursor = cursor.reversed()
 
        def pager_url(p, cursor):
            params = OrderedDict()
            if q:
                params['q'] = q
            if p in ['prev']:
                params['p'] = p
            if cursor:
                params['c'] = cursor.urlsafe()
            return self.uri_for('boms-admin', **params)

        self.view.pager_url = pager_url
        self.view.q = q
        
        params = {
            "list_columns": [('public_id', 'Public ID'),
                             ('name', 'BOM Name'), 
                             ('tag_name', 'Tag Name'),
                             ('public', 'public')],
            "boms" : boms,
            "count" : qry.count(),
        }
        return self.render_template('admin/boms.html', **params)



class Edit(BaseHandler):
    def get_or_404(self, bom_id):
        try:
            bom = Bom.get_by_id(long(bom_id))
            if bom:
                return bom
        except ValueError:
            pass
        self.abort(404)

    def edit(self, bom_id):
        if self.request.POST:
            bom = self.get_or_404(bom_id)
            if self.form.validate():
                self.form.populate_obj(bom)
                bom.put()
                self.add_message("Changes saved!", 'success')
                return self.redirect_to("bom-admin-edit", bom_id=bom_id)
            else:
                self.add_message("Could not save changes!", 'error')
        else:
            bom = self.get_or_404(bom_id)
            self.form.process(obj=bom)

        params = {
            'bom' : bom
        }
        return self.render_template('admin/editbom.html', **params)

    @webapp2.cached_property
    def form(self):
        return EditProfileForm(self)



class Delete(BaseHandler):
    def get(self, bom_id):
        bom2delKey = ndb.Key(urlsafe=bom_id)
        bom2del = bom2delKey.get()
        bom2del.delete()
        self.redirect('/admin/bom')