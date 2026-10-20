/*
 * completeness.c -- check that the "G - t, canonical min wait" generator misses
 * no tenpai hand: on several mixed sub-universes U, compare
 *   (a) hands produced by the generator whose tiles all lie in U, with
 *   (b) brute force: every 13-tile hand over U, wait set by the NAIVE recursive
 *       checker (no per-suit tables).
 * Compared: number of tenpai hands, order-independent hash sums of the hands,
 * hash sums of (hand, W) pairs, and the number of distinct wait sets.
 */
#include "tenpai_enum.h"

#define NU_T 8
static const char *UNAME[NU_T] = {
    "1-9m+1-3p", "1-5m+3-6p+ESW", "13 orphans", "4-9m+1-3s+7-9s+C",
    "234m567p789s+ESPC", "1-9p+NPFC", "11 tiles: 1-4m 6-9m 1p E S", "1-6m+4-9s+F"};
static uint64_t UMASK[NU_T];

static void set_universes(void) {
    const int L[NU_T][16] = {
        {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, -1},
        {0, 1, 2, 3, 4, 11, 12, 13, 14, 27, 28, 29, -1},
        {0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33, -1},
        {3, 4, 5, 6, 7, 8, 18, 19, 20, 24, 25, 26, 33, -1},
        {1, 2, 3, 13, 14, 15, 24, 25, 26, 27, 28, 31, 33, -1},
        {9, 10, 11, 12, 13, 14, 15, 16, 17, 30, 31, 32, 33, -1},
        {0, 1, 2, 3, 5, 6, 7, 8, 9, 27, 28, -1},
        {0, 1, 2, 3, 4, 5, 21, 22, 23, 24, 25, 26, 32, -1}};
    for (int u = 0; u < NU_T; u++) {
        UMASK[u] = 0;
        for (int i = 0; L[u][i] >= 0; i++) UMASK[u] |= 1ull << L[u][i];
    }
}

static inline uint64_t mix64(uint64_t z) {
    z += 0x9e3779b97f4a7c15ull;
    z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ull;
    z = (z ^ (z >> 27)) * 0x94d049bb133111ebull;
    return z ^ (z >> 31);
}
static inline uint64_t hand_hash(const uint8_t *c) {
    uint64_t a = 0, b = 0;
    for (int t = 0; t < 17; t++) a = a * 5 + c[t];
    for (int t = 17; t < NT; t++) b = b * 5 + c[t];
    return mix64(a ^ mix64(b));
}

typedef struct { int64_t n; uint64_t hsum, hxor, hwsum; uint64_t cls[4096]; int ncls; } Stat;
static void stat_add_class(Stat *s, uint64_t W) {
    for (int i = 0; i < s->ncls; i++) if (s->cls[i] == W) return;
    if (s->ncls < 4096) s->cls[s->ncls++] = W;
}
static void stat_add(Stat *s, const uint8_t *c, uint64_t W) {
    uint64_t h = hand_hash(c);
    s->n++; s->hsum += h; s->hxor ^= h; s->hwsum += mix64(h ^ W);
    stat_add_class(s, W);
}

/* ---- (a) generator side ---- */
typedef struct { Stat st[NU_T]; } GCtx;
static void on_hand(void *vctx, uint8_t *c, uint64_t W) {
    GCtx *g = (GCtx *)vctx;
    uint64_t sup = 0;
    for (int t = 0; t < NT; t++) if (c[t]) sup |= 1ull << t;
    for (int u = 0; u < NU_T; u++) if (!(sup & ~UMASK[u])) stat_add(&g->st[u], c, W);
}

/* ---- (b) brute force side ---- */
typedef struct { int u, first; Stat st; } BJob;
static int UT[NU_T][NT], UN[NU_T];
static BJob *JOBS; static int NJOBS; static volatile int64_t JNEXT;

