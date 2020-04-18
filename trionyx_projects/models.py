"""App models"""
from trionyx import models
from trionyx.utils import CacheLock
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext as _
from django.utils.html import strip_tags

from .conf import settings as app_settings


class Project(models.BaseModel):
    STATUS_DRAFT = 10
    STATUS_ACTIVE = 20
    STATUS_ON_HOLD = 30
    STATUS_COMPLETED = 40
    STATUS_CANCELED = 99

    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_ON_HOLD, _('On hold')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_CANCELED, _('Canceled')),
    ]

    TYPE_FIXED = 10
    TYPE_HOURLY_BASED = 20

    TYPE_CHOICES = [
        (TYPE_FIXED, _('Fixed')),
        (TYPE_HOURLY_BASED, _('Hourly based')),
    ]

    # Connect Project to other Model
    for_object_type = models.ForeignKey(
        'contenttypes.ContentType',
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_('Object type'),
    )
    for_object_id = models.BigIntegerField(_('Object ID'), blank=True, null=True)
    for_object = GenericForeignKey('for_object_type', 'for_object_id')

    name = models.CharField(max_length=256)
    code = models.CharField(max_length=10, unique=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_DRAFT)
    project_type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE_FIXED)
    description = models.TextField(default='', null=True, blank=True)

    deadline = models.DateField(default=None, null=True, blank=True)
    started_on = models.DateField(default=None, null=True, blank=True)
    completed_on = models.DateField(default=None, null=True, blank=True)

    fixed_price = models.PriceField(null=True, blank=True)
    project_hourly_rate = models.PriceField(null=True, blank=True)

    item_increment_id = models.IntegerField(default=0)

    # Project stats
    open_items = models.IntegerField(default=0)
    completed_items = models.IntegerField(default=0)

    total_items_estimate = models.FloatField(default=0.0)
    total_worked = models.FloatField(default=0.0)
    total_billed = models.FloatField(default=0.0)

    @property
    def hourly_rate(self):
        return float(self.project_hourly_rate if self.project_hourly_rate else app_settings.HOURLY_RATE)

    def save(self, *args, **kwargs):
        self.code = str(self.code).upper()
        super().save(*args, **kwargs)


