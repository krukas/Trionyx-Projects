"""App layouts"""
from trionyx.views import tabs, sidebars
from trionyx.layout import Component, Container, Row, Column4, Column8, Panel, TableDescription, Html, Button, Table, OnclickLink, Field, Badge
from trionyx.renderer import price_value_renderer
from trionyx.urls import model_url

from .conf import settings as app_settings
from .models import Project, Item
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
                        # 'total_worked' if obj.project_type == Project.TYPE_HOURLY_BASED else None,
                        # 'total_billed' if obj.project_type == Project.TYPE_HOURLY_BASED else None,

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
                ),
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
                'item_type',
                'priority',
                'created_at',
                'updated_at',
            ),
        )
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
            },
            css_class='no-margin',
            object=obj,
        ).render({}, request),
        'content': content.render({}, request),
        'actions': [
            {
                'label': 'Edit',
                'url': model_url(obj, 'dialog-edit'),
                'dialog': True,
                'reload': True,
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