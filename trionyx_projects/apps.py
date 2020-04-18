"""Trionyx_projects app configuration"""
from trionyx.trionyx.apps import BaseConfig
from trionyx.config import ModelConfig


def render_status(model, *args, **kwargs):
    """Render status as label"""
    mapping = {
        10: 'default',
        20: 'info',
        30: 'default',
        40: 'success',
        99: 'danger',
    }

    return '<span class="label label-{}">{}</span>'.format(
        mapping.get(model.status, 'default'),
        model.get_status_display()
    )


class Config(BaseConfig):
    """Trionyx_projects configuration"""

    name = 'trionyx_projects'
    verbose_name = 'Projects'

    css_files = [
        'projects/style.css'
    ]

    class Project(ModelConfig):
        menu_root = True
        menu_icon = 'fa fa-cubes'
        menu_order = 40
        verbose_name = '{code} - {name}'
        list_default_fields = ['name', 'code', 'status', 'deadline']
        list_fields = [
            {
                'field': 'status',
                'renderer': render_status
            }
        ]

        auditlog_ignore_fields = ['item_increment_id']

    class Item(ModelConfig):
        menu_exclude = True
        disable_search_index = True
        auditlog_disable = True

        verbose_name = '{code}'

    class Comment(ModelConfig):
        menu_exclude = True
        disable_search_index = True
        auditlog_disable = True

    class WorkLog(ModelConfig):
        menu_exclude = True
        disable_search_index = True
        auditlog_disable = True
