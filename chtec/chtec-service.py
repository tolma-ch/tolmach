#!/usr/bin/env python
#-*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

from bottle import route, run, response, request, BaseRequest, app
import os, json, random, string
import subprocess

BaseRequest.MEMFILE_MAX = 102400000

FILES_DIR = os.environ.get("FILES_DIR", "/var/www/tolmach_documents")
WORKER_TIMEOUT = os.environ.get("WORKER_TIMEOUT", 3600)
LIBREOFFICE_BIN = os.environ.get("LIBREOFFICE_BIN", "/usr/bin/libreoffice --headless")
HOST = "127.0.0.1"
import formats
from chtec_lib import parsers
from chtec_lib import utils
from chtec_lib import exporters

import logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level='INFO')
logging.warning('is when this event was logged.')


@route('/convert', method="POST")
def convert():
    """
    Document model:
        "name": "test-doc.docx",
        "user_id": 35,
        "project_id": 246,
        "orig_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    """
    response.content_type = "application/json"

    parse_id = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))

    file_name = request.forms.get("fname")
    file_type = request.forms.get("format")
    title = getattr(request.forms, 'title')
    user_id = request.forms.get("user_id", type=int)
    project_id = request.forms.get("project_id", type=int)
    subject_id = request.forms.get("subject_id", default=5, type=int)
    source_lang_code = request.forms.get("source_lang")
    target_lang_code = request.forms.get("target_lang")
    save_to_db = request.forms.get("save_to_db", default=True, type=bool)
    split_mode = request.forms.get("split_mode", default="default", type=str)
    custom_parse = request.forms.get("custom_parse", default=None, type=str)

    original_file_type = ""

    if None in [file_name, file_type, user_id, project_id, source_lang_code]:
        return json.dumps({'Error': 500, 'Text': 'Not enough params', 'Splitted': False})

    file_path = "%s/%d/%d/%s" % (FILES_DIR, user_id, project_id, file_name)
    target_path = "%s/%d/%d/" % (FILES_DIR, user_id, project_id)

    if not os.path.isdir(target_path):
        os.makedirs(target_path)

    logging.info('%s - parsing file "%s", title="%s", type="%s", source_lang="%s"',
                 parse_id, file_path, title, file_type, source_lang_code)


    if not file_name == "None":
        if not os.path.isfile(file_path):
            logging.error("%s - file (%s) not found", parse_id, file_path)
            return json.dumps({'Error': 404, 'Text': 'File not found'})

    data = {}

    if file_type == formats.FORMATS['txt']:
        if not request.forms.text_body == "":
            data_to_parse = request.forms.text_body
        else:
            import codecs
            enc = utils.detect_by_bom(file_path, 'utf-8-sig')
            with codecs.open(file_path, 'r', encoding=enc) as f:
                lines = f.readlines()
                data_to_parse = "".join(lines)
        data = parsers.from_plain_text(data_to_parse, source_lang_code, split_mode=split_mode)
    elif file_type == formats.FORMATS['docx']:
        # "чистим" docx перед парсингом
        logging.debug("%(parse_id)s - %(libreoffice)s --convert-to docx --outdir %(tmp_path)s \"%(file_name)s\"" % {
            'parse_id': parse_id,
            'libreoffice': LIBREOFFICE_BIN,
            'tmp_path': target_path,
            "file_name": file_path,
        })
        subprocess.call("%(libreoffice)s --convert-to docx --outdir %(tmp_path)s \"%(file_name)s\"" % {
            'libreoffice': LIBREOFFICE_BIN,
            'tmp_path': target_path,
            "file_name": file_path,
        },
                        shell=True)

        logging.debug("%s - mv %s %s", parse_id, target_path + file_name, file_path)
        os.rename(target_path + file_name, file_path)
        data = parsers.from_docx(file_path, source_lang_code, split_mode=split_mode)
    elif file_type in [formats.FORMATS['doc'],
                       formats.FORMATS['odt'],
                       formats.FORMATS['rtf']]:
        logging.info("%s - converting to DOCX", parse_id)
        convert_status, new_filename = parsers.to_x(target_path, file_path, "docx")
        if convert_status:
            logging.info("%s - converted successfully - %s", parse_id, new_filename)
            original_file_type = file_type
            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_name = new_filename.split("/")[-1]
            data = parsers.from_docx(new_filename, source_lang_code, split_mode=split_mode)
    elif file_type == formats.FORMATS['xlsx']:
        data = parsers.from_xlsx(file_path, custom_parse)
    elif file_type in [formats.FORMATS['pptx'],
                       formats.FORMATS['html'],
                       ]:
        logging.info("%s - converting to XLIFF", parse_id)
        convert_status, new_filename = parsers.to_tmp_xliff(file_path)
        if convert_status:
            logging.info("%s - converted successfully - %s", parse_id, new_filename)
            original_file_type = file_type
            file_type = "application/x-xliff+xml"
            # file_name = new_filename.split("/")[-1]
            data = parsers.from_xliff(file_path + ".xlf")
    elif file_type in [formats.FORMATS['po'], formats.FORMATS['mo'], formats.FORMATS['pot']]:
        data = parsers.from_po_mo(file_path, file_type, source_lang_code)
    elif file_type == formats.FORMATS['srt']:
        data = parsers.from_srt(file_path, source_lang_code)
    elif file_type == formats.FORMATS['xlf']:
        data = parsers.from_xlf(file_path)
    elif file_type == formats.FORMATS['ass']:
        data = parsers.from_ass(file_path, source_lang_code)
    else:
        logging.error("%s - file format is not supported", parse_id)
        return json.dumps({'Error': 500, 'Text': 'Sorry, file format is not supported'})

    if data['Error'] == 0:
        logging.info('%s - data parsed from file successfully', parse_id)
        if len(data['entries']) > 0:
            if save_to_db:
                utils.make_sure_mysql_usable()

                db_save = utils.save_to_db(data,
                                 project_id,
                                 source_lang_code,
                                 target_lang_code,
                                 subject_id,
                                 user_id,
                                 title,
                                 document_format=file_type,
                                 document_name=file_name,
                                 original_format=original_file_type)
                if db_save['Error'] == 0:
                    logging.info("%s - parsed data successfully saved to db", parse_id)
                    return json.dumps({'Error': 0, 'Text': db_save['TextId']})
                else:
                    logging.error("%s - %s", parse_id, db_save['TextId'])
                    return json.dumps({'Error': db_save['Error'], 'Text': db_save['ErrorText']})
            else:
                logging.info("%s - parsed data was not saved to db, but it's okay", parse_id)
                return json.dumps({'Error': 0, 'Text': data})
        else:
            logging.error("%s - no entries in parsed data", parse_id)
            return json.dumps({'Error': 400, 'Text': "document is empty"})
    else:
        logging.error("%s - file parsing failed: %s", parse_id, data['ErrorText'])
        return json.dumps({'Error': data['Error'], 'Text': data['ErrorText']})


