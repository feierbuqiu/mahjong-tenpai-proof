/*
 * reorder_plan.c -- reorder the codes within each class of a k=4 plan, most useful first.
 * For every active part of a tenpai hand (the units of the coverage proof) it counts which codes
 * of the unit's class fit in it, then sorts each class's codes by that count (ties keep the
 * original order).  Only the order within a class changes: every class keeps exactly its codes,
 * so kernel look-ups find a fitting code sooner without changing what the proof checks.
 * usage: reorder_plan.exe in.txt out.txt
 */
#include "../../src/mjcore.h"

static int PK, nPC, nCodes;
#define MAX_CLASSES (1 << 16)         /* capacity of PC_mask, PC_start, PC_n */
#define CODE_BYTES (1 << 22)          /* capacity of CODE */
#define MAX_CLASS_CODES 4096          /* capacity of the sort buffer in main */
static uint64_t *PC_mask;
static int *PC_start, *PC_n;
static uint8_t *CODE;
#define PM_SIZE (1 << 16)
static uint64_t PM_key[PM_SIZE];
static int PM_val[PM_SIZE];
static inline uint32_t hmix(uint64_t x) {
    x ^= x >> 33; x *= 0xff51afd7ed558ccdull; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ull; x ^= x >> 33;
    return (uint32_t)x;
}
static int pm_find(uint64_t k) {
    uint32_t h = hmix(k) & (PM_SIZE - 1);
    while (PM_key[h]) {
        if (PM_key[h] == k) return PM_val[h];
        h = (h + 1) & (PM_SIZE - 1);
    }
    return -1;
}
static int load_plan(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    int cap = 1 << 20;
    char *line = malloc(cap);
    PC_mask = malloc(sizeof(uint64_t) * MAX_CLASSES); PC_start = malloc(sizeof(int) * MAX_CLASSES);
    PC_n = malloc(sizeof(int) * MAX_CLASSES); CODE = malloc(CODE_BYTES);
    if (!line || !PC_mask || !PC_start || !PC_n || !CODE) { printf("out of memory\n"); fclose(f); return 0; }
    while (fgets(line, cap, f)) {
        char *p = line, *e;
        if (*p == '#' || *p == '\n' || !*p) continue;
        uint64_t mask = strtoull(p, &e, 16); p = e;
        int n = (int)strtol(p, &e, 10); p = e;
        int k = (int)strtol(p, &e, 10); p = e;
        if (k < 1 || k > 8 || (PK && k != PK) || n < 0 || n > MAX_CLASS_CODES || nPC >= MAX_CLASSES ||
            (size_t)(nCodes + n) * (size_t)k > CODE_BYTES) {
            printf("plan exceeds the supported size or is malformed (class %d)\n", nPC);
            fclose(f); return 0;
        }
        PK = k;
        PC_mask[nPC] = mask; PC_start[nPC] = nCodes; PC_n[nPC] = n;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < k; j++) { CODE[(size_t)nCodes * k + j] = (uint8_t)strtol(p, &e, 10); p = e; }
            nCodes++;
        }
        uint32_t h = hmix(mask) & (PM_SIZE - 1);
        while (PM_key[h]) h = (h + 1) & (PM_SIZE - 1);
        PM_key[h] = mask; PM_val[h] = nPC;
        nPC++;
    }
    fclose(f);
    return 1;
}
static inline int code_fits(int ci, const uint8_t *c) {
    uint8_t need[NT];
    memset(need, 0, NT);
    for (int j = 0; j < PK; j++) need[CODE[ci * PK + j]]++;
    for (int j = 0; j < PK; j++) { int t = CODE[ci * PK + j]; if (need[t] > c[t]) return 0; }
    return 1;
}
/* first fitting code of class W in hand c; returns code index or -1; -2 if class missing */
static int find_code(uint64_t W, const uint8_t *c) {
    int ci = pm_find(W);
    if (ci < 0) return -2;
    for (int i = 0; i < PC_n[ci]; i++) if (code_fits(PC_start[ci] + i, c)) return PC_start[ci] + i;
    return -1;
}
static int OFF[4] = {0, 9, 18, 27}, LEN[4] = {9, 9, 9, 7};
static inline int st(int k, int idx) { return k < 3 ? ST_N[idx] : ST_Z[idx]; }
static void vec_of(int k, int idx, uint8_t *v) { for (int i = 0; i < LEN[k]; i++) { v[i] = idx % 5; idx /= 5; } }
static int vsize(int k, int idx) { int s = 0; for (int i = 0; i < LEN[k]; i++) { s += idx % 5; idx /= 5; } return s; }
static uint64_t WPm(int k, int idx) {
    uint8_t v[9]; vec_of(k, idx, v); uint64_t W = 0;
    for (int i = 0; i < LEN[k]; i++) if (v[i] < 4 && (st(k, idx + P5[i]) & 2)) W |= 1ull << (OFF[k] + i);
    return W;
}
static uint64_t WMm(int k, int idx) {
    uint8_t v[9]; vec_of(k, idx, v); uint64_t W = 0;
    for (int i = 0; i < LEN[k]; i++) if (v[i] < 4 && (st(k, idx + P5[i]) & 1)) W |= 1ull << (OFF[k] + i);
    return W;
}
static int NV(int k) { return k < 3 ? N5_9 : N5_7; }


