/*
 * census.c -- independent census of all tenpai hands + exhaustive check of a
 *             k-tile code plan against every single tenpai hand.
 *
 * usage: census.exe [plan.txt] [-threads N] [-classes out.txt] [-usage]
 *
 * plan.txt format (one class per line, produced by tools/plan_json_to_txt.py):
 *     <W as hex mask> <ncodes> <k> t1 t2 ... tk  t1 t2 ... tk ...
 */
#include "tenpai_enum.h"

/* ---------------- class hash map ---------------- */
#define CM_BITS 15
#define CM_SIZE (1 << CM_BITS)
typedef struct {
    uint64_t key[CM_SIZE];
    int64_t n[CM_SIZE], nstd[CM_SIZE], nchi[CM_SIZE], nkok[CM_SIZE], nboth[CM_SIZE];
    int64_t nsingle[CM_SIZE]; /* hands lying entirely in one category */
} ClassMap;

static inline uint32_t hmix(uint64_t x) {
    x ^= x >> 33; x *= 0xff51afd7ed558ccdull; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ull; x ^= x >> 33;
    return (uint32_t)x;
}
static int cm_slot(ClassMap *m, uint64_t k) {
    uint32_t h = hmix(k) & (CM_SIZE - 1);
    while (m->key[h] && m->key[h] != k) h = (h + 1) & (CM_SIZE - 1);
    if (!m->key[h]) m->key[h] = k;
    return (int)h;
}

/* ---------------- plan ---------------- */
typedef struct { uint8_t t[4]; uint8_t m[4]; int nreq; } Req; /* distinct tiles + multiplicities */
static int PK = 0;                  /* code length */
static int nPC = 0;                 /* classes in plan */
static uint64_t *PC_mask;
static int *PC_start, *PC_n;       /* codes of class i: [start, start+n) */
static int nCodes = 0;
static uint8_t *CODE;               /* nCodes * PK */
static Req *CREQ;
static int64_t *CODE_used;          /* per code: number of hands of its class containing it (-usage) */
static int64_t *CODE_first;         /* per code: number of hands where it is the first hit */
#define PM_SIZE (1 << 16)
static uint64_t PM_key[PM_SIZE];
static int PM_val[PM_SIZE];
static int plan_loaded = 0, want_usage = 0;

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
    if (!f) { printf("cannot open plan %s\n", path); return 0; }
    int cap = 1 << 20;
    char *line = malloc(cap);
    int ccap = 1 << 16, kcap = 1 << 22;
    PC_mask = malloc(sizeof(uint64_t) * ccap);
    PC_start = malloc(sizeof(int) * ccap);
    PC_n = malloc(sizeof(int) * ccap);
    CODE = malloc(kcap);
    while (fgets(line, cap, f)) {
        char *p = line, *e;
        if (*p == '#' || *p == '\n' || *p == '\r' || !*p) continue;
        uint64_t mask = strtoull(p, &e, 16); p = e;
        int n = (int)strtol(p, &e, 10); p = e;
        int k = (int)strtol(p, &e, 10); p = e;
        if (PK == 0) PK = k;
        if (k != PK) { printf("mixed code lengths\n"); return 0; }
        PC_mask[nPC] = mask; PC_start[nPC] = nCodes; PC_n[nPC] = n;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < k; j++) {
                int v = (int)strtol(p, &e, 10);
                if (e == p) { printf("parse error in class %d\n", nPC); return 0; }
                p = e;
                if ((nCodes + 1) * PK > kcap) { printf("too many codes\n"); return 0; }
                CODE[nCodes * PK + j] = (uint8_t)v;
                if (j == k - 1) nCodes++;
            }
        nPC++;
    }
    fclose(f);
    free(line);
    CREQ = malloc(sizeof(Req) * (nCodes + 1));
    CODE_used = calloc(nCodes + 1, sizeof(int64_t));
    CODE_first = calloc(nCodes + 1, sizeof(int64_t));
    for (int i = 0; i < nCodes; i++) {
        Req r; r.nreq = 0;
        for (int j = 0; j < PK; j++) {
            int t = CODE[i * PK + j], found = 0;
            for (int q = 0; q < r.nreq; q++) if (r.t[q] == t) { r.m[q]++; found = 1; }
            if (!found) { r.t[r.nreq] = (uint8_t)t; r.m[r.nreq] = 1; r.nreq++; }
        }
        CREQ[i] = r;
    }
    for (int i = 0; i < nPC; i++) {
        uint32_t h = hmix(PC_mask[i]) & (PM_SIZE - 1);
        while (PM_key[h]) {
            if (PM_key[h] == PC_mask[i]) { printf("duplicate class row in plan!\n"); return 0; }
            h = (h + 1) & (PM_SIZE - 1);
        }
        PM_key[h] = PC_mask[i]; PM_val[h] = i;
    }
    plan_loaded = 1;
    return 1;
}

