from django import forms
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe


from mptt.exceptions import InvalidMove


class OutlinerChoiceField(forms.ModelChoiceField):
  """
  A ModelChoiceField for tree nodes. A ModelChoiceField is a select-tag.
  This ModelChoiceField presents the options of the select-tag as a
  nested structure
  """
  def __init__(self, *args, **kwargs):
    self.level_indicator = kwargs.pop('level_indicator', u'---')
    if kwargs.get('required', True) and not 'empty_label' in kwargs:
      kwargs['empty_label'] = None
    super(OutlinerChoiceField, self).__init__(*args, **kwargs)

  def label_from_instance(self, obj):
    """
    Creates the label printed to the option-tag. This will be on the format
    "--- [node_label]" if the level indicator is set to "---".
    """
    return mark_safe(u'%s %s' % (self.level_indicator * getattr(obj, obj._mptt_meta.level_attr), smart_unicode(obj)))