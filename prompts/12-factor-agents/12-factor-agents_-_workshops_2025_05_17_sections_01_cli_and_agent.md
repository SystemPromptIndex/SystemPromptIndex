---
id: "12-factor-agents/12-factor-agents_-_workshops_2025_05_17_sections_01_cli_and_agent"
company: "12-factor-agents"
product: "12-factor-agents - workshops 2025 05 17 sections 01 cli and agent ..."
category: "general-purpose"
annotation: "ai"
source_file: "clone_workshops_2025-05-17_sections_01-cli-and-agent_README.md"
---

# Chapter 1 - CLI and Agent Loop

Now let's add BAML and create our first agent with a CLI interface.

First, we'll need to install [BAML](https://github.com/boundaryml/baml)
which is a tool for prompting and structured outputs.


    npm install @boundaryml/baml

Initialize BAML

    npx baml-cli init

Remove default resume.baml

    rm baml_src/resume.baml

Add our starter agent, a single baml prompt that we'll build on

    cp ./walkthrough/01-agent.baml baml_src/agent.baml

<details>
<summary>show file</summary>

```rust
// ./walkthrough/01-agent.baml
class DoneForNow {
  intent "done_for_now"
  message string 
}

client<llm> Qwen3 {
  provider "openai-generic"
  options {
    base_url env.BASETEN_BASE_URL
    api_key env.BASETEN_API_KEY 
  }
}

function DetermineNextStep(
    thread: string 
) -> DoneForNow {
    client Qwen3

    // use /nothink for now because the thinking tokens (or streaming thereof) screw with baml (i think (no pun intended))
    prompt #"
        {{ _.role("system") }}

        /nothink 

        You are a helpful assistant that can help with tasks.

        {{ _.role("user") }}

        You are working on the following thread:

        {{ thread }}

        What should the next step be?

        {{ ctx.output_format }}
    "#
}

test HelloWorld {
  functions [DetermineNextStep]
  args {
    thread #"
      {
        "type": "user_input",
        "data": "hello!"
      }
    "#
  }
}
```

</details>

Generate BAML client code

    npx baml-cli generate

Enable BAML logging for this section

    export BAML_LOG=debug

Add the CLI interface

    cp ./walkthrough/01-cli.ts src/cli.ts

<details>
<summary>show file</summary>

```ts
// ./walkthrough/01-cli.ts
// cli.ts lets you invoke the agent loop from the command line

import { agentLoop, Thread, Event } from "./agent";

export async function cli() {
    // Get command line arguments, skipping the first two (node and script name)
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.error("Error: Please provide a message as a command line argument");
        process.exit(1);
    }

    // Join all arguments into a single message
    const message = args.join(" ");

    // Create a new thread with the user's message as the initial event
    const thread = new Thread([{ type: "user_input", data: message }]);

    // Run the agent loop with the thread
    const result = await agentLoop(thread);
    console.log(result);
}
```

</details>

Update index.ts to use the CLI

```diff
src/index.ts
+import { cli } from "./cli"
+
 async function hello(): Promise<void> {
     console.log('hello, world!')
 
 async function main() {
-    await hello()
+    await cli()
 }
 
```

<details>
<summary>skip this step</summary>

    cp ./walkthrough/01-index.ts src/index.ts

</details>

Add the agent implementation

    cp ./walkthrough/01-agent.ts src/agent.ts

<details>
<summary>show file</summary>

```ts
// ./walkthrough/01-agent.ts
import { b } from "../baml_client";

// tool call or a respond to human tool
type AgentResponse = Awaited<ReturnType<typeof b.DetermineNextStep>>;

export interface Event {
    type: string
    data: any;
}

export class Thread {
    events: Event[] = [];

    constructor(events: Event[]) {
        this.events = events;
    }

    serializeForLLM() {
        // can change this to whatever custom serialization you want to do, XML, etc
        // e.g. https://github.com/got-agents/agents/blob/59ebbfa236fc376618f16ee08eb0f3bf7b698892/linear-assistant-ts/src/agent.ts#L66-L105
        return JSON.stringify(this.events);
    }
}

// right now this just runs one turn with the LLM, but
// we'll update this function to handle all the agent logic
export async function agentLoop(thread: Thread): Promise<AgentResponse> {
    const nextStep = await b.DetermineNextStep(thread.serializeForLLM());
    return nextStep;
}
```

</details>

The the BAML code is configured to use BASETEN_API_KEY by default

To get a Baseten API key and URL, create an account at [baseten.co](https://baseten.co),
and then deploy [Qwen3 32B from the model library](https://www.baseten.co/library/qwen-3-32b/).

```rust 
  function DetermineNextStep(thread: string) -> DoneForNow {
      client Qwen3
      // ...
```

If you want to run the example with no changes, you can set the BASETEN_API_KEY env var to any valid baseten key.

If you want to try swapping out the model, you can change the `client` line.

[Docs on baml clients can be found here](https://docs.boundaryml.com/guide/baml-basics/switching-llms)

For example, you can configure [gemini](https://docs.boundaryml.com/ref/llm-client-providers/google-ai-gemini) 
or [anthropic](https://docs.boundaryml.com/ref/llm-client-providers/anthropic) as your model provider.

For example, to use openai with an OPENAI_API_KEY, you can do:

    client "openai/gpt-4o"


Set your env vars

    export BASETEN_API_KEY=...
    export BASETEN_BASE_URL=...

Try it out

    npx tsx src/index.ts hello

you should see a familiar response from the model

    {
      intent: 'done_for_now',
      message: 'Hello! How can I assist you today?'
    }
