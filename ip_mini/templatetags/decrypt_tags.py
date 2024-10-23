from django import template
from ip_mini.encrypt_util import decrypt

register = template.Library()


@register.filter
def decrypt_template_tag(value):
    return decrypt(value)
