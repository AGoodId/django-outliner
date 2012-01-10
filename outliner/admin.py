from django.contrib.admin.views.main import ChangeList
from django.http import HttpResponse, HttpResponseBadRequest


from mptt.admin import MPTTModelAdmin
from mptt.exceptions import InvalidMove


class OutlinerChangeList(ChangeList):
  """
  Outliner ChangeList class. Inherits the django.contrib.admin ChangeList
  class and extends it by adding logic for sorting nodes in tree order.
  Requires an MPTTModel to function as intended.
  """
  def __init__(self, *args, **kwargs):
    super(OutlinerChangeList, self).__init__(*args, **kwargs)
    self.root_query_set = self.model.objects.get_query_set()
    self.query_set = self.get_query_set()
    self.get_results(args[0])
  
  def get_query_set(self):
    qs = super(OutlinerChangeList, self).get_query_set()
    # always order by (tree_id, left)
    tree_id = qs.model._mptt_meta.tree_id_attr
    left = qs.model._mptt_meta.left_attr
    return qs.order_by(tree_id, left)


class OutlinerModelAdmin(MPTTModelAdmin):
  """
  This class extends the MPTTModelAdmin (https://github.com/django-mptt
  /django-mptt/) with views that allow insertion and moving of nodes
  through AJAX POST requests.
  """
  def get_changelist(self, request, **kwargs):
    """
    Returns the ChangeList class for use on the changelist page.
    """
    return OutlinerChangeList

  def changelist_view(self, request, extra_context=None, *args, **kwargs):
    """
    Extends the default ModelAdmin ``changelist_view`` function with
    logic for handling AJAX requests.
    """    
    # handle common AJAX requests
    if request.is_ajax():
      cmd = request.POST.get('__cmd')
      if cmd == 'move_node':
        return self.move_node(request)
      else:
        return HttpResponseBadRequest('AJAX request not understood.')
    return super(OutlinerModelAdmin, self).changelist_view(request, extra_context, *args, **kwargs)

  def move_node(self, request):
    """
    Takes a POST request containing node, target and parent parameters
    and moves the node accordingly.
    """
    node = self.model._tree_manager.get(pk=request.POST.get('node'))
    target = self.model._tree_manager.get(pk=request.POST.get('target'))
    position = request.POST.get('position')
    if request.POST.get('parent') != 'false':
      parent = self.model._tree_manager.get(pk=request.POST.get('parent'))
      target_level = parent.level + 1
    else:
      parent = None
      target_level = 0
    if target.level > target_level:
      # If the above condition is true, we should find the closest
      # preceding node at the same level as the target level
      target = target.get_ancestors(ascending=True).filter(level=target_level)[0]
    if target == parent:
      # If target and parent are the same node, insert as first-child
      position = 'first-child'
    elif position == 'before':
      # If the position string in the post request is ``before``
      # position should be ``left``. This only happens when a node is
      # dragged to position of first root.
      position = 'left'
    else:
      # Otherwise, insert to the right of target
      position = 'right'
    # Mode the node to its new home using mptt
    try:
      self.model._tree_manager.move_node(node, target, position)
    except InvalidMove, e:
      self.message_user(request, unicode(e))
      return HttpResponse('FAIL: %s' % e, mimetype="text/plain")
    # Make sure the node has been saved
    node = self.model._tree_manager.get(pk=node.pk)
    node.save()
    return HttpResponse('OK', mimetype="text/plain")