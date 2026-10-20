/*
 * build.c -- independent construction of a k = 4 plan (class -> set of ordered 4-codes).
 *
 * Correctness of the produced plan is NOT argued here: it is checked
 * afterwards, hand by hand, by census.exe over all 92,371,838 tenpai hands.
 * This program only needs good heuristics.
 *
 * Covering units (derived from the actual tenpai hands):
 *   - standard-form tenpai hand H: active categories = categories whose tile
 *     count is not divisible by 3, core A = tiles of H in active categories.
 *       |A| >= 4 : unit (class, A); any code whose multiset is contained in A
 *                  serves every hand with that (class, A).
 *       |A| == 1 : single wait x, rest of the hand complete ("tanki family");
 *                  served by the reserved codes {x} + one meld of another category.
 *   - seven-pairs-only hand (6 pairs + single x): served by reserved codes
 *     {x, a, a, b} where a, b lie in the same block of a 5-block partition of
 *     the other 33 tile types (6 pairs cannot hit 5 blocks once each).
 *   - kokushi hands: reserved codes made of 4 distinct orphans other than the wait.
 *
 * usage: build.exe classes_census.txt plan_out.txt [-threads N] [-seed S]
 */
#include "tenpai_enum.h"

/* ------------------------------------------------------------------ classes */
static int NCL = 0;
static uint64_t CL_mask[4096];
#define CH_SIZE 16384
static uint64_t CH_key[CH_SIZE];
static int CH_val[CH_SIZE];
static inline uint32_t hmix(uint64_t x) {
    x ^= x >> 33; x *= 0xff51afd7ed558ccdull; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ull; x ^= x >> 33;
    return (uint32_t)x;
}
static int class_id(uint64_t W) {
    uint32_t h = hmix(W) & (CH_SIZE - 1);
    while (CH_key[h]) { if (CH_key[h] == W) return CH_val[h]; h = (h + 1) & (CH_SIZE - 1); }
    return -1;
}
static void class_add(uint64_t W) {
    uint32_t h = hmix(W) & (CH_SIZE - 1);
    while (CH_key[h]) { if (CH_key[h] == W) return; h = (h + 1) & (CH_SIZE - 1); }
    CH_key[h] = W; CH_val[h] = NCL; CL_mask[NCL++] = W;
}

/* ------------------------------------------------------------------ growable u64 hash set */
typedef struct { uint64_t *k; int64_t cap, n; } HSet;
static void hs_init(HSet *s, int64_t cap) { s->cap = cap; s->n = 0; s->k = calloc(cap, 8); }
static void hs_add(HSet *s, uint64_t key);
static void hs_grow(HSet *s) {
    HSet t; hs_init(&t, s->cap * 2);
    for (int64_t i = 0; i < s->cap; i++) if (s->k[i]) hs_add(&t, s->k[i]);
    free(s->k); *s = t;
}
static void hs_add(HSet *s, uint64_t key) {
    if (s->n * 2 >= s->cap) hs_grow(s);
    uint64_t h = hmix(key) & (s->cap - 1);
    while (s->k[h]) { if (s->k[h] == key) return; h = (h + 1) & (s->cap - 1); }
    s->k[h] = key; s->n++;
}

/* unit key = cls(12) <<46 | catmask(4) <<42 | idxLo(21) <<21 | idxHi(21) */
typedef struct { HSet units; int64_t n_tanki, n_chi_only, n_kok, n_unit_hands, n_odd; } BCtx;

static void on_hand(void *vctx, uint8_t *c, uint64_t W) {
    BCtx *x = (BCtx *)vctx;
    int cls = class_id(W);
    if (cls < 0) { x->n_odd++; return; }
    if (waits_kokushi(c)) { x->n_kok++; return; }
    uint64_t ws = waits_std(c);
    if (!ws) { x->n_chi_only++; return; }
    int n[4] = {0, 0, 0, 0};
    for (int t = 0; t < NT; t++) n[CAT[t]] += c[t];
    int cm = 0, asz = 0;
    for (int k = 0; k < 4; k++) if (n[k] % 3) { cm |= 1 << k; asz += n[k]; }
    if (asz == 1) { x->n_tanki++; return; }
    int I[4];
    cat_index(c, I);
    uint64_t lo = 0, hi = 0;
    int first = 1;
    for (int k = 0; k < 4; k++)
        if ((cm >> k) & 1) { if (first) { lo = (uint64_t)I[k]; first = 0; } else hi = (uint64_t)I[k]; }
    uint64_t key = ((uint64_t)cls << 46) | ((uint64_t)cm << 42) | (lo << 21) | hi;
    hs_add(&x->units, key);
    x->n_unit_hands++;
}

