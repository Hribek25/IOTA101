{%- extends 'full.tpl' -%}

{% block in_prompt -%}
<div class="prompt input_prompt">
%%%language_ico|{{cell['metadata'].get('iotadev', {}).get('codeid', '')}}%%%
</div>
{%- endblock in_prompt %}

{% block codecell %}
<span id="{{cell['metadata'].get('iotadev', {}).get('codeid', '')}}"></span>
<div class="cell border-box-sizing code_cell rendered">
{{ super() }}
</div>
{%- endblock codecell %}

{%- block html_head -%}
<meta charset="utf-8" />
<title>%%%title%%%</title>
<meta name="description" content="These notebooks provide a self-study introduction to IOTA protocol and are designed for developers and tech enthusiasts who would like to get quickly familiar with the IOTA. Technical-related information is accompanied with interactive code snippets to help you to quickly jump on the platform and be ready to build own solutions based on it. It is currently based on Python and NodeJS.">
<meta name="keywords" content="IOTA, code snippets, python, NodeJS, interactive, developers, tech enthusiasts, github">
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=UA-122669239-1"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'UA-122669239-1');
</script>

{%- if "widgets" in nb.metadata -%}
<script src="https://unpkg.com/jupyter-js-widgets@2.0.*/dist/embed.js"></script>
{%- endif-%}

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>

{% for css in resources.inlining.css -%}
    <style type="text/css">
    {{ css }}
    </style>
{% endfor %}

<style type="text/css">
/* Overrides of notebook CSS for static HTML export */
body {
  overflow: visible;
  padding: 8px;
}

div#notebook {
  overflow: visible;
  border-top: none;
}

{%- if resources.global_content_filter.no_prompt-%}
div#notebook-container{
  padding: 6ex 12ex 8ex 12ex;
}
{%- endif -%}

@media print {
  div.cell {
    display: block;
    page-break-inside: avoid;
  } 
  div.output_wrapper { 
    display: block;
    page-break-inside: avoid; 
  }
  div.output { 
    display: block;
    page-break-inside: avoid; 
  }
}
</style>

<!-- Custom stylesheet, it must be in the same directory as the html file -->
<link rel="stylesheet" href="custom.css">

<!-- Loading mathjax macro -->
{{ mathjax() }}
{%- endblock html_head -%}

