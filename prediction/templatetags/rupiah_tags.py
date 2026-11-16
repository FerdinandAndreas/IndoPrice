from django import template

register = template.Library()

@register.filter(name='rupiah')
def rupiah(value):
    """
    Format angka integer atau float menjadi format Rupiah dengan pemisah titik ribuan.
    Contoh: 247217341 -> "247.217.341"
    """
    if value is None or value == '':
        return '-'
    try:
        val = int(round(float(value)))
        return f"{val:,}".replace(',', '.')
    except (ValueError, TypeError):
        return value