@route('/preparse', method="POST")
def get_preparse_data():
    file_name = request.forms.get("fname")
    file_type = request.forms.get("format")
    user_id = request.forms.get("user_id", type=int)
    project_id = request.forms.get("project_id", type=int)

    if None in [file_name, file_type, user_id, project_id]:
        return json.dumps({'Error': 500, 'Text': 'Not enough params', 'Splitted': False})

    file_path = "%s/%d/%d/%s" % (FILES_DIR, user_id, project_id, file_name)

    utils.make_sure_mysql_usable()

    if file_type == formats.FORMATS['xlsx']:
        return json.dumps({'Error': 0, 'file_name': file_name, 'Text': utils.get_xlsx_data(file_path)}, default=str)
    else:
        return json.dumps({'Error': 204, 'Text': 'No data'})

@route('/export', method="POST")
def export_text():
    text_id = request.forms.get("text_id", type=int)
    target_lang = request.forms.get("target_lang")
    export_pairs = request.forms.get("export_pairs", default=False, type=bool)
    export_as_po = request.forms.get("export_as_po", default=False, type=bool)

    export_id = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))

    RETURN_DATA = {
        'Error': 500,
        'error_message': 'Something unexpected occured. Please try again.',
        'file_name': '',
        'file_ext': '',
        'content_type': '',
    }

    utils.make_sure_mysql_usable()

    if export_pairs:
        RETURN_DATA = exporters.uni_export(text_id, target_lang, export_id, export_pairs=True)
    elif export_as_po:
        RETURN_DATA = exporters.uni_export(text_id, target_lang, export_id, export_as_po=True)
    else:
        RETURN_DATA = exporters.uni_export(text_id, target_lang, export_id)

    return json.dumps(RETURN_DATA)

@route('/update', method="POST")
def update_text():
    file_name = request.forms.get("fname")
    text_id = request.forms.get("text_id")
    user_id = request.forms.get("user_id")
    new_data = request.forms.get("new_data")
    document_format = request.forms.get("document_format")
    if None in [file_name, text_id, user_id, new_data, document_format]:
        return json.dumps({'Error': 500, 'Text': 'Not enough params', 'Splitted': False})

    data = json.loads(new_data)['Text']

    utils.make_sure_mysql_usable()

    return json.dumps({'Result': utils.update_text(text_id, user_id, data, file_name, document_format)})


sent_app = app()
sent_app.catchall = False
from raven import Client
from raven.contrib.bottle import Sentry
client = Client('***REMOVED***')
sent_app = Sentry(sent_app, client)

run(host=HOST, port=8080, server="gunicorn", workers=10, debug=True, app=sent_app, timeout=WORKER_TIMEOUT)