/* exception unit: no code inside A. Check: for every meld m inside the allowed filler categories
   (catmask), some code of class W fits A+m. Returns number of melds violating it. */
static int meld_rule_violations(const uint8_t *A, uint64_t W, int catmask, int *nmelds) {
    int bad = 0; *nmelds = 0;
    uint8_t h[NT];
    int bm[200], bk[200], nb = 0;
    for (int m = 0; m < NT; m++) {
        if (!((catmask >> CAT[m]) & 1)) continue;
        for (int kind = 0; kind < 2; kind++) {
            memcpy(h, A, NT);
            if (kind == 0) h[m] += 3;
            else { if (m >= 27 || POS[m] > 6) continue; h[m]++; h[m + 1]++; h[m + 2]++; }
            (*nmelds)++;
            if (find_code(W, h) < 0) { bad++; bm[nb] = m; bk[nb] = kind; nb++; }
        }
    }
    /* F = 3 melds; if all three are bad, check A+m1+m2+m3 directly (multisets with repetition) */
    static int64_t triples = 0, triple_fail = 0, maxbad = 0;
    if (nb > maxbad) maxbad = nb;
    for (int i = 0; i < nb; i++)
        for (int j = i; j < nb; j++)
            for (int l = j; l < nb; l++) {
                memcpy(h, A, NT);
                int ms[3] = {i, j, l}, okc = 1;
                for (int q = 0; q < 3; q++) {
                    int m = bm[ms[q]];
                    if (bk[ms[q]] == 0) h[m] += 3; else { h[m]++; h[m + 1]++; h[m + 2]++; }
                }
                for (int t = 0; t < NT; t++) if (h[t] > 4) okc = 0;
                if (!okc) continue;
                triples++;
                if (find_code(W, h) < 0) {
                    triple_fail++;
                    char b[300], w[300]; hand_to_str(h, b); mask_to_str(W, w);
                    printf("TRIPLE FAIL: %s W={%s}\n", b, w);
                }
            }
    if (nb) {
        char b[300], w[300]; hand_to_str(A, b); mask_to_str(W, w);
        printf("exception A=%s W={%s}: %d bad melds; cumulative bad-triples %lld (fail %lld), max bad %lld\n",
               b, w, nb, (long long)triples, (long long)triple_fail, (long long)maxbad);
    }
    return bad;
}

static int64_t *USE;
static int64_t exc_units=0, exc_bad=0, exc_size_ne4=0; /* per code: number of units where it is the first hit */
static int lst[4][70000], nl[4];
static uint64_t LWM[4][70000];
static uint8_t LP[4][70000], LS[4][70000];
static int AP[4][600], nap[4];


