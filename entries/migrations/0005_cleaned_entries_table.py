# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Entry.text'
        db.delete_column(u'entries_entry', 'text_id')

        # Deleting field 'Entry.vote'
        db.delete_column(u'entries_entry', 'vote')

        # Deleting field 'Entry.id_in_text'
        db.delete_column(u'entries_entry', 'id_in_text')


    def backwards(self, orm):
        # Adding field 'Entry.text'
        db.add_column(u'entries_entry', 'text',
                      self.gf('django.db.models.fields.related.ForeignKey')(default='', related_name='parent_text', to=orm['translations.Text']),
                      keep_default=False)

        # Adding field 'Entry.vote'
        db.add_column(u'entries_entry', 'vote',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'Entry.id_in_text'
        db.add_column(u'entries_entry', 'id_in_text',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    models = {
        u'entries.entry': {
            'Meta': {'object_name': 'Entry'},
            'body': ('django.db.models.fields.TextField', [], {'default': "''"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['entries.Language']"}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['entries.Subject']"})
        },
        u'entries.language': {
            'Meta': {'object_name': 'Language'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        u'entries.subject': {
            'Meta': {'object_name': 'Subject'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['entries']