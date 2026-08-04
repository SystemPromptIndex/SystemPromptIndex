---
id: "12-factor-agents/12-factor-agents_-_packages_walkthroughgen_prompt"
company: "12-factor-agents"
product: "12-factor-agents - packages walkthroughgen prompt"
category: "general-purpose"
annotation: "ai"
source_file: "packages_walkthroughgen_prompt.md"
---

Walkthroughgen is a tool for creating walkthroughs, tutorials, readmes, and documentation.

## Usage

You create a walkthrough by writing a simple yaml file that describes the walkthrough. In the file, you reference the incremental files that should exist at each step of the walkthrough

```
├── walkthrough
│   ├── 00-package-lock.json
│   ├── 00-package.json
│   ├── 01-index.ts
│   ├── 02-cli.ts
│   └── 02-index.ts
└── walkthrough.yaml
```

Your walkthrough.yaml file might look like this (runnable example in [examples/typescript-cli](./examples/typescript))

```yaml
title: "setting up a typescript cli"
text: "this is a walkthrough for setting up a typescript cli"
targets:
  - markdown: "./build/walkthrough.md" # generates a walkthrough.md file
    onChange: # default behavior - on changes, show diffs and cp commands
      diff: true
      cp: true
    newFiles: # when new files are created, just show the copy command
      cat: false
      cp: true
  - final: "./build/final" # outputs the final project to the final folder
  - folders: "./build/by-section" # creates a separate working folder for each section
sections:
  - name: setup
    title: "Copy initial files"
    steps:
      - file: {src: ./walkthrough/00-package.json, dest: package.json}
      - file: {src: ./walkthrough/00-package-lock.json, dest: package-lock.json}
      - file: {src: ./walkthrough/00-tsconfig.json, dest: tsconfig.json}
  - name: initialize
    title: "Initialize the project"
    steps:
      - text: "initialize the project"
        command: |
          npm install
      - text: "then add index.ts"
        file: {src: ./walkthrough/01-index.ts, dest: src/index.ts}
      - text: "run it with tsx"
        command: |
          npx tsx src/index.ts
        results:
          - text: "you should see a hello world message"
            code: |
              hello world
  - name: add-cli
    title: "Add a CLI"
    steps:
      - text: "add a cli"
        file: {src: ./walkthrough/02-cli.ts, dest: src/cli.ts}
      - text: "add a cli"
        file: {src: ./walkthrough/02-index.ts, dest: src/index.ts}
```

Build the project with:

```
npm i -g wtg
wtg build
```

based on your targets, this would create the following files

```
├── walkthrough
│   ├── 00-package-lock.json
│   ├── 00-package.json
│   ├── 01-index.ts
│   ├── 02-cli.ts
│   └── 02-index.ts
├── build
│   ├── by-section
│   │   ├── 00-initialize # only contains the files in `init`
│   │   │   ├── readme.md # contains steps for this section
│   │   │   ├── package.json
│   │   │   ├── package-lock.json
│   │   │   └── tsconfig.json
│   │   └── 01-add-cli # contains the files up to the START of section 1
│   │       ├── readme.md # contains steps for this section
│   │       ├── package.json
│   │       ├── package-lock.json
│   │       ├── tsconfig.json
│   │       └── src
│   │           └── index.ts
│   ├── final
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   ├── tsconfig.json
│   │   └── src
│   │       ├── cli.ts
│   │       └── index.ts
│   └── walkthrough.md

and your walkthrough.md file will look like:

```markdown
# Setting up a typescript cli

this is a walkthrough for setting up a typescript cli

## Copy initial files

  cp walkthrough/00-package.json package.json
  cp walkthrough/00-package-lock.json package-lock.json
  cp walkthrough/00-tsconfig.json tsconfig.json

## Initialize the project

initialize the project

     npm install

then add index.ts


    cp walkthrough/01-index.ts src/index.ts

and run it with tsx

    npx tsx src/index.ts

you should see a hello world message

    hello world

## Add a CLI

add a cli

    ```
    ```
 
    cp walkthrough/02-cli.ts src/cli.ts

update index.ts to use the cli

    ```diff
      const main = async () => {
      +    return cli();
      };
        
      main();
    ```

    or just:

    cp walkthrough/02-index.ts src/index.ts

```

## Features

### Targets

- `file`: generates a single markdown file
- `folder`: creates a set of folders, one for each section
- `final`: outputs the final project to the current directory

### Init



### Sections

### Steps

#### Step 


## Walkthrough.yaml for walkthroughgen

## Implementation Plan

- [ ] implement core walkthroughgen CLI - `wtg build` # defaults to walkthrough.yaml in current directory
- Scope 1: generating walkthrough.md
  - [ ] create end-to-end test for a simple walkthrough file, just a single yaml file with no sections
  - [ ] create end-to-end test for a walkthrough file with a single section
  - [ ] test generation of diffs and cp commands
- Scope 2: generating final/ project build
  - [ ] create end-to-end test for a walkthrough file with a final target
- Scope 3: generating by-section project builds with readmes
  - [ ] create end-to-end test for a walkthrough file with a by-section target
