// compressor_c/main.c
#include <stdio.h>
#include <string.h>
#include "huffman.h"

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr,
                "Usage:\n"
                "  %s c <input_file> <output_file>      # compress\n"
                "  %s d <input_file> <output_file>      # decompress\n",
                argv[0], argv[0]);
        return 1;
    }

    const char *mode = argv[1];
    const char *input = argv[2];
    const char *output = argv[3];

    if (strcmp(mode, "c") == 0 || strcmp(mode, "compress") == 0) {
        return huffman_compress(input, output);
    } else if (strcmp(mode, "d") == 0 || strcmp(mode, "decompress") == 0) {
        return huffman_decompress(input, output);
    } else {
        fprintf(stderr, "Unknown mode '%s'. Use 'c' or 'd'.\n", mode);
        return 1;
    }
}
