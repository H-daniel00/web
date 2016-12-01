import os
import logging
import smtplib
from django.http import HttpResponse, Http404
from django.template import Template, Context, RequestContext
from django.template.loader import select_template
#from django.shortcuts import render
from contenidos.models import Contenido, Categoria
from estudio.models import Estudio
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.contenttypes.models import ContentType


logger = logging.getLogger(u'videos')
NOVEDADES_CATEGORY_ID = 2

def get_home(request):

    slide_contents = Contenido.objects.filter(categoria__name__contains='Home slide', publishContent=True).order_by("publishInitDate")
    novedades = Contenido.objects.filter(categoria__id__exact=NOVEDADES_CATEGORY_ID, publishContent=True).order_by("-createdDate")[:3]
    context = {
        u'novedades': novedades,
        u'slide_contents': slide_contents
    }
    t = select_template(['home/index.html'])
    return HttpResponse(t.render(RequestContext(request, context)))

def get_content_friendly_url(request, friendly_url):
    """
    Soporte para frinedly URL: content/<friendly-url>
    """
    cContent = Contenido.objects.filter(friendlyURL=friendly_url).first()
    if bool(cContent):
        return get_content(request, cContent.id)
    else:
        raise Http404("No existe contenido: " + friendly_url)


def get_content(request, id_content, templateName='detalle-contenido.html' ):

    if (request.GET.has_key('template') and request.GET['template'] != ''):
        templateName = request.GET['template']

    cContent = Contenido.objects.get(pk=id_content)
    filePathName1, ext1 = os.path.splitext(cContent.img1.name)
    filePathName2, ext2 = os.path.splitext(cContent.img2.name)
    filePathName3, ext3 = os.path.splitext(cContent.img3.name)

    c = Context({
        'id':cContent.id,
        'title':cContent.title,
        'description':cContent.description,
        'body':cContent.body,
        'footer':cContent.footer,
        'img1':cContent.img1,
        'img1_med':filePathName1 + '_med' + ext1,
        'img2':cContent.img2,
        'img2_med':filePathName2 + '_med' + ext2,
        'img3':cContent.img3,
        'img3_med':filePathName3 + '_med' + ext3,
        'page_title':cContent.title
    })

    t = select_template(['home/{}'.format(templateName)])
    return HttpResponse(t.render(RequestContext(request, c)))

def get_categoria_friendly_url(request, friendly_url):
    """
    Soporte para friendly URL: categoria/<friendly-url>
    """
    c_categ = Categoria.objects.filter(friendlyURL=friendly_url).first()
    if bool(c_categ):
        request.GET = request.GET.copy() #creamos una copia para poder mutarlo
        request.GET['categoryId'] = c_categ.id
        return get_categoria(request)
    else:
        raise Http404("No existe contenido: " + friendly_url)

def get_categoria(request):
    """
    muestra los contenidos de una Categoria
    """
    category_id = 1
    if request.GET.has_key('categoryId') and request.GET['categoryId']:
        category_id = request.GET['categoryId']

    #Parche para ordenar novedades for fecha, hacerlo bien
    order_by = 'id'
    if request.GET.has_key('template') and request.GET['template'] == 'novedades.html':
        order_by = 'createdDate'

    categoria = Categoria.objects.get(id=category_id)
    contents = Contenido.objects.filter(categoria__id__exact=category_id, publishContent=True).order_by(order_by)

    def create_content(content):
        """
        genera un contenido
        """

        log = LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(type(content)).pk,object_id=content.pk,action_flag=ADDITION).first()

        contents_dicc = {
            "id" : content.id,
            "title": content.title,
            "description": content.description,
            "pub_date": content.publishInitDate or (log.action_time.date() if log else None),
            "footer": content.footer,
            "url": content.friendlyURL or content.id,
            "categories": content.keywords.split(',') if content.keywords else [],
            "img1": content.img1,
            "footer": content.footer
            }

        if content.img1:
            file_path_name, ext = os.path.splitext(content.img1.name)
            contents_dicc["img1_min"] = file_path_name + '_min' + ext

        return contents_dicc

    context = Context({
        'title': categoria.name,
        'description': categoria.description,
        'friendly': categoria.friendlyURL,
        'contents': [create_content(content) for content in contents],
        })

    template_name = 'listado-contenidos.html'
    if request.GET.has_key('template') and request.GET['template']:
        template_name = request.GET['template']

    template = select_template(['home/{}'.format(template_name)])
    return HttpResponse(template.render(RequestContext(request, context)))


def get_video(request, public_id):
    """
    Get the estudio for the given public_id, and displays the video link that redirects to the video download page.
    """    
    video_url = None
    paciente = None
    fecha_vencimiento = None
    link_vencido = True
    estudio_does_not_exist = False

    try:
        estudio = Estudio.objects.get(public_id=public_id)
        video_url = estudio.enlace_video
        paciente = str(estudio.paciente)
        fecha_vencimiento = estudio.fecha_vencimiento_link_video
        link_vencido = estudio.is_link_vencido()

        logger.info('Acceso correcto con public_id: %s' % public_id)
    except Estudio.DoesNotExist:
        estudio_does_not_exist = True
        logger.error('Intento con public_id erroneo: %s' % public_id)

    context = {
        u'video_url': video_url,
        u'paciente': paciente,
        u'fecha_vencimiento': fecha_vencimiento,
        u'link_vencido': link_vencido,
        u'estudio_does_not_exist': estudio_does_not_exist,
    }
    t = select_template(['pages/video_details.html'])
    return HttpResponse(t.render(RequestContext(request, context)))

def send_mail(request):
    toaddrs = settings.EMAIL_NOTIFICATION_ACCOUNTS
    subject = "Subject: Nuevo mensaje registrado desde cedirsalud.com.ar\n\n"

    gmail_user = settings.EMAIL_ACCOUNT_USER
    gmail_pwd = settings.EMAIL_ACCOUNT_PSW

    name = request.POST['name']
    email = request.POST['email']
    tel = request.POST['tel']
    message = request.POST['message']

    msg = subject + 'Nombre: ' + name + "\n" + 'Mail: ' + email + "\n" + 'Tel: ' + tel + "\n" + 'Mensaje: ' + message + "\n"

    smtpserver = smtplib.SMTP("smtp.gmail.com",587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(gmail_user, gmail_pwd)
    smtpserver.sendmail(gmail_user, toaddrs, msg)
    smtpserver.close()

    templateName = 'contacto_ok.html'
    t = select_template(['pages/' + templateName])

    c = Context({
        #'latest_poll_list': latest_poll_list,
	    #'current_date': now,
    })
    return HttpResponse(t.render(RequestContext(request, c)))

