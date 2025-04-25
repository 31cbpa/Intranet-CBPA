from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter(name='currency_clp')
def currency_clp(value):
    return f"${value:,.0f}".replace(',', '.')
