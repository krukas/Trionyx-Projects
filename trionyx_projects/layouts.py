"""App layouts"""
from trionyx.views import tabs, sidebars
from trionyx.layout import (
    Component, Container, Row, Column4, Column8, Panel,
    TableDescription, Html, Button, Table, OnclickLink, Field, Badge,
    HtmlTemplate, ButtonGroup
)
from trionyx.renderer import price_value_renderer
from trionyx.urls import model_url
from trionyx.utils import get_current_request

from .conf import settings as app_settings
from .models import Project, Item, Comment, WorkLog
from .apps import render_status

@tabs.register('trionyx_projects.Project')
def project_overview(obj):
    return Container(
        Row(
            Column8(
                Panel(
                    'Backlog',
                    Table(
                        obj.items.order_by('-priority', 'item_type', 'code'),
                        {
                            'field': 'item_type',
                            'renderer': lambda value, **options: Item.get_type_icon(value)
                        },
                        {
                            'field': 'priority',
                            'renderer': lambda value, **options: Item.get_priority_icon(value)
                        },
                        {
                            'field': 'code',
                            'value': OnclickLink(
                                Field('code'),
                                sidebar=True,
                            )
                        },
                        {
                            'field': 'name',
                            'class': 'width-100'
                        },
                        {
                            'field': 'estimate',
                            'value': Badge(Field('estimate', renderer= lambda value, data_object: f"{value}h" if value else '&nbsp;'), css_class="badge estimate-badge"),
                            'class': 'text-right',
                        },
                        header=False
                    ),
                    Button(
                        'Add item',
                        model_url='dialog-create',
                        model_params={
                            'project': obj.id
                        },
                        dialog=True,
                        dialog_reload_tab='general',
                        css_class='btn btn-flat bg-theme btn-block',
                        object=Item()
                    ),
                )
            ),
            Column4(
                Panel(
                    'Project details',
                    TableDescription(
                        {
                            'field': 'status',
                            'renderer': lambda value, data_object, **options: render_status(data_object),
                        },
                        'created_at',
                        'project_type',
                        {
                            'label': 'deadline',
                            'value': obj.deadline if obj.deadline else 'n/a',
                            'format': '<strong>{}</strong>'
                        },
                        {
                            'field': 'hour_rate',
                            'value': price_value_renderer(app_settings.HOURLY_RATE if obj.project_type == Project.TYPE_FIXED else obj.hourly_rate)
                        },
                        {
                            'field': 'total_items_estimate',
                            'label': 'Total hours'
                        } if obj.project_type == Project.TYPE_HOURLY_BASED else {
                          'field': 'Calculated hours',
                          'value': float(obj.fixed_priceif if obj.fixed_price else 0) / float(obj.hourly_rate),
                        },

                        {
                            'label': 'Calculated price',
                            'value': price_value_renderer(float(obj.total_billed) * float(obj.hourly_rate)),
                            'format': '<strong>{}</strong>'
                        } if obj.project_type == Project.TYPE_HOURLY_BASED else {
                            'field': 'fixed_price',
                            'format': '<strong>{}</strong>'
                        },
                    )
                ),
                Panel(
                    'Logged hours',
                    TableDescription(
                        'total_worked',
                        'total_billed',
                    ),
                ) if get_current_request().user.has_perm('trionyx_projects.view_worklog') else None,
                Panel(
                    'Description',
                    Html(obj.description),
                    collapse=False
                )
            )
        )
    )


