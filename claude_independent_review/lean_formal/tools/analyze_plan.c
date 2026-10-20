/*
 * analyze_plan.c -- structural analysis of a k=4 plan, to design the Lean proof.
 * Checks the plan against the active/inert decomposition of tenpai hands:
 *   T0 tanki: class {z} must contain z+meld for every meld outside cat(z)
 *   T1 single-category active part a (|a| in 4,7,10,13): some code of class WP(a) inside a
 *   T2 two-category active part (ax,ay): some code of class W0 inside ax+ay
 *   T3 seven-pairs-only hands: clique cover (<=5 groups) of the (z,x,x,y) graph
 *   T4 hands that are standard tenpai AND seven-pairs shaped: direct check
 *   K  kokushi hands: direct check
 * usage: analyze_plan.exe plan.txt
 */
#include "../../src/mjcore.h"

static int PK, nPC, nCodes;
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
    PC_mask = malloc(8 << 16); PC_start = malloc(4 << 16); PC_n = malloc(4 << 16); CODE = malloc(1 << 22);
    while (fgets(line, cap, f)) {
        char *p = line, *e;
        if (*p == '#' || *p == '\n' || !*p) continue;
        uint64_t mask = strtoull(p, &e, 16); p = e;
        int n = (int)strtol(p, &e, 10); p = e;
        int k = (int)strtol(p, &e, 10); p = e;
        PK = k;
        PC_mask[nPC] = mask; PC_start[nPC] = nCodes; PC_n[nPC] = n;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < k; j++) { CODE[nCodes * k + j] = (uint8_t)strtol(p, &e, 10); p = e; }
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

