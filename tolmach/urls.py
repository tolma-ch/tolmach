from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView
import django.contrib.auth.views
import tolmach.views as main_views
import tolmach.views_ajax as main_ajax
import translations.views as trans_views
import translations.views_ajax as trans_ajax
import dicts.views as dict_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

PATH = getattr(settings, 'URL_PATH', '')

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/uwsgi/', include('django_uwsgi.urls')),
    url(r'%s' % PATH, include('social_django.urls',
        namespace='social')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^rest/', include('api.urls')),

    # main
    url(r'^$', main_views.index, name='index'),
    url(r'privacy/', TemplateView.as_view(template_name='main/policy/ru.html')),
    url(r'^%slogout/$' % PATH, django.contrib.auth.views.logout, {'next_page': '/'}),
    url(r'^user/(?P<user_id>\d+)/$', main_views.user_page, name="user_page"),
    url(r'^register/', main_views.register, name="register_user"),
    url(r'password-reset/$', main_views.reset_password_approve, name="reset_password_approve"),
    url(r'password-reset/(?P<token>\w+)/$', main_views.reset_password_form, name="reset_password_form"),
    url(r'password-accept/$', main_views.accept_password, name="accept_password"),
    url(r'^login/', main_views.login_user, name="login_user"),
    url(r'^social-login/', main_views.post_social_auth),
    url(r'^settings/(?:(?P<sett_type>\w+)/)?$', main_views.settings_page, name="settings_page"),
    url(r'^(?P<invite_type>\w+)/i/(?P<invite_id>\w+)/$', main_views.invite_urls, name='invitation_url'),
    url(r'^(?P<invite_type>\w+)/i/(?P<invite_id>\w+).jpg$', main_views.invite_urls_og_image, name='invitation_url_image'),

    # organizations
    url(r'^orgs/(?P<slug>[\w-]+)/$', main_views.organization_page, name='organization'),
    url(r'^orgs/(?P<slug>[\w-]+)/members/$', main_views.organization_members_page, name='organization_members'),
    url(r'^orgs/(?P<slug>[\w-]+)/settings/$', main_views.organization_settings_page, name='organization_settings'),
    url(r'^orgs/$', main_views.organizations),

    # translations
    url(r'^projects/(?P<proj_type>\w+)/$', trans_views.projects),

    url(r'^project/(?P<proj_id>\d+)/$', trans_views.project, name='project'),
    url(r'^project/(?P<proj_id>\d+)/stats/$', trans_views.project_stats, name='project_stats'),
    url(r'^project/(?P<proj_id>\d+)/(?P<target_lang>\w+)/$', trans_views.project_by_translation, name='project_by_translation'),
    url(r'^text/(?P<text_id>\d+)/(?P<target_lang>\w+)/$', trans_views.view_translation, name='view_translation'),
    url(r'^text/(?P<text_id>\d+)/(?P<target_lang>\w+)/export/$', trans_views.export_translation, name='export_translation'),
    url(r'^text/(?P<text_id>\d+)/(?P<target_lang>\w+)/export/(?P<extra>\w+)/$', trans_views.export_translation, name='export_translation'),
    url(r'^text/(?P<text_id>\d+)/(?P<target_lang>\w+)/f/(?P<preview_code>\w+)/$', trans_views.fragment_preview, name='fragment_preview'),

    # short link for fragment with social preview
    # url(r'^f/(?P<preview_code>\w+)/$', trans_views.fragment_preview, name='fragment_preview'),

    # ajax
    url(r'^ajax/search/$', main_ajax.global_search_ajax, name='global_search_ajax'),
    url(r'^ajax/orgs/$', main_ajax.organization_ajax, name='manage_orgs_ajax'),
    url(r'^ajax/orgs/members/$', main_ajax.organization_members_ajax, name='manage_orgs_members_ajax'),
    url(r'^ajax/projects/(?P<proj_type>\w+)/(?:(?P<object_id>[\w-]+)/)?$', trans_ajax.projects_ajax),
    url(r'^ajax/project-create/$', trans_ajax.create_project_ajax, name='create_project_ajax'),
    url(r'^ajax/project-add-translation/$', trans_ajax.add_project_translation, name='add_project_translation'),
    url(r'^ajax/project/$', trans_ajax.project_ajax, name='project_ajax'),
    url(r'^ajax/entry/(?:(?P<action>\w+)/)?$', trans_ajax.entry_ajax, name='entry_action_ajax'),
    url(r'^ajax/entry-disable/$', trans_ajax.disable_entry_ajax, name='entry_disable_ajax'),
    url(r'^ajax/entry-enable/$', trans_ajax.enable_entry_ajax, name='entry_enable_ajax'),
    url(r'^ajax/entry-approve/$', trans_ajax.approve_entry_ajax, name='entry_approve_ajax'),
    url(r'^ajax/entry-approve-by-user/$', trans_ajax.approve_all_entries_by_user_ajax, name='approve_all_entries_by_user_ajax'),
    url(r'^ajax/entry-disapprove-by-user/$', trans_ajax.disapprove_all_entries_by_user_ajax, name='disapprove_all_entries_by_user_ajax'),
    url(r'^ajax/entry-disapprove/$', trans_ajax.disapprove_entry_ajax, name='entry_approve_ajax'),
    url(r'^ajax/entry-translate/$', trans_ajax.translate_entry_ajax, name='translate_entry_ajax'),
    url(r'^ajax/remove-translate/$', trans_ajax.remove_entry_ajax, name='remove_entry_ajax'),
    url(r'^ajax/get-translation-progress/$', trans_ajax.get_translation_progress, name='get_translation_progress'),
    url(r'^ajax/get-users/$', trans_ajax.get_users_ajax, name='get_users_ajax'),
    url(r'^ajax/participant/$', trans_ajax.participant_ajax, name='participant_ajax'),
    url(r'^ajax/text/$', trans_ajax.text_ajax, name='text_ajax'),
    url(r'^ajax/glossary/$', trans_ajax.glossary_ajax, name='glossary_ajax'),
    url(r'^ajax/tmx/$', trans_ajax.tmx_ajax, name='tmx_ajax'),
    url(r'^ajax/ya-translate/$', trans_ajax.yandex_translate_ajax, name='yandex_translate'),
    url(r'^ajax/tmdb-search/$', trans_ajax.tmdb_search, name='tmdb_search'),
    url(r'^ajax/dict-search/$', dict_views.dict_search, name='dict_search'),
    url(r'^ajax/message/(?:(?P<all>\w+)/)?$', trans_ajax.message_ajax, name='message_ajax'),
    url(r'^ajax/user/$', trans_ajax.user_ajax, name='user_ajax'),

    url('', include('chat.urls')),

    # temporarily added urls for developing purpuses
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

try:
    debug_toolbar_enable = settings.DEBUG_TOOLBAR
except:
    debug_toolbar_enable = False

if debug_toolbar_enable:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]