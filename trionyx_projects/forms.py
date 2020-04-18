"""
trionyx_invoices.forms
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019 by Maikel Martens
:license: GPLv3
"""
from django.utils import timezone
from django.apps import apps
from trionyx import forms
from trionyx.forms.helper import FormHelper
from trionyx.forms.layout import Layout, Div, HTML, Depend, DateTimePicker
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags
from trionyx.utils import get_current_request

from .models import Project, Item, Comment, WorkLog


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

@forms.register(code='limited', create_permission='trionyx_projects.limit_add_item', edit_permission='trionyx_projects.limit_change_item')
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

        estimate_div = Div(
            Div(
                'estimate',
                css_class='col-md-6',
            ),
            Div(
                'non_billable',
                css_class='col-md-6',
            ),
            css_class='row',
        )

        if (
            self.instance.id and not get_current_request().user.has_perm('trionyx_projects.change_item') and get_current_request().user.has_perm('trionyx_projects.limit_change_item')
        ) or (
            not self.instance.id and not get_current_request().user.has_perm('trionyx_projects.add_item') and get_current_request().user.has_perm('trionyx_projects.limit_add_item')
        ):
            self.fields['estimate'].disabled = True
            self.fields['non_billable'].disabled = True
            estimate_div = Div()

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
            estimate_div,
            'description',
        )



@forms.register(default_create=True, default_edit=True)
class CommentForm(forms.ModelForm):
    comment = forms.Wysiwyg()

    class Meta:
        model = Comment
        fields = ['item', 'comment']

        widgets = {
            'item': forms.HiddenInput(),
        }

    def clean_comment(self):
        if not strip_tags(self.cleaned_data['comment']).replace('&nbsp;', ' ').strip():
            raise forms.ValidationError('This field is required.')

        return self.cleaned_data['comment']


@forms.register(default_create=True, default_edit=True)
class WorklogForm(forms.ModelForm):
    description = forms.Wysiwyg(required=False)
    date = forms.DateField(initial=timezone.now)

    class Meta:
        model = WorkLog
        fields = ['item', 'date', 'worked', 'billed', 'description']

        widgets = {
            'item': forms.HiddenInput(),
        }
