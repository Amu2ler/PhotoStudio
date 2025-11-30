# compressor_c/Makefile
CC = gcc
CFLAGS = -std=c11 -O2 -Wall -Wextra -pedantic

TARGET = huff
OBJS = main.o huffman.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJS)

main.o: main.c huffman.h
	$(CC) $(CFLAGS) -c main.c

huffman.o: huffman.c huffman.h
	$(CC) $(CFLAGS) -c huffman.c

clean:
	rm -f $(TARGET) $(OBJS)