static int cmp_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return x < y ? -1 : x > y;
}

/* ------------------------------------------------------------------ code multisets */
#define NMU (34 * 34 * 34 * 34)
static uint8_t MU_used[NMU];      /* orderings already handed out */
static uint8_t MU_perm[NMU];      /* number of distinct orderings p(mu) */
static int *MU_demand;            /* classes having some unit containing mu (computed later) */
static inline int mu_key(const int *t) { return ((t[0] * 34 + t[1]) * 34 + t[2]) * 34 + t[3]; }
static inline void mu_tiles(int key, int *t) {
    t[3] = key % 34; key /= 34; t[2] = key % 34; key /= 34; t[1] = key % 34; t[0] = key / 34;
}
static int perm_count(const int *t) {
    int m[4] = {1, 1, 1, 1}, f[5] = {1, 1, 2, 6, 24}, r = 24;
    /* t sorted: count runs */
    int i = 0;
    while (i < 4) { int j = i; while (j < 4 && t[j] == t[i]) j++; r /= f[j - i]; i = j; }
    (void)m;
    return r;
}

/* per class owned codes */
typedef struct { int *mu; int *ord; int n, cap; } Owned;
static Owned *OWN;
static void own_add(int cls, int mu) {
    Owned *o = &OWN[cls];
    if (o->n == o->cap) {
        o->cap = o->cap ? o->cap * 2 : 16;
        o->mu = realloc(o->mu, sizeof(int) * o->cap);
        o->ord = realloc(o->ord, sizeof(int) * o->cap);
    }
    o->mu[o->n] = mu; o->ord[o->n] = MU_used[mu]; o->n++;
    MU_used[mu]++;
}
static int owns(int cls, int mu) {
    Owned *o = &OWN[cls];
    for (int i = 0; i < o->n; i++) if (o->mu[i] == mu) return 1;
    return 0;
}
/* give class cls a fresh ordering of multiset {a,b,c,d}; returns 1 on success */
static int take(int cls, int a, int b, int c, int d) {
    int t[4] = {a, b, c, d};
    for (int i = 1; i < 4; i++) for (int j = i; j > 0 && t[j] < t[j - 1]; j--) { int z = t[j]; t[j] = t[j - 1]; t[j - 1] = z; }
    int mu = mu_key(t);
    if (owns(cls, mu)) return 1;
    if (MU_used[mu] >= MU_perm[mu]) return 0;
    own_add(cls, mu);
    return 1;
}

/* ------------------------------------------------------------------ units */
typedef struct { int cls, catmask, size; uint8_t a[NT]; } Unit;
static Unit *U;
static int64_t NU;
static uint8_t *COVERED;

static void decode_unit(uint64_t key, Unit *u) {
    u->cls = (int)(key >> 46);
    u->catmask = (int)((key >> 42) & 15);
    uint64_t lo = (key >> 21) & ((1u << 21) - 1), hi = key & ((1u << 21) - 1);
    memset(u->a, 0, NT);
    int first = 1;
    u->size = 0;
    for (int k = 0; k < 4; k++) {
        if (!((u->catmask >> k) & 1)) continue;
        uint64_t idx = first ? lo : hi;
        first = 0;
        int n = k < 3 ? 9 : 7;
        for (int i = 0; i < n; i++) { u->a[9 * k + i] = (uint8_t)(idx % 5); u->size += (int)(idx % 5); idx /= 5; }
    }
}