static int64_t *FITCNT;
static int64_t scan_sum = 0, scan_units = 0;
static int scan_len(uint64_t W, const uint8_t *c) {
    int ci = pm_find(W); if (ci < 0) return -1;
    for (int i = 0; i < PC_n[ci]; i++) if (code_fits(PC_start[ci] + i, c)) return i + 1;
    return -1;
}
static void count_fits(uint64_t W, const uint8_t *c) {
    int ci = pm_find(W); if (ci < 0) return;
    int s = scan_len(W, c); if (s > 0) { scan_sum += s; scan_units++; }
    for (int i = 0; i < PC_n[ci]; i++) if (code_fits(PC_start[ci] + i, c)) FITCNT[PC_start[ci] + i]++;
}
static void for_all_units(int pass) {
    uint8_t h[NT];
    for (int k = 0; k < 4; k++)
        for (int idx = 0; idx < NV(k); idx++) {
            int s = vsize(k, idx);
            if (s % 3 != 1 || s > 13 || s == 1) continue;
            uint64_t W = WPm(k, idx); if (!W) continue;
            memset(h, 0, NT); vec_of(k, idx, h + OFF[k]);
            if (pass == 0) count_fits(W, h); else { int q = scan_len(W, h); if (q > 0) { scan_sum += q; scan_units++; } }
        }
    for (int x = 0; x < 4; x++)
        for (int y = x + 1; y < 4; y++)
            for (int i = 0; i < nl[x]; i++)
                for (int j = 0; j < nl[y]; j++) {
                    if (LS[x][i] + LS[y][j] > 13) continue;
                    uint64_t W = (LP[y][j] ? LWM[x][i] : 0) | (LP[x][i] ? LWM[y][j] : 0);
                    if (!W) continue;
                    memset(h, 0, NT); vec_of(x, lst[x][i], h + OFF[x]); vec_of(y, lst[y][j], h + OFF[y]);
                    if (pass == 0) count_fits(W, h); else { int q = scan_len(W, h); if (q > 0) { scan_sum += q; scan_units++; } }
                }
}
static int64_t *KEYCNT;
static int cmp_code(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    if (KEYCNT[x] != KEYCNT[y]) return KEYCNT[x] > KEYCNT[y] ? -1 : 1;
    return x - y;
}
int main(int argc, char **argv) {
    mj_init();
    if (argc < 3 || !load_plan(argv[1])) { printf("usage: reorder_plan in.txt out.txt\n"); return 1; }
    FITCNT = calloc(nCodes, sizeof(int64_t));
    if (!FITCNT) { printf("out of memory\n"); return 1; }
    for (int k = 0; k < 4; k++) {
        nl[k] = 0;
        for (int idx = 0; idx < NV(k); idx++) {
            int s = vsize(k, idx);
            if (s % 3 != 2 || s > 11) continue;
            uint64_t wm = WMm(k, idx); int p = (st(k, idx) >> 1) & 1;
            if (!wm && !p) continue;
            lst[k][nl[k]] = idx; LWM[k][nl[k]] = wm; LP[k][nl[k]] = (uint8_t)p; LS[k][nl[k]] = (uint8_t)s; nl[k]++;
        }
    }
    for_all_units(0);
    printf("before: units %lld, average scan length %.2f\n", (long long)scan_units, (double)scan_sum / scan_units);
    KEYCNT = FITCNT;
    size_t code_bytes = (size_t)nCodes * (size_t)PK;
    uint8_t *NEW = malloc(code_bytes);
    int *ord = malloc(sizeof(int) * MAX_CLASS_CODES);
    if (!NEW || !ord) { printf("out of memory\n"); return 1; }
    for (int ci = 0; ci < nPC; ci++) {
        for (int i = 0; i < PC_n[ci]; i++) ord[i] = PC_start[ci] + i;
        qsort(ord, PC_n[ci], sizeof(int), cmp_code);
        for (int i = 0; i < PC_n[ci]; i++)
            memcpy(NEW + (size_t)(PC_start[ci] + i) * PK, CODE + (size_t)ord[i] * PK, PK);
    }
    memcpy(CODE, NEW, code_bytes);
    scan_sum = scan_units = 0;
    for_all_units(1);
    printf("after:  units %lld, average scan length %.2f\n", (long long)scan_units, (double)scan_sum / scan_units);
    FILE *f = fopen(argv[2], "wb");
    if (!f) { printf("cannot write %s\n", argv[2]); return 1; }
    char buf[64];
    for (int ci = 0; ci < nPC; ci++) {
        int L = snprintf(buf, sizeof buf, "%llx %d %d", (unsigned long long)PC_mask[ci], PC_n[ci], PK);
        fwrite(buf, 1, L, f);
        for (int i = 0; i < PC_n[ci] * PK; i++) {
            L = snprintf(buf, sizeof buf, " %d", CODE[(size_t)PC_start[ci] * PK + i]);
            fwrite(buf, 1, L, f);
        }
        fwrite("\n", 1, 1, f);
    }
    fclose(f);
    return 0;
}