static int cmp_u32(const void *a, const void *b) {
    uint32_t x = *(const uint32_t *)a, y = *(const uint32_t *)b;
    return x < y ? -1 : x > y;
}

/* structural checks: tile range, multiplicity <= 4, ordered codes pairwise distinct */
static void plan_structure_report(void) {
    int bad_range = 0, bad_mult = 0;
    uint32_t *keys = malloc(sizeof(uint32_t) * (nCodes + 1));
    int *owner = malloc(sizeof(int) * (nCodes + 1));
    for (int c = 0; c < nPC; c++)
        for (int i = PC_start[c]; i < PC_start[c] + PC_n[c]; i++) owner[i] = c;
    for (int i = 0; i < nCodes; i++) {
        uint32_t key = 0;
        for (int j = 0; j < PK; j++) {
            int t = CODE[i * PK + j];
            if (t < 0 || t >= NT) bad_range++;
            key = key * 64 + (uint32_t)t;
        }
        for (int q = 0; q < CREQ[i].nreq; q++) if (CREQ[i].m[q] > 4) bad_mult++;
        keys[i] = key;
    }
    qsort(keys, nCodes, sizeof(uint32_t), cmp_u32);
    int dup = 0;
    for (int i = 1; i < nCodes; i++) if (keys[i] == keys[i - 1]) dup++;
    int empty = 0;
    for (int c = 0; c < nPC; c++) if (PC_n[c] == 0) empty++;
    printf("[plan] classes=%d codes=%d k=%d  bad_tile_index=%d mult>4=%d duplicate_ordered_codes=%d empty_classes=%d\n",
           nPC, nCodes, PK, bad_range, bad_mult, dup, empty);
    free(keys); free(owner);
}

/* ---------------- per-thread context ---------------- */
#define MAXFAIL 40
typedef struct {
    ClassMap *cm;
    int64_t nstd, nchi, nkok, nboth, nsingle_cat[4];
    int64_t plan_missing_class, plan_uncovered;
    int nfail;
    uint8_t fail_hand[MAXFAIL][NT];
    uint64_t fail_W[MAXFAIL];
    int64_t *code_used, *code_first;
} Ctx;

static int want_naive = 0;
static volatile int64_t naive_mismatch = 0;

/* -critical: for each code, how many hands have it as their ONLY usable code, split by hand type */
static int want_critical = 0;
enum { HT_TYPE1, HT_TYPE2, HT_TANKI, HT_CHI_ONLY, HT_STD_CHI, HT_KOK, HT_N };
static const char *HT_NAME[HT_N] = {"std-1cat", "std-2cat", "tanki", "chiitoi-only", "std+chiitoi", "kokushi"};
static int64_t (*CRIT)[HT_N];        /* [code][type] */
static uint8_t (*CRIT_EX)[HT_N][NT];  /* example hand per code/type (racy but only informational) */
static int hand_type(const uint8_t *c, uint64_t ws, uint64_t wc, uint64_t wk) {
    if (wk) return HT_KOK;
    if (!ws) return HT_CHI_ONLY;
    if (wc) return HT_STD_CHI;
    int n[4] = {0, 0, 0, 0};
    for (int t = 0; t < NT; t++) n[CAT[t]] += c[t];
    int act = 0, asz = 0;
    for (int k = 0; k < 4; k++) if (n[k] % 3) { act++; asz += n[k]; }
    if (asz == 1) return HT_TANKI;
    return act == 2 ? HT_TYPE2 : HT_TYPE1;
}