/* enumerate 4-sub-multisets of a unit; cross_only = only those touching both active categories (if two) */
static int g_nt, g_tiles[NT], g_cnt[NT], g_pick[4], *g_out, g_n, g_cross, g_catmask;
static void subs_rec(int i, int left, int q) {
    if (left == 0) {
        if (g_cross && __builtin_popcount(g_catmask) == 2) {
            int cats = 0;
            for (int r = 0; r < 4; r++) cats |= 1 << CAT[g_pick[r]];
            if (cats != g_catmask) return;
        }
        g_out[g_n++] = mu_key(g_pick);
        return;
    }
    if (i == g_nt) return;
    int mx = g_cnt[i] < left ? g_cnt[i] : left;
    for (int k = mx; k >= 0; k--) {
        for (int r = 0; r < k; r++) g_pick[q + r] = g_tiles[i];
        subs_rec(i + 1, left - k, q + k);
    }
}
static int subs4(const Unit *u, int *out, int cross_only) {
    g_nt = 0;
    for (int t = 0; t < NT; t++) if (u->a[t]) { g_tiles[g_nt] = t; g_cnt[g_nt] = u->a[t]; g_nt++; }
    g_out = out; g_n = 0; g_cross = cross_only; g_catmask = u->catmask;
    subs_rec(0, 4, 0);
    return g_n;
}

/* ------------------------------------------------------------------ main */
static int *CNT;      /* per mu: count of uncovered units of current class containing it */
static int *TOUCH; static int nTOUCH;