class Item(models.BaseModel):
    TYPE_FEATURE = 10
    TYPE_ENHANCEMENT = 20
    TYPE_TASK = 30
    TYPE_BUG = 40
    TYPE_QUESTION = 50

    TYPE_CHOICES = (
        (TYPE_FEATURE, _('Feature')),
        (TYPE_ENHANCEMENT, _('Enhancement')),
        (TYPE_TASK, _('Task')),
        (TYPE_BUG, _('Bug')),
        (TYPE_QUESTION, _('Question')),
    )

    PRIORITY_HIGHEST = 50
    PRIORITY_HIGH = 40
    PRIORITY_MEDIUM = 30
    PRIORITY_LOW = 20
    PRIORITY_LOWEST = 10

    PRIORITY_CHOICES = (
        (PRIORITY_HIGHEST, _('Highest')),
        (PRIORITY_HIGH, _('High')),
        (PRIORITY_MEDIUM, _('Medium')),
        (PRIORITY_LOW, _('Low')),
        (PRIORITY_LOWEST, _('Lowest')),
    )

    project = models.ForeignKey(Project, related_name='items', on_delete=models.CASCADE)
    item_type = models.IntegerField(choices=TYPE_CHOICES, default=TYPE_FEATURE, blank=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM, blank=True)

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=256)
    description = models.TextField(default='', null=True, blank=True)
    completed_on = models.DateField(default=None, null=True, blank=True)

    estimate = models.FloatField(null=True, blank=True)
    non_billable = models.BooleanField(default=False, blank=True)

    # Item stats
    total_worked = models.FloatField(default=0.0, blank=True)
    total_billed = models.FloatField(default=0.0, blank=True)

    class Meta:
        permissions = (
            ("limit_add_item", "Limit add"),
            ("limit_change_item", "Limit change"),
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        result = self.project.items.aggregate(
            open=models.Count('pk', filter=models.Q(completed_on__isnull=True)),
            closed=models.Count('pk', filter=models.Q(completed_on__isnull=False)),
            total_items_estimate=models.Sum('estimate', filter=models.Q(completed_on__isnull=True))
        )

        self.project.open_items = int(result['open'] or 0)
        self.project.completed_items = int(result['closed'] or 0)
        self.project.total_items_estimate = float(result['total_items_estimate'] or 0)


        if not self.code:
            with CacheLock('set-item-code', self.project_id):
                self.project.refresh_from_db() # get latest value
                self.project.item_increment_id += 1
                self.code = f"{self.project.code}-{self.project.item_increment_id}"
                self.save(update_fields=['code'])

        self.project.save(update_fields=['item_increment_id', 'open_items', 'completed_items', 'total_items_estimate'])

    @classmethod
    def get_type_icon(cls, item_type):
        icon_mapping = {
            cls.TYPE_FEATURE: 'fa fa-star',
            cls.TYPE_ENHANCEMENT: 'fa fa-bolt',
            cls.TYPE_TASK: 'fa fa-check',
            cls.TYPE_BUG: 'fa fa-bug',
            cls.TYPE_QUESTION: 'fa fa-question-circle',
        }

        badge_mapping = {
            cls.TYPE_FEATURE: 'badge-feature',
            cls.TYPE_ENHANCEMENT: 'badge-enhancement',
            cls.TYPE_TASK: 'badge-task',
            cls.TYPE_BUG: 'badge-bug',
            cls.TYPE_QUESTION: 'badge-question',
        }

        return f"<span class='badge badge-icon {badge_mapping[item_type]}'><i class='{icon_mapping[item_type]}'></i></span>"

    @classmethod
    def get_priority_icon(cls, priority):
        icon = 'fa fa-long-arrow-up'
        if priority <= cls.PRIORITY_LOW:
            icon = 'fa fa-long-arrow-down'

        class_mapping = {
            cls.PRIORITY_HIGHEST: 'priority-icon-highest',
            cls.PRIORITY_HIGH: 'priority-icon-high',
            cls.PRIORITY_MEDIUM: 'priority-icon-medium',
            cls.PRIORITY_LOW: 'priority-icon-low',
            cls.PRIORITY_LOWEST: 'priority-icon-lowest',
        }

        return f"<i class='{class_mapping[priority]} {icon}'></i>"


class Comment(models.BaseModel):
    item = models.ForeignKey(Item, related_name='comments', on_delete=models.CASCADE)
    comment = models.TextField(default='')

    def generate_verbose_name(self):
        comment = strip_tags(self.comment)
        if len(comment) > 20:
            return f"{comment:.20}..."
        return comment


class WorkLog(models.BaseModel):
    item = models.ForeignKey(Item, related_name='worklogs', on_delete=models.CASCADE)

    date = models.DateField()
    worked = models.FloatField()
    billed = models.FloatField(
        null=True, blank=True,
        help_text='On empty this wil be auto filled based on estimate and remaining billed hours, when there is no estimate billed will always be same as worked')

    description = models.TextField(default='', null=True, blank=True)

    def save(self, *args, **kwargs):
        result = self.item.worklogs.exclude(id=self.id).aggregate(
            total_worked=models.Sum('worked'),
            total_billed=models.Sum('billed'),
        )
        self.item.total_worked = (float(result['total_worked']) if result['total_worked'] else 0.0) + float(self.worked)
        total_billed = float(result['total_billed']) if result['total_billed'] else 0.0

        if self.item.non_billable:
            self.billed = 0
            self.item.total_billed = 0
        elif not self.billed and not self.item.estimate:
            self.billed = self.worked
        elif not self.billed:
            available = float(self.item.estimate or 0.0) - total_billed
            if available > 0:
                self.billed = available if self.worked > available else float(self.worked)
            else:
                self.billed = 0

        self.item.total_billed = total_billed + float(self.billed)

        if not self.description:
            self.description = f'Working on item {self.item.code}'

        self.item.save(update_fields=['total_billed', 'total_worked'])

        # Update project totals
        result = self.item.project.items.aggregate(
            total_worked=models.Sum('total_worked'),
            total_billed=models.Sum('total_billed'),
        )
        self.item.project.total_worked = float(result['total_worked'] or 0.0)
        self.item.project.total_billed = float(result['total_billed'] or 0.0)
        self.item.project.save(update_fields=['total_worked', 'total_billed'])

        super().save(*args, **kwargs)

    def generate_verbose_name(self):
        description = strip_tags(self.description)
        if len(description) > 20:
            return f"{description:.20}..."
        return description
