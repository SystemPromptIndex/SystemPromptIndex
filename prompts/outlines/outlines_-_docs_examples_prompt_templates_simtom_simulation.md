---
id: "outlines/outlines_-_docs_examples_prompt_templates_simtom_simulation"
company: "outlines"
product: "outlines - docs examples prompt templates simtom simulation"
category: "general-purpose"
source_file: "docs_examples_prompt_templates_simtom_simulation.txt"
---

<s>[INST] {% for event in events %}
{{event}}
{% endfor %}
You are {{name}}.
Based on the above information, answer the following question:
{{question}}
You must choose one of the above choices, do not say there is not enough information. Answer with a single word, do not output anything else. [/INST]
