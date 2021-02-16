from django.utils.translation import ugettext as _
from django.shortcuts import render, get_object_or_404, HttpResponse
from django.urls import reverse as reverse_url
from django.http import Http404
from entries.models import Language
from .models import Post


def main(request, blog_lang, is_rss=False):
    if blog_lang == "ru":
        language_full_code = "ru-RU"
        blog_lang_return = "ru"
    elif blog_lang == "en":
        language_full_code = "en-US"
        blog_lang_return = "en"
    else:
        language_full_code = "en-US"
        blog_lang_return = "en"

    l = get_object_or_404(Language, code_tmx=language_full_code)

    # для админа показываем посты со всеми статусами, для обычного юзера - только те, что опубликованы
    published = [True, False] if request.user.is_staff else [True]
    posts = Post.objects.filter(language=l, published__in=published).order_by('-date')
    for p in posts:
        p.formatted_content = p.formatted_markdown()
        p.clean_content = p.clean_content_text()
        p.lang_code = p.language.code_tmx
        p.url = reverse_url('post', kwargs={
            'blog_lang': p.language.code,
            'date': p.date.strftime("%y%m%d"),
            'slug': p.slug
        })

    if is_rss:
        from xml.dom import minidom
        from email.utils import format_datetime
        method = "https" if request.is_secure() else "http"
        domain = request.get_host()
        base_domain = method + "://" + domain

        doc = minidom.Document()
        rss = doc.createElement('rss')
        rss.setAttribute('version', '2.0')
        rss.setAttribute('xmlns:atom', 'http://www.w3.org/2005/Atom')
        doc.appendChild(rss)
        channel = doc.createElement('channel')
        rss.appendChild(channel)

        channelTitle = doc.createElement('title')
        channel.appendChild(channelTitle)
        channelTitleText = doc.createTextNode("Tolma.ch Blog")
        channelTitle.appendChild(channelTitleText)

        channelLink = doc.createElement('link')
        channel.appendChild(channelLink)
        channelLinkText = doc.createTextNode(base_domain + reverse_url('blog', kwargs={'blog_lang': l.code}))
        channelLink.appendChild(channelLinkText)

        atom = doc.createElement('atom:link')
        atom.setAttribute('href', base_domain + reverse_url('rss', kwargs={'blog_lang': l.code, 'is_rss': 'rss'}))
        atom.setAttribute('rel', 'self')
        atom.setAttribute('type', 'application/rss+xml')
        channel.appendChild(atom)

        channelDescription = doc.createElement('description')
        channel.appendChild(channelDescription)
        channelDescriptionText = doc.createTextNode('Tolma.ch CAT news-feed')
        channelDescription.appendChild(channelDescriptionText)

        for p in posts:
            newItem = doc.createElement('item')
            channel.appendChild(newItem)

            newItemLink = doc.createElement('link')
            newItemLinkText = doc.createTextNode(base_domain + p.url)
            newItem.appendChild(newItemLink)
            newItemLink.appendChild(newItemLinkText)

            newItemLink = doc.createElement('guid')
            newItemLinkText = doc.createTextNode(base_domain + p.url)
            newItem.appendChild(newItemLink)
            newItemLink.appendChild(newItemLinkText)

            newItemTitle = doc.createElement('title')
            newItemTitleText = doc.createTextNode(p.title)
            newItem.appendChild(newItemTitle)
            newItemTitle.appendChild(newItemTitleText)

            newItemPubDate = doc.createElement('pubDate')
            newItemPubDateText = doc.createTextNode(format_datetime(p.date))
            newItem.appendChild(newItemPubDate)
            newItemPubDate.appendChild(newItemPubDateText)

            newItemDescription = doc.createElement('description')
            newItemDescriptionText = doc.createCDATASection(p.formatted_content)
            newItem.appendChild(newItemDescription)
            newItemDescription.appendChild(newItemDescriptionText)

        response = HttpResponse(doc.toxml(), content_type="application/xml")
        response['Content-Disposition'] = 'inline; filename=myfile.xml'
        return response
    context = {
        'posts': posts,
        'blog_lang': blog_lang_return,
        'social_preview_tags': {'title': _('Blog'), 'description': _('Tolma.ch news and tips & tricks')},
        'page_title': f"{_('Blog')} / Tolma.ch",
        'breadcrumbs': [
            {'title': _("Blog"), 'url': reverse_url('blog', kwargs={'blog_lang': l.code}), 'type': ''},
        ],
    }
    return render(request, "blog/main.html", context)


def post(request, blog_lang, date, slug):
    import datetime
    if blog_lang == "ru":
        language_full_code = "ru-RU"
    elif blog_lang == "en":
        language_full_code = "en-US"
    else:
        language_full_code = "en-US"
    t = datetime.datetime.strptime(date, "%y%m%d")
    l = get_object_or_404(Language, code_tmx=language_full_code)
    p = get_object_or_404(Post, slug=slug, date__date=t, language=l)
    if not p.published and not request.user.is_staff:
        raise Http404(_("Blog post does not exist"))
    p.formatted_content = p.formatted_markdown()
    p.clean_content = p.clean_content_text()
    p.url = reverse_url('post', kwargs={'blog_lang': l.code, 'date': date, 'slug': slug})

    context = {
        'post': p,
        'social_preview_tags': {'title': p.title, 'description' : p.content},
        'page_title': f"{p.title} / {_('Blog')} / Tolma.ch",
        'breadcrumbs': [
            {'title': _("Blog"), 'url': reverse_url('blog', kwargs={'blog_lang': l.code}), 'type': ''},
            {'title': p.title, 'url': '#', 'type': ''},
        ],
    }

    return render(request, "blog/post.html", context)

