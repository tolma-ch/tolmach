import warnings
warnings.simplefilter('default', DeprecationWarning)

from django.conf import settings
from django.shortcuts import render
from django.urls import include, re_path
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

PATH = getattr(settings, 'URL_PATH', '')

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^login/twitter/', lambda request: render(request, "main/helpers/twitter-outage.html")),
    re_path(r'%s' % PATH, include('social_django.urls',
        namespace='social')),
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    
    re_path(r'^blog/', include("blog.urls")),
    re_path(r'^markdownx/', include('markdownx.urls')),

    # new landing
    re_path(r'^landos/', main_views.new_landing, name='new_landing'),

    # main
    re_path(r'^$', main_views.index, name='index'),
    re_path(r'privacy/', TemplateView.as_view(template_name='main/policy/ru.html'), name="privacy_policy"),
    re_path(r'^%slogout/$' % PATH, django.contrib.auth.views.LogoutView.as_view(next_page = '/')),
    re_path(r'^user/(?P<username>[\w.@+-]+)/$', main_views.user_page, name="user_page"),
    re_path(r'^register/', main_views.register, name="register_user"),
    re_path(r'password-reset/$', main_views.reset_password_approve, name="reset_password_approve"),
    re_path(r'password-reset/(?P<token>\w+)/$', main_views.reset_password_form, name="reset_password_form"),
    re_path(r'password-accept/$', main_views.accept_password, name="accept_password"),
    re_path(r'^login/', main_views.login_user, name="login_user"),
    re_path(r'^social-login/', main_views.post_social_auth),
    re_path(r'^settings/(?:(?P<sett_type>\w+)/)?$', main_views.settings_page, name="settings_page"),
    re_path(r'^(?P<invite_type>\w+)/i/(?P<invite_id>\w+)/$', main_views.invite_urls, name='invitation_url'),
    re_path(r'^(?P<invite_type>\w+)/i/(?P<invite_id>\w+).jpg$', main_views.invite_urls_og_image, name='invitation_url_image'),

    # organizations
    re_path(r'^orgs/(?P<slug>[\w-]+)/$', main_views.organization_page, name='organization'),
    re_path(r'^orgs/(?P<slug>[\w-]+)/members/$', main_views.organization_members_page, name='organization_members'),
    re_path(r'^orgs/(?P<slug>[\w-]+)/settings/$', main_views.organization_settings_page, name='organization_settings'),
    re_path(r'^orgs/$', main_views.organizations),

    # translations
    re_path(r'^projects/(?P<proj_type>\w+)/$', trans_views.projects),

    re_path(r'^project/(?P<proj_id>\d+)/$', trans_views.project, name='project'),
    re_path(r'^project/(?P<proj_id>\d+)/stats/$', trans_views.project_stats, name='project_stats'),
    re_path(r'^project/(?P<proj_id>\d+)/(?P<target_lang>[\w-]+)/$', trans_views.project_by_translation, name='project_by_translation'),
    re_path(r'^text/show-readability/$', trans_views.show_readability, name='show_readability'),
    re_path(r'^text/(?P<text_id>\d+)/(?P<target_lang>[\w-]+)/$', trans_views.view_translation, name='view_translation'),
    re_path(r'^text/(?P<text_id>\d+)/(?P<target_lang>[\w-]+)/export/$', trans_views.export_translation, name='export_translation'),
    re_path(r'^text/(?P<text_id>\d+)/(?P<target_lang>[\w-]+)/export/(?P<extra>\w+)/$', trans_views.export_translation, name='export_translation'),
    re_path(r'^text/(?P<text_id>\d+)/(?P<target_lang>[\w-]+)/f/(?P<preview_code>\w+)/$', trans_views.fragment_preview, name='fragment_preview'),

    re_path(r'^tmx/(?P<tmx_id>\d+)/export/$', trans_views.export_tmx, name='export_tmx'),
    re_path(r'^glossary/(?P<glossary_id>\d+)/export/$', trans_views.export_glossary, name='export_glossary'),

    # short link for fragment with social preview
    # re_path(r'^f/(?P<preview_code>\w+)/$', trans_views.fragment_preview, name='fragment_preview'),

    # ajax
    re_path(r'^update-email/$', main_ajax.update_email_from_banner_ajax, name='update_email_ajax'),
    re_path(r'^check-email-approved/$', main_ajax.check_email_approved_from_banner_ajax, name='check_email_approved_ajax'),
    re_path(r'^confirm-email/$', main_ajax.request_email_confirmation_token_ajax, name='confirm_email_ajax'),
    re_path(r'^confirm-email/(?P<token>\w+)/$', main_ajax.validate_email_confirmation_token_ajax, name='confirm_email_token'),
    re_path(r'^ajax/search/$', main_ajax.global_search_ajax, name='global_search_ajax'),
    re_path(r'^ajax/orgs/$', main_ajax.organization_ajax, name='manage_orgs_ajax'),
    re_path(r'^ajax/orgs/members/$', main_ajax.organization_members_ajax, name='manage_orgs_members_ajax'),
    re_path(r'^ajax/orgs/invite-code/$', main_ajax.organization_invite_code_ajax, name='manage_orgs_invites_ajax'),

    re_path(r'^ajax/projects/(?P<proj_type>\w+)/(?:(?P<object_id>[\w.-]+)/)?$', trans_ajax.projects_ajax),
    re_path(r'^ajax/project-create/$', trans_ajax.create_project_ajax, name='create_project_ajax'),
    re_path(r'^ajax/project/invite-code/$', trans_ajax.project_invite_code, name='project_invite_code_ajax'),
    re_path(r'^ajax/project-add-translation/$', trans_ajax.add_project_translation, name='add_project_translation'),
    re_path(r'^ajax/project/$', trans_ajax.project_ajax, name='project_ajax'),

    re_path(r'^ajax/entry/(?:(?P<action>\w+)/)?$', trans_ajax.entry_ajax, name='entry_action_ajax'),
    re_path(r'^ajax/entry-history/$', trans_ajax.entry_history_ajax, name='entry_history_ajax'),
    re_path(r'^ajax/entry-deleted/$', trans_ajax.entry_deleted_ajax, name='entry_deleted_ajax'),
    re_path(r'^ajax/entry-disable/$', trans_ajax.disable_entry_ajax, name='entry_disable_ajax'),
    re_path(r'^ajax/entry-enable/$', trans_ajax.enable_entry_ajax, name='entry_enable_ajax'),
    re_path(r'^ajax/entry-approve/$', trans_ajax.approve_entry_ajax, name='entry_approve_ajax'),
    re_path(r'^ajax/entry-approve-by-user/$', trans_ajax.approve_all_entries_by_user_ajax, name='approve_all_entries_by_user_ajax'),
    re_path(r'^ajax/entry-disapprove-by-user/$', trans_ajax.disapprove_all_entries_by_user_ajax, name='disapprove_all_entries_by_user_ajax'),
    re_path(r'^ajax/entry-disapprove/$', trans_ajax.disapprove_entry_ajax, name='entry_approve_ajax'),
    re_path(r'^ajax/entry-translate/$', trans_ajax.translate_entry_ajax, name='translate_entry_ajax'),
    re_path(r'^ajax/entry-glossary-filter/$', trans_ajax.glossary_filter_entry_ajax, name='glossary_filter_entry_ajax'),
    re_path(r'^ajax/remove-translate/$', trans_ajax.remove_entry_ajax, name='remove_entry_ajax'),
    re_path(r'^ajax/get-translation-progress/$', trans_ajax.get_translation_progress, name='get_translation_progress'),
    re_path(r'^ajax/get-users/$', trans_ajax.get_users_ajax, name='get_users_ajax'),
    re_path(r'^ajax/participant/$', trans_ajax.participant_ajax, name='participant_ajax'),
    re_path(r'^ajax/text/$', trans_ajax.text_ajax, name='text_ajax'),
    re_path(r'^ajax/glossary/$', trans_ajax.glossary_ajax, name='glossary_ajax'),
    re_path(r'^ajax/tmx/$', trans_ajax.tmx_ajax, name='tmx_ajax'),
    re_path(r'^ajax/ya-translate/$', trans_ajax.yandex_translate_ajax, name='yandex_translate'),
    re_path(r'^ajax/tmdb-search/$', trans_ajax.tmdb_search, name='tmdb_search'),
    re_path(r'^ajax/tm-percentage/$', trans_ajax.update_tmdb_percentage, name='update_tmdb_percentage'),
    re_path(r'^ajax/dict-search/$', dict_views.dict_search, name='dict_search'),
    re_path(r'^ajax/message/(?:(?P<all>\w+)/)?$', trans_ajax.message_ajax, name='message_ajax'),
    re_path(r'^ajax/user/$', trans_ajax.user_ajax, name='user_ajax'),
    re_path(r'^ajax/languagetool/$', trans_ajax.languagetool_ajax, name='languagetool_ajax'),
    re_path(r'^ajax/get-url-og/$', main_ajax.get_url_og_meta, name='get_url_og_meta'),

    # temporarily added urls for developing purpuses
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += re_path("admin/", include('loginas.urls')),

try:
    debug_toolbar_enable = settings.DEBUG_TOOLBAR
except:
    debug_toolbar_enable = False

if debug_toolbar_enable:
    import debug_toolbar
    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
