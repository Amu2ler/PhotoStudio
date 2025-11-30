// compressor_c/huffman.c
#include "huffman.h"

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

typedef struct HuffmanNode {
    uint8_t value;
    uint64_t freq;
    struct HuffmanNode *left;
    struct HuffmanNode *right;
    int is_leaf;
} HuffmanNode;

typedef struct {
    uint32_t bits;
    uint8_t length;
    int valid;
} Code;

typedef struct {
    FILE *fp;
    uint8_t buffer;
    int bit_count;
} BitWriter;

typedef struct {
    FILE *fp;
    int buffer;
    int bits_left;
} BitReader;

static void bw_init(BitWriter *bw, FILE *fp) {
    bw->fp = fp;
    bw->buffer = 0;
    bw->bit_count = 0;
}

static void bw_write_bit(BitWriter *bw, int bit) {
    bw->buffer = (bw->buffer << 1) | (bit & 1);
    bw->bit_count++;
    if (bw->bit_count == 8) {
        fputc(bw->buffer, bw->fp);
        bw->buffer = 0;
        bw->bit_count = 0;
    }
}

static void bw_write_bits(BitWriter *bw, uint32_t bits, uint8_t length) {
    for (int i = length - 1; i >= 0; --i) {
        int bit = (bits >> i) & 1;
        bw_write_bit(bw, bit);
    }
}

static void bw_flush(BitWriter *bw) {
    if (bw->bit_count > 0) {
        bw->buffer <<= (8 - bw->bit_count);
        fputc(bw->buffer, bw->fp);
        bw->buffer = 0;
        bw->bit_count = 0;
    }
}

static void br_init(BitReader *br, FILE *fp) {
    br->fp = fp;
    br->buffer = 0;
    br->bits_left = 0;
}

static int br_read_bit(BitReader *br) {
    if (br->bits_left == 0) {
        br->buffer = fgetc(br->fp);
        if (br->buffer == EOF) {
            return -1;
        }
        br->bits_left = 8;
    }
    int bit = (br->buffer >> (br->bits_left - 1)) & 1;
    br->bits_left--;
    return bit;
}

static HuffmanNode *create_node(uint8_t value, uint64_t freq, int is_leaf) {
    HuffmanNode *node = (HuffmanNode *)malloc(sizeof(HuffmanNode));
    if (!node) return NULL;
    node->value = value;
    node->freq = freq;
    node->left = NULL;
    node->right = NULL;
    node->is_leaf = is_leaf;
    return node;
}

static void free_tree(HuffmanNode *node) {
    if (!node) return;
    free_tree(node->left);
    free_tree(node->right);
    free(node);
}

static HuffmanNode *build_tree(uint64_t freq[256]) {
    HuffmanNode *nodes[512];
    int count = 0;

    for (int i = 0; i < 256; ++i) {
        if (freq[i] > 0) {
            nodes[count++] = create_node((uint8_t)i, freq[i], 1);
        }
    }

    if (count == 0) {
        return NULL;
    }
    if (count == 1) {
        // cas dégénéré : un seul symbole
        HuffmanNode *root = create_node(0, nodes[0]->freq, 0);
        root->left = nodes[0];
        root->right = create_node(nodes[0]->value, nodes[0]->freq, 1);
        return root;
    }

    while (count > 1) {
        // deux plus petites fréquences
        int min1 = -1, min2 = -1;
        for (int i = 0; i < count; ++i) {
            if (min1 == -1 || nodes[i]->freq < nodes[min1]->freq) {
                min2 = min1;
                min1 = i;
            } else if (min2 == -1 || nodes[i]->freq < nodes[min2]->freq) {
                min2 = i;
            }
        }

        HuffmanNode *a = nodes[min1];
        HuffmanNode *b = nodes[min2];
        HuffmanNode *parent = create_node(0, a->freq + b->freq, 0);
        parent->left = a;
        parent->right = b;

        // remplacer min1 par parent, supprimer min2
        nodes[min1] = parent;
        nodes[min2] = nodes[count - 1];
        count--;
    }

    return nodes[0];
}

static void build_codes_recursive(HuffmanNode *node, Code table[256], uint32_t bits, uint8_t length) {
    if (!node) return;
    if (node->is_leaf) {
        table[node->value].bits = bits;
        table[node->value].length = length;
        table[node->value].valid = 1;
        return;
    }
    build_codes_recursive(node->left, table, (bits << 1), length + 1);
    build_codes_recursive(node->right, table, (bits << 1) | 1, length + 1);
}

static void build_codes(HuffmanNode *root, Code table[256]) {
    for (int i = 0; i < 256; ++i) {
        table[i].bits = 0;
        table[i].length = 0;
        table[i].valid = 0;
    }
    build_codes_recursive(root, table, 0, 0);
}

static int write_header(FILE *out, uint64_t original_size, uint64_t freq[256]) {
    // Magic "HF1" + version
    if (fwrite("HF1", 1, 3, out) != 3) return -1;
    uint8_t version = 1;
    if (fwrite(&version, 1, 1, out) != 1) return -1;

    // taille originale (uint64_t little endian)
    if (fwrite(&original_size, sizeof(uint64_t), 1, out) != 1) return -1;

    // fréquences (uint64_t pour chaque symbole)
    if (fwrite(freq, sizeof(uint64_t), 256, out) != 256) return -1;

    return 0;
}

