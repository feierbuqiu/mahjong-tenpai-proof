/* Minimal libc declarations (no system headers available in this toolchain). */
#ifndef MINIC_H
#define MINIC_H
#include <stdint.h>
#include <stddef.h>
#include <stdarg.h>
typedef struct _iobuf_opaque FILE;
int printf(const char *fmt, ...);
int sprintf(char *buf, const char *fmt, ...);
int snprintf(char *buf, size_t n, const char *fmt, ...);
int fprintf(FILE *f, const char *fmt, ...);
FILE *fopen(const char *path, const char *mode);
int fclose(FILE *f);
size_t fwrite(const void *p, size_t sz, size_t n, FILE *f);
size_t fread(void *p, size_t sz, size_t n, FILE *f);
int fflush(FILE *f);
int fgetc(FILE *f);
char *fgets(char *s, int n, FILE *f);
int fputs(const char *s, FILE *f);
void *malloc(size_t n);
void *calloc(size_t n, size_t m);
void *realloc(void *p, size_t n);
void free(void *p);
void *memset(void *p, int c, size_t n);
void *memcpy(void *d, const void *s, size_t n);
void *memmove(void *d, const void *s, size_t n);
int memcmp(const void *a, const void *b, size_t n);
size_t strlen(const char *s);
int strcmp(const char *a, const char *b);
int strncmp(const char *a, const char *b, size_t n);
char *strchr(const char *s, int c);
char *strstr(const char *s, const char *t);
long strtol(const char *s, char **e, int base);
long long strtoll(const char *s, char **e, int base);
unsigned long long strtoull(const char *s, char **e, int base);
int atoi(const char *s);
void exit(int code);
void abort(void);
void qsort(void *base, size_t n, size_t sz, int (*cmp)(const void *, const void *));
typedef long clock_t;
clock_t clock(void);
#define CLOCKS_PER_SEC 1000
/* Windows threads (kernel32) */
typedef void *HANDLE;
typedef unsigned long DWORD;
typedef DWORD (__stdcall *LPTHREAD_START_ROUTINE)(void *);
HANDLE __stdcall CreateThread(void *attr, size_t stack, LPTHREAD_START_ROUTINE fn, void *arg, DWORD flags, DWORD *tid);
DWORD __stdcall WaitForSingleObject(HANDLE h, DWORD ms);
int __stdcall CloseHandle(HANDLE h);
unsigned long long __stdcall GetTickCount64(void);
#define INFINITE 0xFFFFFFFFul
#endif
