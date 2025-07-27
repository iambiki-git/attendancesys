from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)



@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None  # or return "-" if you prefer

# @register.filter
# def get_item(dictionary, key):
#     if isinstance(dictionary, dict):
#         return dictionary.get(key, "-")
#     return "-"
