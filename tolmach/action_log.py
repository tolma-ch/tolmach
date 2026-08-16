# -*- coding: utf-8 -*-

import json
import logging
import time


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter with no external dependencies.

    Emits one JSON object per log record. Standard fields are always present;
    extra keys (user_id, action, status, ...) are included only when the
    caller passed them via the ``extra`` argument of a logging call.
    """

    def __init__(self, fmt=None, datefmt=None, extra_fields=None):
        super(JsonFormatter, self).__init__(fmt, datefmt)
        self.extra_fields = extra_fields or ()

    def format(self, record):
        record_dict = {
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        for field in self.extra_fields:
            if hasattr(record, field):
                record_dict[field] = getattr(record, field)
        if record.exc_info:
            record_dict['exception'] = self.formatException(record.exc_info)
        return json.dumps(record_dict, ensure_ascii=False, default=str)


audit_logger = logging.getLogger('audit')


def _request_context(request):
    if not request:
        return {}
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')
    return {
        'request_id': getattr(request, 'request_id', ''),
        'method': request.method,
        'path': request.path,
        'ip': ip,
    }


def _user_id(user):
    return getattr(user, 'pk', None)


def _username(user):
    if user is None:
        return 'anonymous'
    if getattr(user, 'is_authenticated', False):
        return getattr(user, 'username', '')
    return 'anonymous'


def _level_for(status):
    if status == 'error':
        return logging.ERROR
    elif status in ('failed', 'denied'):
        return logging.WARNING
    return logging.INFO


def log_action(user, action, status='success', request=None, detail=None,
               target=None, start_time=None):
    """Explicitly record one user action and its outcome to the audit log.

    Call this at the point where the outcome is known:

        log_action(request.user, 'project.create', status='success',
                   request=request, target='project:42', detail={'lang': 'ru'})

    ``status`` is one of ``success``, ``failed``, ``denied``, ``error``.
    ``start_time`` is optional and, when given, adds ``duration_ms``.
    """
    duration_ms = None
    if start_time is not None:
        try:
            duration_ms = int((time.time() - start_time) * 1000)
        except (TypeError, ValueError):
            duration_ms = None

    record = {
        'user_id': _user_id(user),
        'username': _username(user),
        'action': action,
        'status': status,
        'target': target,
        'detail': detail or {},
        'duration_ms': duration_ms,
    }
    record.update(_request_context(request))

    audit_logger.log(_level_for(status), action, extra=record)