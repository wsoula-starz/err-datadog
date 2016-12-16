{% if saves %}
Found **{{ saves | length }}** saved queries:

{% for save in saves %}
{{ save.name }} - `{{ save.query }}` *({{ save.hours }}h)*
{% endfor %}{% else %}
:thinking_face: Maybe you could should make a saved graph first before listing them?
{% endif %}
