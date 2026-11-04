/* BrainSh: Brainfuck with an opt-in shell command instruction. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define TAPE_SIZE 30000

typedef struct { char op; char *command; size_t jump; } Instruction;

static void cleanup(Instruction *program, size_t count) {
    for (size_t i = 0; i < count; i++) free(program[i].command);
    free(program);
}

int main(int argc, char **argv) {
    int allow_shell = 0;
    const char *path = NULL;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--allow-shell") == 0) allow_shell = 1;
        else if (!path) path = argv[i];
        else { fprintf(stderr, "Usage: %s [--allow-shell] program.bsh\n", argv[0]); return 2; }
    }
    if (!path) { fprintf(stderr, "Usage: %s [--allow-shell] program.bsh\n", argv[0]); return 2; }
    FILE *file = fopen(path, "rb");
    if (!file) { perror(path); return 1; }
    Instruction *program = NULL;
    size_t *stack = NULL, count = 0, depth = 0;
    int c, result = 1;
    while ((c = fgetc(file)) != EOF) {
        if (!strchr("><+-.,[]!", c)) continue;
        Instruction *next = realloc(program, (count + 1) * sizeof(*program));
        if (!next) { fprintf(stderr, "Out of memory\n"); goto done; }
        program = next;
        program[count] = (Instruction){(char)c, NULL, 0};
        count++;
        if (c == '!') {
            if (fgetc(file) != '{') { fprintf(stderr, "Expected '{' immediately after '!'\n"); goto done; }
            size_t len = 0;
            while ((c = fgetc(file)) != EOF && c != '}') {
                char *s = realloc(program[count - 1].command, len + 2);
                if (!s) { fprintf(stderr, "Out of memory\n"); goto done; }
                program[count - 1].command = s;
                s[len++] = (char)c;
                s[len] = '\0';
            }
            if (c == EOF) { fprintf(stderr, "Unclosed shell command\n"); goto done; }
            if (!program[count - 1].command) {
                program[count - 1].command = calloc(1, 1);
                if (!program[count - 1].command) { fprintf(stderr, "Out of memory\n"); goto done; }
            }
        } else if (c == '[') {
            size_t *s = realloc(stack, (depth + 1) * sizeof(*stack));
            if (!s) { fprintf(stderr, "Out of memory\n"); goto done; }
            stack = s; stack[depth++] = count - 1;
        } else if (c == ']') {
            if (!depth) { fprintf(stderr, "Unmatched ']'\n"); goto done; }
            size_t opening = stack[--depth];
            program[opening].jump = count - 1;
            program[count - 1].jump = opening;
        }
    }
    if (ferror(file)) { perror(path); goto done; }
    if (depth) { fprintf(stderr, "Unmatched '['\n"); goto done; }
    uint8_t tape[TAPE_SIZE] = {0};
    size_t pointer = 0;
    for (size_t pc = 0; pc < count; pc++) {
        switch (program[pc].op) {
        case '>': if (pointer == TAPE_SIZE - 1) { fprintf(stderr, "Tape pointer moved past the end\n"); goto done; } pointer++; break;
        case '<': if (!pointer) { fprintf(stderr, "Tape pointer moved before the start\n"); goto done; } pointer--; break;
        case '+': tape[pointer]++; break;
        case '-': tape[pointer]--; break;
        case '.': if (putchar(tape[pointer]) == EOF) { perror("stdout"); goto done; } break;
        case ',': { int input = getchar(); tape[pointer] = input == EOF ? 0 : (uint8_t)input; break; }
        case '[': if (!tape[pointer]) pc = program[pc].jump; break;
        case ']': if (tape[pointer]) pc = program[pc].jump; break;
        case '!':
            if (!allow_shell) { fprintf(stderr, "Shell commands require --allow-shell\n"); goto done; }
            if (fflush(stdout) == EOF) { perror("stdout"); goto done; }
            if (system(program[pc].command) != 0) { fprintf(stderr, "Shell command failed: %s\n", program[pc].command); goto done; }
            break;
        }
    }
    result = 0;
done:
    fclose(file);
    free(stack);
    cleanup(program, count);
    return result;
}
