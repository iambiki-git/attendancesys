from django import template
import nepali_datetime

register = template.Library()

@register.filter
def nepali_date(value):
    if isinstance(value, (str,)):
        return value
    try:
        bs_date = nepali_datetime.date.from_datetime_date(value)
        return bs_date.strftime('%K-%n-%D')  # Example: 2081-04-08
    except:
        return value
