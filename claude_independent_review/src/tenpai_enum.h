/*
 * tenpai_enum.h -- enumerate every tenpai 13-tile hand exactly once.
 *
 * Method (no structural assumption about tenpai shapes):
 *   1. enumerate every winning 14-tile count vector G exactly once
 *      (standard via per-category split, then seven-pairs not already
 *       standard, then kokushi);
 *   2. for each G and each tile t in G, let H = G - t;
 *      H is tenpai with t in W(H); report H only when t == min W(H).
 *   Every tenpai H is reported exactly once: from G = H + min W(H).
 */
#ifndef TENPAI_ENUM_H
#define TENPAI_ENUM_H
#include "mjcore.h"

typedef struct { int idx, size, isP; uint8_t v[9]; } Opt;
static Opt *OPT_N, *OPT_Z;
static int nOPT_N, nOPT_Z;
static int BN_lo[16], BN_hi[16], BZ_lo[16], BZ_hi[16]; /* bucket ranges by size */

static int cmp_opt(const void *a, const void *b) {
    const Opt *x = a, *y = b;
    if (x->size != y->size) return x->size - y->size;
    return x->idx - y->idx;
}

static void build_options(void) {
    OPT_N = malloc(sizeof(Opt) * 200000);
    OPT_Z = malloc(sizeof(Opt) * 20000);
    nOPT_N = nOPT_Z = 0;
    for (int idx = 0; idx < N5_9; idx++) {
        int st = ST_N[idx];
        if (!st) continue;
        Opt o; o.idx = idx; o.isP = (st >> 1) & 1; o.size = 0;
        int x = idx;
        for (int i = 0; i < 9; i++) { o.v[i] = (uint8_t)(x % 5); x /= 5; o.size += o.v[i]; }
        if (o.size <= 14) OPT_N[nOPT_N++] = o;
    }
    for (int idx = 0; idx < N5_7; idx++) {
        int st = ST_Z[idx];
        if (!st) continue;
        Opt o; o.idx = idx; o.isP = (st >> 1) & 1; o.size = 0;
        int x = idx;
        for (int i = 0; i < 9; i++) o.v[i] = 0;
        for (int i = 0; i < 7; i++) { o.v[i] = (uint8_t)(x % 5); x /= 5; o.size += o.v[i]; }
        if (o.size <= 14) OPT_Z[nOPT_Z++] = o;
    }
    qsort(OPT_N, nOPT_N, sizeof(Opt), cmp_opt);
    qsort(OPT_Z, nOPT_Z, sizeof(Opt), cmp_opt);
    for (int s = 0; s < 16; s++) { BN_lo[s] = BN_hi[s] = BZ_lo[s] = BZ_hi[s] = 0; }
    for (int s = 0; s <= 14; s++) {
        int lo = 0; while (lo < nOPT_N && OPT_N[lo].size < s) lo++;
        int hi = lo; while (hi < nOPT_N && OPT_N[hi].size == s) hi++;
        BN_lo[s] = lo; BN_hi[s] = hi;
        lo = 0; while (lo < nOPT_Z && OPT_Z[lo].size < s) lo++;
        hi = lo; while (hi < nOPT_Z && OPT_Z[hi].size == s) hi++;
        BZ_lo[s] = lo; BZ_hi[s] = hi;
    }
}

static int is_std_win14(const uint8_t *c) {
    int I[4];
    cat_index(c, I);
    int np = 0;
    for (int k = 0; k < 4; k++) {
        int s = cat_status(k, I[k]);
        if (!s) return 0;
        np += (s >> 1) & 1;
    }
    return np == 1;
}

typedef void (*HandFn)(void *ctx, uint8_t *c, uint64_t W);

typedef struct {
    void *ctx;
    HandFn fn;
    int64_t nG_std, nG_chi_total, nG_chi_also_std, nG_kok, nH, bad;
} EnumThread;

static void process_G(EnumThread *et, uint8_t *c) {
    for (int t = 0; t < NT; t++) {
        if (!c[t]) continue;
        c[t]--;
        uint64_t W = waits_all(c);
        if (!((W >> t) & 1)) et->bad++;            /* would mean G was not winning */
        else if (ctz64(W) == t) { et->nH++; et->fn(et->ctx, c, W); }
        c[t]++;
    }
}