@sidebars.register(Item)
def item_sidebar(request, obj):
    content = Component(
        Panel(
            'Description',
            Html(obj.description),
        ),
        Panel(
            'Info',
            TableDescription(
                {
                    'field': 'item_type',
                    'renderer': lambda value, data_object, **options: "{} {}".format(
                        data_object.get_type_icon(data_object.item_type),
                        data_object.get_item_type_display(),
                    )
                },
                {
                    'field': 'priority',
                    'renderer': lambda value, data_object, **options: "{} {}".format(
                        data_object.get_priority_icon(data_object.priority),
                        data_object.get_priority_display(),
                    )
                },
                'created_at',
                'updated_at',
            ),
        ),
        Panel(
            'Comments',
            Button(
                'Add comment',
                model_url='dialog-create',
                model_params={
                    'item': obj.id
                },
                dialog=True,
                dialog_reload_sidebar=True,
                css_class='btn btn-flat bg-theme btn-block',
                object=Comment()
            ),
             *[Component(
                 HtmlTemplate('trionyx_projects/project_comment.html', object=comment, lock_object=True),
            ) for comment in obj.comments.order_by('-created_at')]
        ) if request.user.has_perm('trionyx_projects.view_comment') else None,
        Panel(
            'Worklogs',
            Button(
                'Add worklog',
                model_url='dialog-create',
                model_params={
                    'item': obj.id
                },
                dialog=True,
                dialog_reload_sidebar=True,
                css_class='btn btn-flat bg-theme btn-block',
                object=WorkLog()
            ),
            Table(
                obj.worklogs.order_by('-date', 'id'),
                'date',
                {
                    'field': 'created_by',
                    'label': 'User',
                },
                'description',
                {
                    'field': 'worked',
                    'label': 'W',
                },
                {
                    'field': 'billed',
                    'label': 'B',
                },
                {
                    'label': 'Options',
                    'width': '60px',
                    'value': ButtonGroup(
                        Button(
                            '<i class="fa fa-edit"></i>',
                            css_class='btn bg-theme btn-xs',
                            dialog=True,
                            model_url='dialog-edit',
                            dialog_reload_sidebar=True,
                            should_render=lambda comp: comp.object.created_by == request.user or request.user.is_superuser,
                        ) if request.user.has_perm('trionyx_projects.change_worklog') else None,
                        Button(
                            '<i class="fa fa-times"></i>',
                            css_class='btn bg-red btn-xs',
                            dialog=True,
                            model_url='dialog-delete',
                            dialog_reload_sidebar=True,
                            should_render=lambda comp: comp.object.created_by == request.user or request.user.is_superuser,
                        ) if request.user.has_perm('trionyx_projects.delete_worklog') else None,
                    )
                }
            ),
        ) if request.user.has_perm('trionyx_projects.view_worklog') else None,
    )

    content.set_object(obj)


    return {
        'title': f"{obj.code} - {obj.name}",
        'fixed_content': TableDescription(
            {
                'field': 'estimate',
                'renderer': lambda value, **options: f"{value}h" if value else '0h',
                'class': 'text-right'
            },
            {
                'field': 'total_worked',
                'label': 'Logged',
                'renderer': lambda value, **options: f"{value}h" if value else '0h',
                'class': 'text-right'
            } if request.user.has_perm('trionyx_projects.view_worklog') else None,
            {
                'field': 'total_billed',
                'label': 'Billed',
                'renderer': lambda value, **options: f"{value}h" if value else '0h',
                'class': 'text-right'
            } if request.user.has_perm('trionyx_projects.view_worklog') else None,
            css_class='no-margin',
            object=obj,
        ).render({}, request),
        'content': content.render({}, request),
        'actions': [
            {
                'label': 'Edit',
                'url': model_url(obj, 'dialog-edit'),
                'dialog': True,
                'dialog_options': {
                    'callback': """
                        if (data.success) { 
                            trionyx_reload_tab('general');
                            reloadSidebar();
                            dialog.close();
                        };
                    """
                },
            },
            {
                'label': 'Delete',
                'class': 'text-danger',
                'url': model_url(obj, 'dialog-delete'),
                'dialog': True,
                'dialog_options': {
                    'callback': """
                        if (data.success) { 
                            trionyx_reload_tab('general');
                            closeSidebar();
                            dialog.close();
                        };
                    """
                },
                'divider': True,
            }
        ]
    }