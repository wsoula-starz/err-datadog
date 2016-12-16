{% if hosts %}
Found **{{ hosts | length }}** hosts matching that name:

{% for host in hosts %}
• {{ host }}
{% endfor %}
{% else %}
The search turned up nothing! :cry:
{% endif %}