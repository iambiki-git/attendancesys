from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def short_school_name(value):
    words = value.split()
    if len(words) >= 4:
        return f"{words[0]} {words[1]} {words[-1]}"
    return value


