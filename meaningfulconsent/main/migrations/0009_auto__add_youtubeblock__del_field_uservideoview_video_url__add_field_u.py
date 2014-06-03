# flake8: noqa
# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'UserVideoView', fields ['user', 'video_url']
        db.delete_unique(u'main_uservideoview', ['user_id', 'video_url'])

        # Adding model 'YouTubeBlock'
        db.create_table(u'main_youtubeblock', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('video_id', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=2)),
        ))
        db.send_create_signal(u'main', ['YouTubeBlock'])

        # Deleting field 'UserVideoView.video_url'
        db.delete_column(u'main_uservideoview', 'video_url')

        # Adding field 'UserVideoView.video_id'
        db.add_column(u'main_uservideoview', 'video_id',
                      self.gf('django.db.models.fields.CharField')(default=1, max_length=256),
                      keep_default=False)

        # Adding unique constraint on 'UserVideoView', fields ['user', 'video_id']
        db.create_unique(u'main_uservideoview', ['user_id', 'video_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'UserVideoView', fields ['user', 'video_id']
        db.delete_unique(u'main_uservideoview', ['user_id', 'video_id'])

        # Deleting model 'YouTubeBlock'
        db.delete_table(u'main_youtubeblock')

        # Adding field 'UserVideoView.video_url'
        db.add_column(u'main_uservideoview', 'video_url',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=512),
                      keep_default=False)

        # Deleting field 'UserVideoView.video_id'
        db.delete_column(u'main_uservideoview', 'video_id')

        # Adding unique constraint on 'UserVideoView', fields ['user', 'video_url']
        db.create_unique(u'main_uservideoview', ['user_id', 'video_url'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'main.clinic': {
            'Meta': {'object_name': 'Clinic'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        u'main.quizsummaryblock': {
            'Meta': {'object_name': 'QuizSummaryBlock'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quiz_class': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'main.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'clinic': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Clinic']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'creator'", 'null': 'True', 'to': u"orm['auth.User']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '2'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        },
        u'main.uservideoview': {
            'Meta': {'unique_together': "(('user', 'video_id'),)", 'object_name': 'UserVideoView'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seconds_viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'video_duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'video_id': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        u'main.youtubeblock': {
            'Meta': {'object_name': 'YouTubeBlock'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'video_id': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        }
    }

    complete_apps = ['main']