static void on_hand(void *vctx, uint8_t *c, uint64_t W) {
    Ctx *x = (Ctx *)vctx;
    if (want_naive) {
        uint64_t Wn = naive_waits(c);
        if (Wn != W) {
            int64_t k = __atomic_fetch_add(&naive_mismatch, 1, __ATOMIC_RELAXED);
            if (k < 10) {
                char hb[128], a[512], b[512];
                hand_to_str(c, hb); mask_to_str(W, a); mask_to_str(Wn, b);
                printf("  NAIVE MISMATCH %s fast={%s} naive={%s}\n", hb, a, b);
            }
        }
    }
    uint64_t ws = waits_std(c), wc = waits_chiitoi(c), wk = waits_kokushi(c);
    int s = (int)(ws != 0), ch = (int)(wc != 0), k = (int)(wk != 0);
    x->nstd += s; x->nchi += ch; x->nkok += k; x->nboth += (s && ch);
    int cats = 0, onecat = -1;
    for (int t = 0; t < NT; t++) if (c[t]) { int ct = CAT[t]; if (!((cats >> ct) & 1)) { cats |= 1 << ct; onecat = ct; } }
    int single = (__builtin_popcount(cats) == 1);
    if (single) x->nsingle_cat[onecat]++;
    int sl = cm_slot(x->cm, W);
    x->cm->n[sl]++; x->cm->nstd[sl] += s; x->cm->nchi[sl] += ch; x->cm->nkok[sl] += k;
    x->cm->nboth[sl] += (s && ch); x->cm->nsingle[sl] += single;
    if (!plan_loaded) return;
    int pc = pm_find(W);
    int ok = 0;
    if (pc < 0) x->plan_missing_class++;
    else {
        int st = PC_start[pc], n = PC_n[pc];
        for (int i = st; i < st + n; i++) {
            const Req *r = &CREQ[i];
            int fits = 1;
            for (int q = 0; q < r->nreq; q++) if (c[r->t[q]] < r->m[q]) { fits = 0; break; }
            if (fits) {
                if (!ok) x->code_first[i]++;
                ok = 1;
                if (!want_usage) break;
                x->code_used[i]++;
            }
        }
        if (!ok) x->plan_uncovered++;
        if (want_critical && ok) {
            int nfit = 0, last = -1;
            for (int i = st; i < st + n && nfit < 2; i++) {
                const Req *r = &CREQ[i];
                int fits = 1;
                for (int q = 0; q < r->nreq; q++) if (c[r->t[q]] < r->m[q]) { fits = 0; break; }
                if (fits) { nfit++; last = i; }
            }
            if (nfit == 1) {
                int ht = hand_type(c, ws, wc, wk);
                int64_t prev = __atomic_fetch_add(&CRIT[last][ht], 1, __ATOMIC_RELAXED);
                if (prev == 0) memcpy(CRIT_EX[last][ht], c, NT);
            }
        }
    }
    if (!ok && x->nfail < MAXFAIL) {
        memcpy(x->fail_hand[x->nfail], c, NT);
        x->fail_W[x->nfail] = W;
        x->nfail++;
    }
}