static int read_header(FILE *in, uint64_t *original_size, uint64_t freq[256]) {
    char magic[3];
    if (fread(magic, 1, 3, in) != 3) return -1;
    if (memcmp(magic, "HF1", 3) != 0) return -1;

    uint8_t version;
    if (fread(&version, 1, 1, in) != 1) return -1;
    if (version != 1) return -1;

    if (fread(original_size, sizeof(uint64_t), 1, in) != 1) return -1;

    if (fread(freq, sizeof(uint64_t), 256, in) != 256) return -1;

    return 0;
}

int huffman_compress(const char *input_path, const char *output_path) {
    FILE *in = fopen(input_path, "rb");
    if (!in) {
        fprintf(stderr, "Error: cannot open input file '%s'\n", input_path);
        return 1;
    }

    // taille du fichier
    fseek(in, 0, SEEK_END);
    long size = ftell(in);
    if (size < 0) {
        fclose(in);
        fprintf(stderr, "Error: ftell failed\n");
        return 1;
    }
    fseek(in, 0, SEEK_SET);

    uint8_t *data = (uint8_t *)malloc((size_t)size);
    if (!data) {
        fclose(in);
        fprintf(stderr, "Error: malloc failed\n");
        return 1;
    }

    if (fread(data, 1, (size_t)size, in) != (size_t)size) {
        fclose(in);
        free(data);
        fprintf(stderr, "Error: fread failed\n");
        return 1;
    }
    fclose(in);

    uint64_t freq[256] = {0};
    for (long i = 0; i < size; ++i) {
        freq[data[i]]++;
    }

    HuffmanNode *root = build_tree(freq);
    if (!root) {
        fprintf(stderr, "Error: cannot build Huffman tree\n");
        free(data);
        return 1;
    }

    Code table[256];
    build_codes(root, table);

    FILE *out = fopen(output_path, "wb");
    if (!out) {
        fprintf(stderr, "Error: cannot open output file '%s'\n", output_path);
        free_tree(root);
        free(data);
        return 1;
    }

    if (write_header(out, (uint64_t)size, freq) != 0) {
        fprintf(stderr, "Error: cannot write header\n");
        fclose(out);
        free_tree(root);
        free(data);
        return 1;
    }

    BitWriter bw;
    bw_init(&bw, out);

    for (long i = 0; i < size; ++i) {
        Code c = table[data[i]];
        if (!c.valid || c.length == 0) {
            fprintf(stderr, "Error: invalid code for byte %d\n", data[i]);
            fclose(out);
            free_tree(root);
            free(data);
            return 1;
        }
        bw_write_bits(&bw, c.bits, c.length);
    }

    bw_flush(&bw);
    fclose(out);
    free_tree(root);
    free(data);

    return 0;
}

int huffman_decompress(const char *input_path, const char *output_path) {
    FILE *in = fopen(input_path, "rb");
    if (!in) {
        fprintf(stderr, "Error: cannot open input file '%s'\n", input_path);
        return 1;
    }

    uint64_t original_size = 0;
    uint64_t freq[256] = {0};

    if (read_header(in, &original_size, freq) != 0) {
        fprintf(stderr, "Error: invalid header in '%s'\n", input_path);
        fclose(in);
        return 1;
    }

    HuffmanNode *root = build_tree(freq);
    if (!root) {
        fprintf(stderr, "Error: cannot rebuild Huffman tree\n");
        fclose(in);
        return 1;
    }

    uint8_t *data = (uint8_t *)malloc((size_t)original_size);
    if (!data) {
        fprintf(stderr, "Error: malloc failed\n");
        fclose(in);
        free_tree(root);
        return 1;
    }

    BitReader br;
    br_init(&br, in);

    for (uint64_t i = 0; i < original_size; ++i) {
        HuffmanNode *node = root;
        while (node && !node->is_leaf) {
            int bit = br_read_bit(&br);
            if (bit < 0) {
                fprintf(stderr, "Error: unexpected end of compressed data\n");
                free(data);
                fclose(in);
                free_tree(root);
                return 1;
            }
            node = (bit == 0) ? node->left : node->right;
        }
        if (!node) {
            fprintf(stderr, "Error: invalid bit sequence in compressed data\n");
            free(data);
            fclose(in);
            free_tree(root);
            return 1;
        }
        data[i] = node->value;
    }

    fclose(in);

    FILE *out = fopen(output_path, "wb");
    if (!out) {
        fprintf(stderr, "Error: cannot open output file '%s'\n", output_path);
        free(data);
        free_tree(root);
        return 1;
    }

    if (fwrite(data, 1, (size_t)original_size, out) != (size_t)original_size) {
        fprintf(stderr, "Error: fwrite failed\n");
        fclose(out);
        free(data);
        free_tree(root);
        return 1;
    }

    fclose(out);
    free(data);
    free_tree(root);

    return 0;
}