static void bf_rec(BJob *j, uint8_t *c, int pos, int left) {
    int u = j->u;
    if (pos == UN[u]) {
        if (left) return;
        uint64_t W = naive_waits(c);
        if (W) stat_add(&j->st, c, W);
        return;
    }
    int mx = left < 4 ? left : 4;
    /* prune: remaining capacity */
    if (left > 4 * (UN[u] - pos)) return;
    for (int k = 0; k <= mx; k++) {
        c[UT[u][pos]] = (uint8_t)k;
        bf_rec(j, c, pos + 1, left - k);
    }
    c[UT[u][pos]] = 0;
}
static DWORD __stdcall bf_worker(void *arg) {
    (void)arg;
    for (;;) {
        int64_t k = __atomic_fetch_add(&JNEXT, 1, __ATOMIC_RELAXED);
        if (k >= NJOBS) break;
        BJob *j = &JOBS[k];
        uint8_t c[NT];
        memset(c, 0, NT);
        /* first two tiles fixed by job: first = a*5+b */
        int a = j->first / 5, b = j->first % 5;
        c[UT[j->u][0]] = (uint8_t)a; c[UT[j->u][1]] = (uint8_t)b;
        if (a + b <= 13) bf_rec(j, c, 2, 13 - a - b);
    }
    return 0;
}

int main(void) {
    uint64_t t0 = GetTickCount64();
    mj_init();
    set_universes();
    for (int u = 0; u < NU_T; u++) {
        UN[u] = 0;
        for (int t = 0; t < NT; t++) if ((UMASK[u] >> t) & 1) UT[u][UN[u]++] = t;
    }
    int nth = 15;
    /* (a) */
    enum_prepare();
    EnumThread *ets = calloc(nth, sizeof(EnumThread));
    GCtx *gc = calloc(nth, sizeof(GCtx));
    for (int i = 0; i < nth; i++) { ets[i].ctx = &gc[i]; ets[i].fn = on_hand; }
    enum_run(ets, nth);
    Stat *A = calloc(NU_T, sizeof(Stat));
    for (int u = 0; u < NU_T; u++)
        for (int i = 0; i < nth; i++) {
            Stat *s = &gc[i].st[u];
            A[u].n += s->n; A[u].hsum += s->hsum; A[u].hxor ^= s->hxor; A[u].hwsum += s->hwsum;
            for (int q = 0; q < s->ncls; q++) stat_add_class(&A[u], s->cls[q]);
        }
    printf("(a) generator pass done [%.1f s]\n", (GetTickCount64() - t0) / 1000.0);
    /* (b) */
    NJOBS = NU_T * 25;
    JOBS = calloc(NJOBS, sizeof(BJob));
    for (int u = 0; u < NU_T; u++) for (int f = 0; f < 25; f++) { JOBS[u * 25 + f].u = u; JOBS[u * 25 + f].first = f; }
    JNEXT = 0;
    HANDLE h[64];
    for (int i = 0; i < nth; i++) h[i] = CreateThread(0, 0, bf_worker, 0, 0, 0);
    for (int i = 0; i < nth; i++) { WaitForSingleObject(h[i], INFINITE); CloseHandle(h[i]); }
    printf("(b) brute-force pass done [%.1f s]\n", (GetTickCount64() - t0) / 1000.0);
    int allok = 1;
    for (int u = 0; u < NU_T; u++) {
        Stat B; memset(&B, 0, sizeof B);
        for (int f = 0; f < 25; f++) {
            Stat *s = &JOBS[u * 25 + f].st;
            B.n += s->n; B.hsum += s->hsum; B.hxor ^= s->hxor; B.hwsum += s->hwsum;
            for (int q = 0; q < s->ncls; q++) stat_add_class(&B, s->cls[q]);
        }
        int ok = A[u].n == B.n && A[u].hsum == B.hsum && A[u].hxor == B.hxor && A[u].hwsum == B.hwsum && A[u].ncls == B.ncls;
        allok &= ok;
        printf("  U=%-26s |U|=%2d  tenpai: generator %9lld / brute force %9lld ; classes %4d / %4d ; hand+W hashes %s\n",
               UNAME[u], UN[u], (long long)A[u].n, (long long)B.n, A[u].ncls, B.ncls, ok ? "IDENTICAL" : "DIFFER");
    }
    printf("VERDICT: %s\n", allok ? "generator reproduces brute force exactly on every test universe" : "MISMATCH");
    printf("elapsed %.1f s\n", (GetTickCount64() - t0) / 1000.0);
    return 0;
}
