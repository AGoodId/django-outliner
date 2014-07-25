"""
The outliner.admin module contains the class definitions needed to
convert the default Django admin changelist to a drag-and-drop enabled
outliner.

The classes in this module enforces correct sort order of the outliner
tree and adds handling of AJAX callbacks to update the tree structure.
"""
from django.contrib.admin.views.main import ChangeList
from django.http import HttpResponse, HttpResponseBadRequest


from mptt.admin import MPTTModelAdmin
from mptt.exceptions import InvalidMove


class SortableModelAdmin(MPTTModelAdmin):
  """
  This class extends the mptt.admin.MPTTModelAdmin
  (from `django-mptt <https://github.com/django-mptt/django-mptt/>`_)
  with views that allow insertion and moving of nodes through AJAX POST
  requests.
  """

  def _move_node(self, request):
    """
    Takes a POST request containing node, target and parent parameters
    and moves the node accordingly.
    """
    node = self.model._tree_manager.get(pk=request.POST.get('node'))
    target = self.model._tree_manager.get(pk=request.POST.get('target'))
    position = request.POST.get('position')
    if request.POST.get('parent') == 'current':
      parent = node.parent
      target_level = parent.level + 1
    elif request.POST.get('parent') != 'false':
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


class OutlinerChangeList(ChangeList):
  """
  OutlinerChangeList class. Inherits the django.contrib.admin.ChangeList
  class and enforces sorting of nodes in tree order. Requires an
  mptt.models.MPTTModel
  (from `django-mptt <https://github.com/django-mptt/django-mptt/>`_)
  to function as intended.
  """
  def __init__(self, *args, **kwargs):
    request = args[0]
    super(OutlinerChangeList, self).__init__(*args, **kwargs)

    queryset = self.get_query_set(request)
    if hasattr(self, 'queryset'):
      self.queryset = queryset
    else:
      # Django 1.5 and older
      self.query_set = queryset

    self.get_results(request)
  
  def get_query_set(self, request):
    qs = super(OutlinerChangeList, self).get_query_set(request)
    # always order by (tree_id, left)
    tree_id = qs.model._mptt_meta.tree_id_attr
    left = qs.model._mptt_meta.left_attr
    return qs.order_by(tree_id, left)


class OutlinerModelAdmin(SortableModelAdmin):
  """
  An admin class that uses an outliner with drag and drop for the change list.
  """
  
  list_max_show_all = 10000
  list_per_page = 10000
  
  def get_changelist(self, request, **kwargs):
    """
    Returns the OutlinerChangeList class for use on the changelist page.
    """
    return OutlinerChangeList

  def changelist_view(self, request, extra_context=None, *args, **kwargs):
    """
    Extends the default ModelAdmin ``changelist_view`` function with
    logic for handling AJAX requests. Performs the requested action if
    the request is sent with ajax, otherwise it calls super.
    """    
    # handle common AJAX requests
    if request.is_ajax():
      cmd = request.POST.get('__cmd')
      if cmd == 'move_node':
        return self._move_node(request)
      else:
        return HttpResponseBadRequest('AJAX request not understood.')
    return super(OutlinerModelAdmin, self).changelist_view(request, extra_context, *args, **kwargs)


class BrowserChangeList(ChangeList):

  tree_params = ['parent', 'level']

  def get_filters(self, request):
    if not self.model_admin.is_browsing(request):
      for p in self.tree_params:
        self.params.pop(p, None)
    return super(BrowserChangeList, self).get_filters(request)

  def get_query_set(self, request):
    qs = super(BrowserChangeList, self).get_query_set(request)
    if self.model_admin.is_browsing(request) and all(p not in self.params for p in self.tree_params):
      qs = qs.filter(level=1)
    return qs


class BrowserModelAdmin(SortableModelAdmin):
  """
  An admin class that uses a browser with drag and drop for the change list.
  """

  def is_browsing(self, request):
    flat_params = ['q']
    if all(p not in request.GET for p in flat_params):
      return True
    else:
      return False

  def is_tree_ordered(self, request):
    if 'o' not in request.GET:
      return True
    else:
      return False

  def get_ordering(self, request):
    return (self.model._mptt_meta.tree_id_attr, self.model._mptt_meta.left_attr)

  def get_changelist(self, request, **kwargs):
    return BrowserChangeList

  def changelist_view(self, request, extra_context={}):
    if request.is_ajax():
      cmd = request.POST.get('__cmd')
      if cmd == 'move_node':
        return self._move_node(request)
      else:
        return HttpResponseBadRequest('AJAX request not understood.')

    # Add breadcrumbs to the context
    crumb_query = request.GET.copy()
    level = crumb_query.pop('level', [None])[0]
    parent_id = crumb_query.pop('parent', [None])[0]
    page = crumb_query.pop('p', [None])[0]
    query = crumb_query.pop('q', [None])[0]
    parent = None
    crumbs = None
    if self.is_browsing(request):
      try:
        parent = self.model.objects.get(pk=parent_id)
      except:
        parent = self.model.on_site.get_root()
      try:
        crumbs = parent.get_ancestors(include_self=True)
      except:
        pass
    extra_context.update({
      'crumb_query': crumb_query.urlencode(),
      'parent': parent,
      'crumbs': crumbs
    })
    # Store the query and extra data so the fields can access it
    self.crumb_query = crumb_query
    return super(BrowserModelAdmin, self).changelist_view(request, extra_context=extra_context)
