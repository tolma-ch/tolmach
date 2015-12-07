from django.conf import settings
from django.conf.urls import patterns, include, url
import tolmach.views as main_views
import translations.views as trans_views
import translations.views_ajax as trans_ajax

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

PATH = getattr(settings, 'URL_PATH', '')

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'%s' % PATH, include('social.apps.django_app.urls',
        namespace='social')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # main
    url(r'^$', main_views.index, name='index'),
    url(r'^%slogout/$' % PATH, 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^user/(?P<user_id>\d+)/$', main_views.user_page, name="user_page"),
    # url(r'^populate-data/$', main_views.populate_test_data, name='alfatest_data'),

    # translations
    # url(r'^parse-tmx/$', trans_views.parse_tmx),
    url(r'^projects/(?P<proj_type>\w+)/$', trans_views.projects),
    url(r'^projects/add/$', trans_views.project_add, name='add_project'),
    url(r'^project/(?P<proj_id>\d+)/$', trans_views.project, name='project'),
    url(r'^project/(?P<proj_id>\d+)/delete/$', trans_views.project_delete, name='delete_project'),
    url(r'^project/(?P<proj_id>\d+)/invite-user/(?P<us_id>\d+)/$', trans_views.invite_user_to_project, name='add_user_to_project'),
    url(r'^project/(?P<proj_id>\d+)/remove-user/(?P<us_id>\d+)/$', trans_views.remove_user_from_project, name='remove_user_from_project'),
    url(r'^text/(?P<text_id>\d+)/(?P<target_lang>\w+)/$', trans_views.view_translation, name='view_translation'),
    url(r'^text/(?P<text_id>\d+)/(?P<target_lang>\w+)/export/$', trans_views.export_translation, name='export_translation'),

    # ajax
    url(r'^api/project-create/$', trans_ajax.create_project_ajax, name='create_project_ajax'),
    url(r'^api/project/$', trans_ajax.project_ajax, name='project_ajax'),
    url(r'^api/entry/(?:(?P<action>\w+)/)?$', trans_ajax.entry_ajax, name='entry_action_ajax'),
    url(r'^api/entry-approve/$', trans_ajax.approve_entry_ajax, name='entry_approve_ajax'),
    url(r'^api/entry-disapprove/$', trans_ajax.disapprove_entry_ajax, name='entry_approve_ajax'),
    url(r'^api/entry-translate/$', trans_ajax.translate_entry_ajax, name='translate_entry_ajax'),
    url(r'^api/get-users/$', trans_ajax.get_users_ajax, name='get_users_ajax'),
    url(r'^api/participant/$', trans_ajax.participant_ajax, name='participant_ajax'),
    url(r'^api/text/$', trans_ajax.text_ajax, name='text_ajax'),
    url(r'^api/glossary/$', trans_ajax.glossary_ajax, name='glossary_ajax'),
    url(r'^api/tmx/$', trans_ajax.tmx_ajax, name='tmx_ajax'),
    url(r'^api/ya-translate/$', trans_ajax.yandex_translate_ajax, name='yandex_translate'),
    url(r'^api/tmdb-search/$', trans_ajax.tmdb_search, name='tmdb_search'),
    url(r'^api/message/(?:(?P<all>\w+)/)?$', trans_ajax.message_ajax, name='message_ajax'),
    url(r'^api/user/$', trans_ajax.user_ajax, name='user_ajax'),

    # temporarily added urls for developing purpuses
)
