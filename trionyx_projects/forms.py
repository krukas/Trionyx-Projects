"""
trionyx_invoices.forms
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019 by Maikel Martens
:license: GPLv3
"""
from django.apps import apps
from trionyx import forms
from trionyx.forms.helper import FormHelper
from trionyx.forms.layout import Layout, Div, HTML, Depend, DateTimePicker
from django.utils.translation import ugettext_lazy as _

from .models import Project, Item


@forms.register(default_create=True, default_edit=True)
class ProjectForm(forms.ModelForm):
    description = forms.Wysiwyg(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if apps.is_installed("trionyx_accounts"):
            from trionyx_accounts.models import Account
            self.fields['account'] = forms.ChoiceField(
                label=_('Account'),
                choices=[
                    ('', '-----'),
                    *Account.objects.values_list('id', 'verbose_name')
                ],
                required=False,
                initial=self.instance.for_object_id,
            )

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        Div(
                            'name',
                            css_class='col-md-8',
                        ),
                        Div(
                            'code',
                            css_class='col-md-2',
                        ),
                        Div(
                            'status',
                            css_class='col-md-2',
                        ),
                        css_class='row',
                    ),
                    Div(
                        Div(
                            'account' if apps.is_installed("trionyx_accounts") else None,
                            css_class='col-md-8',
                        ),
                        Div(
                            DateTimePicker('deadline', format='%Y-%m-%d'),
                            css_class='col-md-4',
                        ),
                        css_class='row',
                    ),
                    Div(
                        Div(
                            'project_type',
                            css_class='col-md-8',
                        ),
                        Div(
                            Depend(
                                [('project_type', '10')],
                                'fixed_price',
                            ),
                            Depend(
                                [('project_type', '20')],
                                'project_hourly_rate',
                            ),
                            css_class='col-md-4',
                        ),
                        css_class='row',
                    ),
                    css_class='col-md-6',
                ),
                Div(
                    'description',
                    css_class='col-md-6',
                ),
                css_class='row',
            ),
        )

    class Meta:
        model = Project
        fields = ['name', 'code', 'status', 'deadline', 'description', 'project_type', 'fixed_price', 'project_hourly_rate']


    def save(self, commit=True):
        invoice = super().save(commit=False)

        if self.cleaned_data.get('account'):
            from trionyx_accounts.models import Account
            invoice.for_object = Account.objects.get(id=self.cleaned_data['account'])

        if commit:
            invoice.save()

        return invoice


@forms.register(default_create=True, default_edit=True)
class ItemForm(forms.ModelForm):
    description = forms.Wysiwyg(required=False)

    item_type = forms.ChoiceField(choices=[
        (choice[0], '{} {}'.format(Item.get_type_icon(choice[0]), choice[1])) for choice in Item.TYPE_CHOICES
    ], required=False)

    priority = forms.ChoiceField(choices=[
        (choice[0], '{} {}'.format(Item.get_priority_icon(choice[0]), choice[1])) for choice in Item.PRIORITY_CHOICES
    ], required=False, initial=Item.PRIORITY_MEDIUM)

    class Meta:
        model = Item
        fields = ['project', 'item_type', 'priority', 'name', 'description', 'estimate', 'non_billable']
        widgets = {
            'project': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'project',
            Div(
                Div(
                    'item_type',
                    css_class='col-md-6',
                ),
                Div(
                    'priority',
                    css_class='col-md-6',
                ),
                css_class='row',
            ),
            'name',
            Div(
                Div(
                    'estimate',
                    css_class='col-md-6',
                ),
                Div(
                    'non_billable',
                    css_class='col-md-6',
                ),
                css_class='row',
            ),
            'description',
        )