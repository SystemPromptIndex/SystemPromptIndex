---
id: "codecompanion.nvim/codecompanion.nvim_-_tests_prompt_library_stubs_test_prompt"
company: "codecompanion.nvim"
product: "codecompanion.nvim - tests prompt library stubs test prompt"
category: "coding-agents"
source_file: "clone_tests_prompt_library_stubs_test_prompt.md"
---

---
name: Test Prompt
strategy: chat
description: Explain how code in a buffer works
opts:
  auto_submit: true
  is_slash_cmd: true
  modes:
    - v
  alias: explain
  stop_context_insertion: true
  user_prompt: false
---

## system

You are a helpful assistant.

## user

Explain the following code:

```python
def hello_world():
    print("Hello, world!")
```

## user

Here is another user prompt.
