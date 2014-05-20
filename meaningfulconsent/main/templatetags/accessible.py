from django import template

register = template.Library()


class AccessibleNode(template.Node):
    def __init__(self, module, nodelist_true, nodelist_false=None):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.module = module

    def render(self, context):
        m = context[self.module]
        if 'request' in context:
            r = context['request']
            u = r.user

            visited, last_section = m.gate_check(u)
            if visited and m.submitted(u):
                return self.nodelist_true.render(context)

        return self.nodelist_false.render(context)


@register.tag('ifaccessible')
def accessible(parser, token):
    module = token.split_contents()[1:][0]
    nodelist_true = parser.parse(('else', 'endifaccessible'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifaccessible',))
        parser.delete_first_token()
    else:
        nodelist_false = None
    return AccessibleNode(module, nodelist_true, nodelist_false)