int main(int argc, char **argv) {
    mj_init();
    if (argc < 2 || !load_plan(argv[1])) { printf("cannot load plan\n"); return 1; }
    printf("plan: %d classes, %d codes, k=%d\n", nPC, nCodes, PK);
    USE = calloc(nCodes, sizeof(int64_t));
    uint8_t h[NT];
    /* ---- T0 tanki ---- */
    int t0miss = 0, t0tot = 0;
    for (int z = 0; z < NT; z++) {
        int ci = pm_find(1ull << z);
        if (ci < 0) { printf("T0: class {%s} missing\n", TN[z]); t0miss++; continue; }
        for (int m = 0; m < NT; m++) {
            if (CAT[m] == CAT[z]) continue;
            for (int kind = 0; kind < 2; kind++) {
                memset(h, 0, NT);
                if (kind == 0) h[m] += 3;
                else { if (m >= 27 || POS[m] > 6) continue; h[m]++; h[m + 1]++; h[m + 2]++; }
                h[z]++;
                t0tot++;
                int ok = 0;
                for (int i = 0; i < PC_n[ci] && !ok; i++) {
                    uint8_t need[NT]; memset(need, 0, NT);
                    for (int j = 0; j < PK; j++) need[CODE[(PC_start[ci] + i) * PK + j]]++;
                    if (!memcmp(need, h, NT)) ok = 1;
                }
                if (!ok) { t0miss++; if (t0miss < 10) printf("T0 miss: z=%s meld kind %d at %s\n", TN[z], kind, TN[m]); }
            }
        }
    }
    printf("T0 tanki: %d z+meld requirements, %d missing\n", t0tot, t0miss);
    /* ---- T1 single-category units ---- */
    int64_t t1u = 0, t1f = 0, t1miss = 0;
    for (int k = 0; k < 4; k++)
        for (int idx = 0; idx < NV(k); idx++) {
            int s = vsize(k, idx);
            if (s % 3 != 1 || s > 13 || s == 1) continue;
            uint64_t W = WPm(k, idx);
            if (!W) continue;
            t1u++;
            memset(h, 0, NT); vec_of(k, idx, h + OFF[k]);
            int r = find_code(W, h);
            if (r == -2) { t1miss++; continue; }
            if (r < 0) {
                t1f++;
                { int nm; int b = meld_rule_violations(h, W, 15 & ~(1 << k), &nm); exc_units++; if (b) exc_bad++; if (s != 4) exc_size_ne4++; }
                if (t1f < 10) { char b[300], w[300]; hand_to_str(h, b); mask_to_str(W, w); printf("T1 fail: a=%s W={%s}\n", b, w); }
            } else USE[r]++;
        }
    printf("T1 single-category units (|a|>=4): %lld, no code inside a: %lld, class missing: %lld\n",
           (long long)t1u, (long long)t1f, (long long)t1miss);
    /* ---- T2 two-category units ---- */
    int64_t t2u = 0, t2f = 0, t2miss = 0, onlyx = 0, onlyy = 0, both = 0;
    for (int k = 0; k < 4; k++) {
        nl[k] = 0;
        for (int idx = 0; idx < NV(k); idx++) {
            int s = vsize(k, idx);
            if (s % 3 != 2 || s > 11) continue;
            uint64_t wm = WMm(k, idx);
            int p = (st(k, idx) >> 1) & 1;
            if (!wm && !p) continue;
            lst[k][nl[k]] = idx; LWM[k][nl[k]] = wm; LP[k][nl[k]] = (uint8_t)p; LS[k][nl[k]] = (uint8_t)s; nl[k]++;
        }
        printf("cat %d: %d vectors with size=2 mod 3 and (P or WM)\n", k, nl[k]);
    }
    for (int x = 0; x < 4; x++)
        for (int y = x + 1; y < 4; y++)
            for (int i = 0; i < nl[x]; i++)
                for (int j = 0; j < nl[y]; j++) {
                    if (LS[x][i] + LS[y][j] > 13) continue;
                    uint64_t W = (LP[y][j] ? LWM[x][i] : 0) | (LP[x][i] ? LWM[y][j] : 0);
                    if (!W) continue;
                    t2u++;
                    memset(h, 0, NT); vec_of(x, lst[x][i], h + OFF[x]); vec_of(y, lst[y][j], h + OFF[y]);
                    int r = find_code(W, h);
                    if (r == -2) { t2miss++; continue; }
                    if (r < 0) {
                        t2f++;
                        { int nm; int b = meld_rule_violations(h, W, 15 & ~(1 << x) & ~(1 << y), &nm); exc_units++; if (b) exc_bad++; if (LS[x][i] + LS[y][j] != 4) exc_size_ne4++; }
                        if (t2f < 10) { char b[300], w[300]; hand_to_str(h, b); mask_to_str(W, w); printf("T2 fail: A=%s W={%s}\n", b, w); }
                        continue;
                    }
                    USE[r]++;
                    int inx = 1, iny = 1;
                    for (int q = 0; q < PK; q++) { int t = CODE[r * PK + q]; if (CAT[t] != x) inx = 0; if (CAT[t] != y) iny = 0; }
                    if (inx) onlyx++; else if (iny) onlyy++; else both++;
                }
    printf("T2 two-category units: %lld, no code inside A: %lld, class missing: %lld; first-hit code in x only %lld, y only %lld, mixed %lld\n",
           (long long)t2u, (long long)t2f, (long long)t2miss, (long long)onlyx, (long long)onlyy, (long long)both);
    /* ---- T3 seven-pairs-only: clique cover of (z,x,x,y) graph by consecutive windows ---- */
    int t3bad = 0;
    for (int z = 0; z < NT; z++) {
        int ci = pm_find(1ull << z);
        static uint8_t E[NT][NT];
        memset(E, 0, sizeof E);
        for (int i = 0; i < PC_n[ci]; i++) {
            uint8_t need[NT]; memset(need, 0, NT);
            for (int j = 0; j < PK; j++) need[CODE[(PC_start[ci] + i) * PK + j]]++;
            if (need[z] != 1) continue;
            int a = -1, b = -1, ok = 1;
            for (int t = 0; t < NT; t++) {
                if (t == z || !need[t]) continue;
                if (need[t] == 2 && a < 0) a = t;
                else if (need[t] == 1 && b < 0) b = t;
                else ok = 0;
            }
            if (ok && a >= 0 && b >= 0) E[a][b] = E[b][a] = 1;
        }
        int grp = 0, members[NT], nm = 0;
        char desc[400]; int L = 0;
        for (int t = 0; t < NT; t++) {
            if (t == z) continue;
            int fits = 1;
            for (int q = 0; q < nm; q++) if (!E[members[q]][t]) fits = 0;
            if (nm == 0 || !fits) { grp++; nm = 0; L += sprintf(desc + L, " |"); }
            members[nm++] = t;
            L += sprintf(desc + L, " %s", TN[t]);
        }
        if (grp > 5) { t3bad++; printf("T3: z=%s greedy windows need %d groups:%s\n", TN[z], grp, desc); }
        else if (z == 0 || z == 4 || z == 27) printf("T3: z=%s groups:%s\n", TN[z], desc);
    }
    printf("exception units: %lld, violating the single-meld rule: %lld, with |A| != 4: %lld\n", (long long)exc_units, (long long)exc_bad, (long long)exc_size_ne4);
    printf("T3 seven-pairs-only: %d of 34 singleton classes NOT coverable by <=5 consecutive cliques\n", t3bad);
    /* ---- T4 standard tenpai AND seven-pairs shaped ---- */
    int64_t t4 = 0, t4f = 0, t4mm = 0;
    for (int k = 0; k < 4; k++) {
        nap[k] = 0;
        for (int msk = 0; msk < (1 << LEN[k]); msk++) {
            int idx = 0;
            for (int i = 0; i < LEN[k]; i++) if (msk >> i & 1) idx += 2 * P5[i];
            if (st(k, idx) & 1) AP[k][nap[k]++] = idx;
        }
    }
    for (int x = 0; x < 4; x++) {
        int n3 = 1;
        for (int i = 0; i < LEN[x]; i++) n3 *= 3;
        for (int code3 = 0; code3 < n3; code3++) {
            int idx = 0, c3 = code3, ones = 0, s = 0;
            for (int i = 0; i < LEN[x]; i++) { int v = c3 % 3; c3 /= 3; idx += v * P5[i]; if (v == 1) ones++; s += v; }
            if (ones != 1 || s % 3 != 1 || s == 1) continue;
            uint64_t W = WPm(x, idx);
            if (!W) continue;
            int single = -1;
            { int q = idx; for (int i = 0; i < LEN[x]; i++) { if (q % 5 == 1) single = OFF[x] + i; q /= 5; } }
            int others[3], no = 0;
            for (int y = 0; y < 4; y++) if (y != x) others[no++] = y;
            for (int a = 0; a < nap[others[0]]; a++)
                for (int b = 0; b < nap[others[1]]; b++)
                    for (int c = 0; c < nap[others[2]]; c++) {
                        int sa = vsize(others[0], AP[others[0]][a]), sb = vsize(others[1], AP[others[1]][b]), sc = vsize(others[2], AP[others[2]][c]);
                        if (s + sa + sb + sc != 13) continue;
                        memset(h, 0, NT); vec_of(x, idx, h + OFF[x]);
                        vec_of(others[0], AP[others[0]][a], h + OFF[others[0]]);
                        vec_of(others[1], AP[others[1]][b], h + OFF[others[1]]);
                        vec_of(others[2], AP[others[2]][c], h + OFF[others[2]]);
                        uint64_t Wall = waits_all(h);
                        if (Wall != (W | 1ull << single)) t4mm++;
                        t4++;
                        if (find_code(Wall, h) < 0) t4f++;
                    }
        }
    }
    for (int x = 0; x < 4; x++)
        for (int y = x + 1; y < 4; y++) {
            int n3x = 1, n3y = 1;
            for (int i = 0; i < LEN[x]; i++) n3x *= 3;
            for (int i = 0; i < LEN[y]; i++) n3y *= 3;
            for (int cx = 0; cx < n3x; cx++) {
                int ix = 0, q = cx, ox = 0, sx = 0;
                for (int i = 0; i < LEN[x]; i++) { int v = q % 3; q /= 3; ix += v * P5[i]; if (v == 1) ox++; sx += v; }
                if (sx % 3 != 2 || ox > 1) continue;
                for (int cy = 0; cy < n3y; cy++) {
                    int iy = 0, q2 = cy, oy = 0, sy = 0;
                    for (int i = 0; i < LEN[y]; i++) { int v = q2 % 3; q2 /= 3; iy += v * P5[i]; if (v == 1) oy++; sy += v; }
                    if (sy % 3 != 2 || ox + oy != 1 || sx + sy > 13) continue;
                    uint64_t W0 = ((st(y, iy) & 2) ? WMm(x, ix) : 0) | ((st(x, ix) & 2) ? WMm(y, iy) : 0);
                    if (!W0) continue;
                    int others[2], no = 0;
                    for (int w = 0; w < 4; w++) if (w != x && w != y) others[no++] = w;
                    for (int a = 0; a < nap[others[0]]; a++)
                        for (int b = 0; b < nap[others[1]]; b++) {
                            int sa = vsize(others[0], AP[others[0]][a]), sb = vsize(others[1], AP[others[1]][b]);
                            if (sx + sy + sa + sb != 13) continue;
                            memset(h, 0, NT); vec_of(x, ix, h + OFF[x]); vec_of(y, iy, h + OFF[y]);
                            vec_of(others[0], AP[others[0]][a], h + OFF[others[0]]);
                            vec_of(others[1], AP[others[1]][b], h + OFF[others[1]]);
                            uint64_t Wall = waits_all(h);
                            t4++;
                            if (find_code(Wall, h) < 0) t4f++;
                        }
                }
            }
        }
    printf("T4 standard-tenpai & seven-pairs-shaped hands (|a|>1): %lld, uncovered %lld, type-I W mismatch %lld\n",
           (long long)t4, (long long)t4f, (long long)t4mm);
    /* ---- K kokushi ---- */
    int nk = 0, kf = 0;
    for (int miss = -1; miss < 13; miss++)
        for (int dbl = -1; dbl < 13; dbl++) {
            if ((miss < 0) != (dbl < 0) || (miss >= 0 && miss == dbl)) continue;
            memset(h, 0, NT);
            for (int i = 0; i < 13; i++) if (i != miss) h[ORPHANS[i]] = 1;
            if (dbl >= 0) h[ORPHANS[dbl]]++;
            nk++;
            if (find_code(waits_all(h), h) < 0) kf++;
        }
    printf("K kokushi hands: %d, uncovered %d\n", nk, kf);
    int unused = 0;
    for (int i = 0; i < nCodes; i++) if (!USE[i]) unused++;
    printf("codes never first-hit in T1/T2: %d\n", unused);
    return 0;
}
