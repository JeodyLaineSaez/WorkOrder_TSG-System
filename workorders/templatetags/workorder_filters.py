from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary using its key."""
    return dictionary.get(key)

@register.filter(name='verbose_name')
def verbose_name(value):
    """Returns the verbose name of a model field."""
    return value._meta.verbose_name.title() if hasattr(value, '_meta') else value

@register.filter(name='status_badge_class')
def status_badge_class(status):
    """Returns the appropriate Bootstrap badge class based on work order status."""
    status_classes = {
        'Pending': 'badge bg-warning',
        'In Progress': 'badge bg-info',
        'Completed': 'badge bg-success',
        'Cancelled': 'badge bg-danger',
    }
    return status_classes.get(status, 'badge bg-secondary')