int main(int argc, char **argv) {
    int nthreads = 14;
    const char *plan = 0, *classes_out = 0, *critical_out = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-threads") && i + 1 < argc) nthreads = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-classes") && i + 1 < argc) classes_out = argv[++i];
        else if (!strcmp(argv[i], "-usage")) want_usage = 1;
        else if (!strcmp(argv[i], "-naive")) want_naive = 1;
        else if (!strcmp(argv[i], "-critical") && i + 1 < argc) { want_critical = 1; critical_out = argv[++i]; }
        else plan = argv[i];
    }
    uint64_t t0 = GetTickCount64();
    mj_init();
    enum_prepare();
    printf("number-suit options (M or P, <=14 tiles): %d ; honor options: %d ; work items: %lld\n",
           nOPT_N, nOPT_Z, (long long)g_items_total);
    if (plan) {
        if (!load_plan(plan)) return 1;
        plan_structure_report();
        if (want_critical) {
            CRIT = calloc(nCodes + 1, sizeof(*CRIT));
            CRIT_EX = calloc(nCodes + 1, sizeof(*CRIT_EX));
        }
    }
    EnumThread *ets = calloc(nthreads, sizeof(EnumThread));
    Ctx *ctx = calloc(nthreads, sizeof(Ctx));
    for (int i = 0; i < nthreads; i++) {
        ctx[i].cm = calloc(1, sizeof(ClassMap));
        if (plan_loaded) {
            ctx[i].code_used = calloc(nCodes + 1, sizeof(int64_t));
            ctx[i].code_first = calloc(nCodes + 1, sizeof(int64_t));
        }
        ets[i].ctx = &ctx[i];
        ets[i].fn = on_hand;
    }
    enum_run(ets, nthreads);

    int64_t nG_std = 0, nG_chi = 0, nG_chi_std = 0, nG_kok = 0, nH = 0, bad = 0;
    int64_t nstd = 0, nchi = 0, nkok = 0, nboth = 0, nsc[4] = {0, 0, 0, 0}, pmiss = 0, punc = 0;
    ClassMap *g = calloc(1, sizeof(ClassMap));
    for (int i = 0; i < nthreads; i++) {
        nG_std += ets[i].nG_std; nG_chi += ets[i].nG_chi_total; nG_chi_std += ets[i].nG_chi_also_std;
        nG_kok += ets[i].nG_kok; nH += ets[i].nH; bad += ets[i].bad;
        nstd += ctx[i].nstd; nchi += ctx[i].nchi; nkok += ctx[i].nkok; nboth += ctx[i].nboth;
        for (int k = 0; k < 4; k++) nsc[k] += ctx[i].nsingle_cat[k];
        pmiss += ctx[i].plan_missing_class; punc += ctx[i].plan_uncovered;
        for (int s = 0; s < CM_SIZE; s++) {
            if (!ctx[i].cm->key[s]) continue;
            int sl = cm_slot(g, ctx[i].cm->key[s]);
            g->n[sl] += ctx[i].cm->n[s]; g->nstd[sl] += ctx[i].cm->nstd[s]; g->nchi[sl] += ctx[i].cm->nchi[s];
            g->nkok[sl] += ctx[i].cm->nkok[s]; g->nboth[sl] += ctx[i].cm->nboth[s]; g->nsingle[sl] += ctx[i].cm->nsingle[s];
        }
        if (plan_loaded)
            for (int q = 0; q < nCodes; q++) { CODE_used[q] += ctx[i].code_used[q]; CODE_first[q] += ctx[i].code_first[q]; }
    }
    printf("winning 14-tile vectors: standard=%lld  seven-pairs(all)=%lld (of which also standard=%lld)  kokushi=%lld\n",
           (long long)nG_std, (long long)nG_chi, (long long)nG_chi_std, (long long)nG_kok);
    printf("sanity (G-t not tenpai on t, must be 0): %lld\n", (long long)bad);
    if (want_naive)
        printf("naive recursive W recomputed for every hand: mismatches with table-driven W = %lld\n",
               (long long)naive_mismatch);
    printf("TENPAI HANDS (distinct 13-tile multisets): %lld\n", (long long)nH);
    printf("  standard-form tenpai: %lld\n  seven-pairs tenpai: %lld\n  both standard & seven-pairs: %lld\n  kokushi tenpai: %lld\n",
           (long long)nstd, (long long)nchi, (long long)nboth, (long long)nkok);
    printf("  single-category hands: m=%lld p=%lld s=%lld z=%lld\n", (long long)nsc[0], (long long)nsc[1], (long long)nsc[2], (long long)nsc[3]);
    int ncls = 0, hist[NT + 1], ncls_single = 0;
    int64_t hh[NT + 1];
    for (int i = 0; i <= NT; i++) { hist[i] = 0; hh[i] = 0; }
    for (int s = 0; s < CM_SIZE; s++)
        if (g->key[s]) {
            ncls++;
            int w = popc64(g->key[s]);
            hist[w]++; hh[w] += g->n[s];
            if (g->nsingle[s]) ncls_single++;
        }
    printf("DISTINCT WAIT SETS (classes): %d   (classes containing a single-category hand: %d)\n", ncls, ncls_single);
    printf("  |W| distribution (classes / hands):");
    for (int i = 1; i <= NT; i++) if (hist[i]) printf("  %d:%d/%lld", i, hist[i], (long long)hh[i]);
    printf("\n");
    if (classes_out) {
        FILE *f = fopen(classes_out, "wb");
        char buf[512];
        for (int s = 0; s < CM_SIZE; s++)
            if (g->key[s]) {
                mask_to_str(g->key[s], buf);
                fprintf(f, "%016llx %d %lld %lld %lld %lld %lld %s\n", (unsigned long long)g->key[s], popc64(g->key[s]),
                        (long long)g->n[s], (long long)g->nstd[s], (long long)g->nchi[s], (long long)g->nkok[s],
                        (long long)g->nsingle[s], buf);
            }
        fclose(f);
        printf("class list written to %s\n", classes_out);
    }
    if (plan_loaded) {
        int classes_not_in_plan = 0, plan_classes_unused = 0;
        for (int s = 0; s < CM_SIZE; s++) if (g->key[s] && pm_find(g->key[s]) < 0) classes_not_in_plan++;
        for (int i = 0; i < nPC; i++) {
            uint32_t h = hmix(PC_mask[i]) & (CM_SIZE - 1);
            int found = 0;
            while (g->key[h]) { if (g->key[h] == PC_mask[i]) { found = 1; break; } h = (h + 1) & (CM_SIZE - 1); }
            if (!found) plan_classes_unused++;
        }
        int64_t never_first = 0, never_fit = 0;
        for (int q = 0; q < nCodes; q++) { if (!CODE_first[q]) never_first++; if (want_usage && !CODE_used[q]) never_fit++; }
        printf("[plan check] true classes missing from plan: %d ; plan rows that are not a real class: %d\n",
               classes_not_in_plan, plan_classes_unused);
        printf("[plan check] hands whose class is missing: %lld ; hands with NO usable code of their class: %lld (out of %lld)\n",
               (long long)pmiss, (long long)punc, (long long)nH);
        printf("[plan check] codes never used as first hit: %lld", (long long)never_first);
        if (want_usage) printf(" ; codes contained in no hand of their class: %lld", (long long)never_fit);
        printf("\n");
        int shown = 0;
        for (int i = 0; i < nthreads && shown < 20; i++)
            for (int j = 0; j < ctx[i].nfail && shown < 20; j++, shown++) {
                char hb[128], wb[512];
                hand_to_str(ctx[i].fail_hand[j], hb);
                mask_to_str(ctx[i].fail_W[j], wb);
                printf("   FAIL hand %s  W={%s}\n", hb, wb);
            }
        printf("[plan check] VERDICT: %s\n",
               (pmiss == 0 && punc == 0) ? "every tenpai hand has a code of its own class (coverage OK)" : "PLAN FAILS");
        if (want_critical && critical_out) {
            FILE *f = fopen(critical_out, "wb");
            int64_t tot[HT_N] = {0}, ncrit[HT_N] = {0};
            int *owner = malloc(sizeof(int) * (nCodes + 1));
            for (int cc = 0; cc < nPC; cc++) for (int i = PC_start[cc]; i < PC_start[cc] + PC_n[cc]; i++) owner[i] = cc;
            fprintf(f, "# code_index class_mask t1 t2 t3 t4 | counts per type (%s %s %s %s %s %s) | example hand per type\n",
                    HT_NAME[0], HT_NAME[1], HT_NAME[2], HT_NAME[3], HT_NAME[4], HT_NAME[5]);
            for (int q = 0; q < nCodes; q++) {
                int any = 0;
                for (int t = 0; t < HT_N; t++) if (CRIT[q][t]) { any = 1; tot[t] += CRIT[q][t]; ncrit[t]++; }
                if (!any) continue;
                fprintf(f, "%d %llx", q, (unsigned long long)PC_mask[owner[q]]);
                for (int j = 0; j < PK; j++) fprintf(f, " %d", CODE[q * PK + j]);
                fprintf(f, " |");
                for (int t = 0; t < HT_N; t++) fprintf(f, " %lld", (long long)CRIT[q][t]);
                fprintf(f, " |");
                for (int t = 0; t < HT_N; t++) {
                    char hb[128];
                    if (CRIT[q][t]) { hand_to_str(CRIT_EX[q][t], hb); fprintf(f, " %s", hb); } else fprintf(f, " -");
                }
                fprintf(f, "\n");
            }
            fclose(f);
            printf("[critical] codes that are the ONLY usable code for some hand, by hand type:\n");
            for (int t = 0; t < HT_N; t++)
                printf("   %-13s critical codes=%lld, hands depending on a single code=%lld\n", HT_NAME[t], (long long)ncrit[t], (long long)tot[t]);
            printf("[critical] written to %s\n", critical_out);
        }
    }
    printf("elapsed %.1f s\n", (GetTickCount64() - t0) / 1000.0);
    return 0;
}
