# BrainSh

BrainSh is a Brainfuck interpreter written in C, with an optional shell-command instruction. Build it from the repository root with a C99 compiler:

```sh
cc -std=c99 -Wall -Wextra -pedantic Setup/brainsh.c -o /tmp/brainsh
/tmp/brainsh Setup/hello.bsh
/tmp/brainsh --allow-shell Setup/command.bsh
```

The eight standard Brainfuck instructions (`> < + - . , [ ]`) operate on a tape of 30,000 initially zeroed 8-bit cells. Cells wrap at 0 and 255; moving outside the tape is an error. Input at EOF produces zero. Other characters are ignored, except for the extension below, so comments must avoid instruction characters.

`!{command}` runs the enclosed text through the system shell. For example, `!{printf 'Hello from the shell\n'}` runs `printf`. The command ends at the first `}`; there is no escaping or interpolation from tape cells. Brainfuck instructions inside the braces are treated as shell text. A nonzero shell result stops the interpreter with an error. Shell execution is disabled unless `--allow-shell` is passed, and executes with the user's privileges; only enable it for programs you trust.

The repository’s `./setup.sh` compiles BrainSh with Clang into a temporary directory and runs `Setup/setup.bsh`, which launches the root `setup.bf` program with shell commands enabled. That program creates the Python environment and installs the project dependencies.
