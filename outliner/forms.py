"""
The outliner.forms module contains a custom FormField that shows nested
structures in a drop down.
"""
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe


from mptt.exceptions import InvalidMove
from mptt.forms import TreeNodeChoiceField


class OutlinerChoiceField(TreeNodeChoiceField):
  """
  A ModelChoiceField for tree nodes. A ModelChoiceField is rendered as
  an HTML select tag. This extension of the ModelChoiceField presents
  the options of the select tag as a nested structure, using an optional
  ``level_indicator`` keyword argument to determine how the structure
  should be indented.
  
  Example:
    ``level_indicator="---"``
    
    would give the following representation of the tree structure:
    
    | ``root``
    | ``---first_level_child``
    | ``------second_level_child``
    | ``---------third_level_child``
    | ``etc.``
  """
  def __init__(self, *args, **kwargs):
    super(OutlinerChoiceField, self).__init__(*args, **kwargs)
    self.level_indicator = kwargs.pop('level_indicator', u'---')

  def label_from_instance(self, obj):
    """
    Creates the label for an HTML option tag.
    """
    return mark_safe(u'%s %s' % (self.level_indicator * getattr(obj, obj._mptt_meta.level_attr), smart_unicode(obj)))