/* work items: [0, nOPT_N) standard with m-option i; then 561 seven-pairs items (a<b); then kokushi */
static int64_t g_items_total;
static volatile int64_t g_next_item;
static int CHI_A[600], CHI_B[600], nCHI;

static void enum_item(EnumThread *et, int64_t item) {
    uint8_t c[NT];
    if (item < nOPT_N) {
        memset(c, 0, NT);
        const Opt *om = &OPT_N[item];
        memcpy(c, om->v, 9);
        int r1 = 14 - om->size;
        for (int sp = 0; sp <= r1; sp++)
            for (int ip = BN_lo[sp]; ip < BN_hi[sp]; ip++) {
                const Opt *op = &OPT_N[ip];
                int np2 = om->isP + op->isP;
                if (np2 > 1) continue;
                memcpy(c + 9, op->v, 9);
                int r2 = r1 - sp;
                for (int ss = 0; ss <= r2; ss++)
                    for (int is = BN_lo[ss]; is < BN_hi[ss]; is++) {
                        const Opt *os = &OPT_N[is];
                        int np3 = np2 + os->isP;
                        if (np3 > 1) continue;
                        memcpy(c + 18, os->v, 9);
                        int r3 = r2 - ss;
                        for (int iz = BZ_lo[r3]; iz < BZ_hi[r3]; iz++) {
                            const Opt *oz = &OPT_Z[iz];
                            if (np3 + oz->isP != 1) continue;
                            memcpy(c + 27, oz->v, 7);
                            et->nG_std++;
                            process_G(et, c);
                        }
                    }
            }
        return;
    }
    item -= nOPT_N;
    if (item < nCHI) {
        int a = CHI_A[item], b = CHI_B[item];
        int t[7];
        t[0] = a; t[1] = b;
        for (t[2] = b + 1; t[2] < NT; t[2]++)
            for (t[3] = t[2] + 1; t[3] < NT; t[3]++)
                for (t[4] = t[3] + 1; t[4] < NT; t[4]++)
                    for (t[5] = t[4] + 1; t[5] < NT; t[5]++)
                        for (t[6] = t[5] + 1; t[6] < NT; t[6]++) {
                            memset(c, 0, NT);
                            for (int i = 0; i < 7; i++) c[t[i]] = 2;
                            et->nG_chi_total++;
                            if (is_std_win14(c)) { et->nG_chi_also_std++; continue; }
                            process_G(et, c);
                        }
        return;
    }
    item -= nCHI;
    if (item == 0) {
        for (int j = 0; j < 13; j++) {
            memset(c, 0, NT);
            for (int i = 0; i < 13; i++) c[ORPHANS[i]] = 1;
            c[ORPHANS[j]] = 2;
            if (is_std_win14(c)) continue;
            et->nG_kok++;
            process_G(et, c);
        }
    }
}

static DWORD __stdcall enum_worker(void *arg) {
    EnumThread *et = (EnumThread *)arg;
    for (;;) {
        int64_t it = __atomic_fetch_add(&g_next_item, 1, __ATOMIC_RELAXED);
        if (it >= g_items_total) break;
        enum_item(et, it);
    }
    return 0;
}

static void enum_prepare(void) {
    build_options();
    nCHI = 0;
    for (int a = 0; a < NT; a++)
        for (int b = a + 1; b < NT; b++) { CHI_A[nCHI] = a; CHI_B[nCHI] = b; nCHI++; }
    g_items_total = (int64_t)nOPT_N + nCHI + 1;
}

/* run enumeration with nthreads workers; ets[i].ctx / .fn must be set by caller */
static void enum_run(EnumThread *ets, int nthreads) {
    g_next_item = 0;
    HANDLE h[64];
    for (int i = 0; i < nthreads; i++) h[i] = CreateThread(0, 0, enum_worker, &ets[i], 0, 0);
    for (int i = 0; i < nthreads; i++) { WaitForSingleObject(h[i], INFINITE); CloseHandle(h[i]); }
}

#endif