int main(int argc, char **argv) {
    if (argc < 3) { printf("usage: build classes.txt plan_out.txt [-threads N]\n"); return 1; }
    int nthreads = 14;
    for (int i = 3; i < argc; i++)
        if (!strcmp(argv[i], "-threads") && i + 1 < argc) {
            nthreads = parse_threads(argv[++i]);
            if (!nthreads) { printf("invalid -threads value '%s' (expected 1..%d)\n", argv[i], ENUM_MAX_THREADS); return 2; }
        }
    uint64_t t0 = GetTickCount64();
    mj_init();
    /* classes */
    {
        FILE *f = fopen(argv[1], "rb");
        if (!f) { printf("cannot open %s\n", argv[1]); return 1; }
        char line[1024];
        while (fgets(line, sizeof line, f)) { char *e; uint64_t W = strtoull(line, &e, 16); if (W) class_add(W); }
        fclose(f);
    }
    printf("classes loaded: %d\n", NCL);
    /* collect units */
    enum_prepare();
    EnumThread *ets = calloc(nthreads, sizeof(EnumThread));
    BCtx *bc = calloc(nthreads, sizeof(BCtx));
    if (!ets || !bc) { printf("out of memory\n"); return 1; }
    for (int i = 0; i < nthreads; i++) { hs_init(&bc[i].units, 1 << 20); ets[i].ctx = &bc[i]; ets[i].fn = on_hand; }
    if (!enum_run(ets, nthreads)) { printf("enumeration failed; no plan written\n"); return 1; }
    int64_t tot = 0, tank = 0, chio = 0, kok = 0, uh = 0, odd = 0;
    for (int i = 0; i < nthreads; i++) {
        tot += bc[i].units.n; tank += bc[i].n_tanki; chio += bc[i].n_chi_only; kok += bc[i].n_kok;
        uh += bc[i].n_unit_hands; odd += bc[i].n_odd;
    }
    uint64_t *all = malloc(8 * (tot + 1));
    int64_t na = 0;
    for (int i = 0; i < nthreads; i++) {
        for (int64_t j = 0; j < bc[i].units.cap; j++) if (bc[i].units.k[j]) all[na++] = bc[i].units.k[j];
        free(bc[i].units.k);
    }
    qsort(all, na, 8, cmp_u64);
    int64_t nu = 0;
    for (int64_t i = 0; i < na; i++) if (!nu || all[i] != all[nu - 1]) all[nu++] = all[i];
    NU = nu;
    printf("hands: core-unit hands=%lld tanki=%lld seven-pairs-only=%lld kokushi=%lld (unknown class %lld)\n",
           (long long)uh, (long long)tank, (long long)chio, (long long)kok, (long long)odd);
    U = malloc(sizeof(Unit) * NU);
    COVERED = calloc(NU, 1);
    int64_t bysz[16] = {0}, type2 = 0;
    for (int64_t i = 0; i < NU; i++) {
        decode_unit(all[i], &U[i]);
        bysz[U[i].size]++;
        if (__builtin_popcount(U[i].catmask) == 2) type2++;
    }
    free(all);
    printf("distinct (class, core) units: %lld (two-category: %lld); by |A|:", (long long)NU, (long long)type2);
    for (int s = 0; s < 16; s++) if (bysz[s]) printf(" %d:%lld", s, (long long)bysz[s]);
    printf("\n  [%.1f s]\n", (GetTickCount64() - t0) / 1000.0);

    /* class ranges (units sorted by class because class is the top key field) */
    int64_t *cl_lo = calloc(NCL + 1, 8), *cl_hi = calloc(NCL + 1, 8);
    for (int c = 0; c < NCL; c++) cl_lo[c] = cl_hi[c] = 0;
    for (int64_t i = 0; i < NU; i++) { int c = U[i].cls; if (cl_hi[c] == 0) cl_lo[c] = i; cl_hi[c] = i + 1; }

    /* multiset tables */
    for (int key = 0; key < NMU; key++) { int t[4]; mu_tiles(key, t); MU_perm[key] = (t[0] <= t[1] && t[1] <= t[2] && t[2] <= t[3]) ? (uint8_t)perm_count(t) : 0; }
    OWN = calloc(NCL, sizeof(Owned));
    CNT = calloc(NMU, sizeof(int));
    TOUCH = malloc(sizeof(int) * NMU);
    MU_demand = calloc(NMU, sizeof(int));
    int *subbuf = malloc(sizeof(int) * 4096);

    /* ---------- phase F: reserved families ---------- */
    int fam_fail = 0, fam_codes = 0;
    for (int x = 0; x < NT; x++) {
        int cls = class_id(1ull << x);
        if (cls < 0) { printf("no class {%s}?\n", TN[x]); return 1; }
        int cx = CAT[x];
        /* tanki: {x} + one meld of another category */
        for (int a = 0; a < NT; a++) {
            if (CAT[a] == cx) continue;
            if (!take(cls, x, a, a, a)) fam_fail++; else fam_codes++;
            if (a < 27 && a % 9 <= 6) { if (!take(cls, x, a, a + 1, a + 2)) fam_fail++; else fam_codes++; }
        }
        /* seven pairs: 5 blocks (7,7,7,6,6) of the other 33 types; block of tile = rank in a rotated list */
        int others[33], no = 0;
        for (int r = 1; r < NT; r++) others[no++] = (x + r * 11) % NT; /* 11 is coprime to 34: a permutation */
        int bsz[5] = {7, 7, 7, 6, 6}, start = 0;
        for (int b = 0; b < 5; b++) {
            for (int i = start; i < start + bsz[b]; i++)
                for (int j = i + 1; j < start + bsz[b]; j++) {
                    int a = others[i], c = others[j];
                    /* {x, a, a, c}: requires 2 copies of a (a pair) and one of c */
                    if (!take(cls, x, a, a, c)) fam_fail++; else fam_codes++;
                }
            start += bsz[b];
        }
    }
    /* kokushi: class {t} for orphan t gets 4 distinct orphans other than t; 13-wait class gets 4 orphans */
    for (int i = 0; i < 13; i++) {
        int cls = class_id(1ull << ORPHANS[i]);
        int q[4], nq = 0;
        for (int r = 1; nq < 4; r++) q[nq++] = ORPHANS[(i + r) % 13];
        if (!take(cls, q[0], q[1], q[2], q[3])) fam_fail++; else fam_codes++;
    }
    {
        int cls = class_id(ORPHAN_MASK);
        if (cls < 0) { printf("no 13-wait class?\n"); return 1; }
        if (!take(cls, 0, 8, 9, 17)) fam_fail++; else fam_codes++;
    }
    printf("phase F (reserved families): %d codes, %d failures\n", fam_codes, fam_fail);

    /* ---------- demand per multiset (number of classes with a unit containing it) ---------- */
    {
        uint8_t *seen = calloc(NMU, 1);
        int *list = malloc(sizeof(int) * NMU);
        for (int c = 0; c < NCL; c++) {
            int nl = 0;
            for (int64_t i = cl_lo[c]; i < cl_hi[c]; i++) {
                int ns = subs4(&U[i], subbuf, 0);
                for (int s = 0; s < ns; s++) if (!seen[subbuf[s]]) { seen[subbuf[s]] = 1; list[nl++] = subbuf[s]; }
            }
            for (int s = 0; s < nl; s++) { MU_demand[list[s]]++; seen[list[s]] = 0; }
        }
        free(seen); free(list);
        int64_t over = 0, used_mu = 0;
        for (int k = 0; k < NMU; k++) if (MU_demand[k]) { used_mu++; if (MU_demand[k] > MU_perm[k]) over++; }
        printf("multisets touched by some unit: %lld ; with demand > orderings: %lld  [%.1f s]\n",
               (long long)used_mu, (long long)over, (GetTickCount64() - t0) / 1000.0);
    }

    /* ---------- phase T: units with |A| == 4 (single candidate) ---------- */
    int tfail = 0, tcodes = 0;
    for (int64_t i = 0; i < NU; i++) {
        if (U[i].size != 4) continue;
        int ns = subs4(&U[i], subbuf, 0);
        if (ns != 1) { printf("internal: |A|=4 unit with %d subs\n", ns); return 1; }
        int t[4]; mu_tiles(subbuf[0], t);
        if (owns(U[i].cls, subbuf[0])) continue;
        if (take(U[i].cls, t[0], t[1], t[2], t[3])) tcodes++; else tfail++;
    }
    printf("phase T (|A|=4 units): %d new codes, %d units with all orderings already taken\n", tcodes, tfail);

    /* ---------- phase G: per-class greedy set cover over remaining units ---------- */
    int64_t gfail = 0;
    int gcodes = 0;
    int *order = malloc(sizeof(int) * NCL);
    for (int c = 0; c < NCL; c++) order[c] = c;
    /* classes with fewer units first */
    for (int i = 1; i < NCL; i++)
        for (int j = i; j > 0 && (cl_hi[order[j]] - cl_lo[order[j]]) < (cl_hi[order[j - 1]] - cl_lo[order[j - 1]]); j--) {
            int z = order[j]; order[j] = order[j - 1]; order[j - 1] = z;
        }
    int64_t *ulist = malloc(sizeof(int64_t) * (NU + 1));
    for (int oi = 0; oi < NCL; oi++) {
        int c = order[oi];
        int nul = 0;
        /* uncovered units of this class */
        for (int64_t i = cl_lo[c]; i < cl_hi[c]; i++) {
            if (U[i].cls != c) continue;
            int cov = 0;
            Owned *o = &OWN[c];
            for (int q = 0; q < o->n && !cov; q++) {
                int t[4]; mu_tiles(o->mu[q], t);
                int need[NT];
                (void)need;
                int ok = 1;
                for (int r = 0; r < 4 && ok; r++) {
                    int m = 0;
                    for (int r2 = 0; r2 < 4; r2++) if (t[r2] == t[r]) m++;
                    if (U[i].a[t[r]] < m) ok = 0;
                }
                cov = ok;
            }
            if (cov) COVERED[i] = 1; else ulist[nul++] = i;
        }
        if (!nul) continue;
        /* count candidates; two-category units prefer cross-category codes */
        nTOUCH = 0;
        for (int u = 0; u < nul; u++) {
            Unit *un = &U[ulist[u]];
            int ns = subs4(un, subbuf, 1);
            if (ns == 0) ns = subs4(un, subbuf, 0);
            for (int s = 0; s < ns; s++) { if (!CNT[subbuf[s]]) TOUCH[nTOUCH++] = subbuf[s]; CNT[subbuf[s]]++; }
        }
        int remaining = nul;
        while (remaining > 0) {
            /* best multiset: max count among those with a free ordering; prefer low contention */
            int best = -1;
            double bestscore = -1;
            for (int q = 0; q < nTOUCH; q++) {
                int mu = TOUCH[q];
                if (CNT[mu] <= 0 || MU_used[mu] >= MU_perm[mu]) continue;
                int freeo = MU_perm[mu] - MU_used[mu];
                double contention = (double)MU_demand[mu] / (double)freeo;
                double score = CNT[mu] * 4.0 / (contention < 1 ? 1 : contention) + CNT[mu];
                if (score > bestscore) { bestscore = score; best = mu; }
            }
            if (best < 0) break;
            int t[4]; mu_tiles(best, t);
            take(c, t[0], t[1], t[2], t[3]);
            gcodes++;
            /* mark covered units */
            for (int u = 0; u < nul; u++) {
                int64_t ui = ulist[u];
                if (COVERED[ui]) continue;
                int ok = 1;
                for (int r = 0; r < 4 && ok; r++) {
                    int m = 0;
                    for (int r2 = 0; r2 < 4; r2++) if (t[r2] == t[r]) m++;
                    if (U[ui].a[t[r]] < m) ok = 0;
                }
                if (!ok) continue;
                COVERED[ui] = 1; remaining--;
                int ns = subs4(&U[ui], subbuf, 1);
                if (ns == 0) ns = subs4(&U[ui], subbuf, 0);
                for (int s = 0; s < ns; s++) CNT[subbuf[s]]--;
            }
        }
        /* any unit still uncovered: try any free sub-multiset (cross rule relaxed) */
        for (int u = 0; u < nul; u++) {
            int64_t ui = ulist[u];
            if (COVERED[ui]) continue;
            int ns = subs4(&U[ui], subbuf, 0), done = 0;
            for (int s = 0; s < ns && !done; s++) {
                int mu = subbuf[s];
                if (MU_used[mu] < MU_perm[mu]) { int t[4]; mu_tiles(mu, t); take(c, t[0], t[1], t[2], t[3]); gcodes++; done = 1; }
            }
            if (done) COVERED[ui] = 1; else gfail++;
        }
        for (int q = 0; q < nTOUCH; q++) CNT[TOUCH[q]] = 0;
    }
    printf("phase G (greedy): %d new codes, %lld units left without any free code  [%.1f s]\n",
           gcodes, (long long)gfail, (GetTickCount64() - t0) / 1000.0);

    /* ---------- write plan ---------- */
    FILE *f = fopen(argv[2], "wb");
    int64_t ncodes = 0;
    for (int c = 0; c < NCL; c++) {
        Owned *o = &OWN[c];
        fprintf(f, "%llx %d 4", (unsigned long long)CL_mask[c], o->n);
        for (int q = 0; q < o->n; q++) {
            int t[4]; mu_tiles(o->mu[q], t);
            /* the ord-th distinct permutation of t in lexicographic order */
            int perm[4] = {t[0], t[1], t[2], t[3]};
            for (int r = 0; r < o->ord[q]; r++) {
                /* next_permutation */
                int i = 2;
                while (i >= 0 && perm[i] >= perm[i + 1]) i--;
                if (i < 0) { printf("ordering overflow\n"); return 1; }
                int j = 3;
                while (perm[j] <= perm[i]) j--;
                int z = perm[i]; perm[i] = perm[j]; perm[j] = z;
                for (int a = i + 1, b = 3; a < b; a++, b--) { z = perm[a]; perm[a] = perm[b]; perm[b] = z; }
            }
            fprintf(f, " %d %d %d %d", perm[0], perm[1], perm[2], perm[3]);
            ncodes++;
        }
        fprintf(f, "\n");
    }
    fclose(f);
    int empty = 0;
    for (int c = 0; c < NCL; c++) if (!OWN[c].n) empty++;
    printf("plan written: %d classes, %lld ordered codes, %d classes without codes -> %s\n", NCL, (long long)ncodes, empty, argv[2]);
    printf("elapsed %.1f s\n", (GetTickCount64() - t0) / 1000.0);
    return 0;
}
