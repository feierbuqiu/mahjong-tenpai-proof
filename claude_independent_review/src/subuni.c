/*
 * subuni.c -- sub-universe counting bound (independent search).
 *
 * If every hand H supported on a tile set U must send an ordered k-tuple of
 * its own tiles, all those tuples lie in U^k.  Hands with different wait sets
 * need different tuples, so  N(U) := #{ W(H) : H tenpai, supp(H) ⊆ U }  must
 * be <= |U|^k.  A class all of whose U-hands share no common k-sub-multiset
 * needs >= 2 tuples, giving the sharper  N(U) + L_k(U) <= |U|^k.
 *
 * Part 1: every subset U of one number suit (511 sets), under three rule
 *         variants:  S = the user's rules (strict seven pairs, no 5th tile),
 *                    F = 5th-tile waits allowed (formal shape only),
 *                    Q = four-of-a-kind may count as two pairs in seven pairs.
 * Part 2: every subset of (one number suit + 7 honors) (65,535 sets), rule S.
 */
#include "mjcore.h"

/* ---------- variant win checks (naive, counts may reach 5 in variant F) ---------- */
static int v_melds(uint8_t *c, int left) {
    if (left == 0) return 1;
    int i = 0;
    while (i < NT && c[i] == 0) i++;
    if (i == NT) return 0;
    if (c[i] >= 3) { c[i] -= 3; int ok = v_melds(c, left - 1); c[i] += 3; if (ok) return 1; }
    if (i < 27 && i % 9 <= 6 && c[i + 1] && c[i + 2]) {
        c[i]--; c[i + 1]--; c[i + 2]--;
        int ok = v_melds(c, left - 1);
        c[i]++; c[i + 1]++; c[i + 2]++;
        if (ok) return 1;
    }
    return 0;
}
static int v_win(uint8_t *c, int variant) {
    for (int j = 0; j < NT; j++)
        if (c[j] >= 2) { c[j] -= 2; int ok = v_melds(c, 4); c[j] += 2; if (ok) return 1; }
    int n2 = 0, even = 1;
    for (int t = 0; t < NT; t++) { if (c[t] == 2) n2++; if (c[t] & 1) even = 0; }
    if (n2 == 7) return 1;
    if (variant == 'Q' && even) {
        int pairs = 0, ok = 1;
        for (int t = 0; t < NT; t++) { if (c[t] > 4) ok = 0; pairs += c[t] / 2; }
        if (ok && pairs == 7) return 1;
    }
    int kk = 1;
    for (int t = 0; t < NT; t++) {
        int orph = (ORPHAN_MASK >> t) & 1;
        if (orph && c[t] < 1) kk = 0;
        if (!orph && c[t] > 0) kk = 0;
    }
    return kk;
}
static uint64_t v_waits(const uint8_t *c0, int variant) {
    if (variant == 'S') return waits_all(c0);
    uint8_t c[NT];
    memcpy(c, c0, NT);
    uint64_t W = 0;
    for (int t = 0; t < NT; t++) {
        if (variant != 'F' && c[t] >= 4) continue;
        c[t]++;
        if (v_win(c, variant)) W |= 1ull << t;
        c[t]--;
    }
    return W;
}

/* ---------- part 1 ---------- */
typedef struct { uint16_t sup; uint64_t W[3]; uint8_t v[9]; } SH;
static SH *hands; static int nh = 0;

static int64_t ipow(int b, int e) { int64_t r = 1; while (e--) r *= b; return r; }

static void part1(void) {
    hands = malloc(sizeof(SH) * 100000);
    int v[9] = {0};
    uint8_t c[NT];
    for (;;) {
        int s = 0;
        for (int i = 0; i < 9; i++) s += v[i];
        if (s == 13) {
            memset(c, 0, NT);
            SH h; h.sup = 0;
            for (int i = 0; i < 9; i++) { c[i] = (uint8_t)v[i]; h.v[i] = (uint8_t)v[i]; if (v[i]) h.sup |= 1 << i; }
            h.W[0] = v_waits(c, 'S'); h.W[1] = v_waits(c, 'F'); h.W[2] = v_waits(c, 'Q');
            hands[nh++] = h;
        }
        int i = 0;
        while (i < 9 && v[i] == 4) { v[i] = 0; i++; }
        if (i == 9) break;
        v[i]++;
    }
    int nt[3] = {0, 0, 0};
    for (int i = 0; i < nh; i++) for (int r = 0; r < 3; r++) nt[r] += hands[i].W[r] != 0;
    printf("Part 1: single-suit hands = %d ; tenpai under S/F/Q = %d / %d / %d\n", nh, nt[0], nt[1], nt[2]);
    const char *vn = "SFQ";
    /* per U: distinct classes and min vectors */
    static uint64_t keys[4096];
    static uint8_t mins[4096][9];
    static int cnt;
    int best_margin[3] = {-99999, -99999, -99999};
    printf("  U (tiles of one suit)   |U|  N_S  L3_S  N_F  L3_F  N_Q  L3_Q   |U|^1 |U|^2 |U|^3 |U|^4\n");
    for (int U = 1; U < 512; U++) {
        int u = __builtin_popcount(U);
        int N[3], L3[3], L4[3], L2[3], L1[3];
        for (int r = 0; r < 3; r++) {
            cnt = 0;
            for (int i = 0; i < nh; i++) {
                if (hands[i].sup & ~U) continue;
                uint64_t W = hands[i].W[r];
                if (!W) continue;
                int j;
                for (j = 0; j < cnt; j++) if (keys[j] == W) break;
                if (j == cnt) { keys[cnt] = W; memcpy(mins[cnt], hands[i].v, 9); cnt++; }
                else for (int q = 0; q < 9; q++) if (hands[i].v[q] < mins[j][q]) mins[j][q] = hands[i].v[q];
            }
            N[r] = cnt; L1[r] = L2[r] = L3[r] = L4[r] = 0;
            for (int j = 0; j < cnt; j++) {
                int s = 0;
                for (int q = 0; q < 9; q++) s += mins[j][q];
                if (s < 1) L1[r]++;
                if (s < 2) L2[r]++;
                if (s < 3) L3[r]++;
                if (s < 4) L4[r]++;
            }
            int margin = N[r] + L3[r] - (int)ipow(u, 3);
            if (margin > best_margin[r]) best_margin[r] = margin;
        }
        int show = (N[0] + L3[0] > ipow(u, 3)) || (N[1] + L3[1] > ipow(u, 3)) || (N[2] + L3[2] > ipow(u, 3)) ||
                   U == 511 || U == 0x7F || U == 0xFE || U == 0x1FC || U == 0x0FE;
        if (show) {
            char name[16]; int L = 0;
            for (int q = 0; q < 9; q++) if ((U >> q) & 1) name[L++] = (char)('1' + q);
            name[L] = 0;
            printf("  %-9sm               %d  %4d %4d  %4d %4d  %4d %4d   %5lld %5lld %5lld %5lld%s%s\n", name, u,
                   N[0], L3[0], N[1], L3[1], N[2], L3[2], (long long)ipow(u, 1), (long long)ipow(u, 2), (long long)ipow(u, 3),
                   (long long)ipow(u, 4), N[0] > ipow(u, 3) ? "   <== N_S > |U|^3" : "",
                   N[0] + L3[0] > ipow(u, 3) && N[0] <= ipow(u, 3) ? "   <== N_S+L3_S > |U|^3" : "");
        }
        if (U == 511) {
            for (int r = 0; r < 3; r++)
                printf("  full suit, variant %c: N=%d  L1=%d L2=%d L3=%d L4=%d   (k=1: N+L1=%d vs 9 ; k=2: N+L2=%d vs 81)\n",
                       vn[r], N[r], L1[r], L2[r], L3[r], L4[r], N[r] + L1[r], N[r] + L2[r]);
        }
    }
    for (int r = 0; r < 3; r++)
        printf("  variant %c: max over U of (N+L3-|U|^3) = %d\n", vn[r], best_margin[r]);
}

/* ---------- part 2: suit + honors, rule S, all 2^16 subsets ---------- */
#define MAXW 8192
static uint64_t wkey[MAXW];
static int nw = 0;
static uint8_t *upset; /* per class: bitmap over 2^16 sets */

static int w_index(uint64_t W) {
    for (int i = 0; i < nw; i++) if (wkey[i] == W) return i;
    wkey[nw] = W;
    return nw++;
}

static void part2(void) {
    const int TU[16] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 32, 33};
    int v[16] = {0};
    uint8_t c[NT];
    upset = calloc((size_t)MAXW * 65536 / 8, 1);
    int64_t nhands = 0, ntp = 0;
    for (;;) {
        int s = 0;
        for (int i = 0; i < 16; i++) s += v[i];
        if (s == 13) {
            memset(c, 0, NT);
            int sup = 0;
            for (int i = 0; i < 16; i++) { c[TU[i]] = (uint8_t)v[i]; if (v[i]) sup |= 1 << i; }
            nhands++;
            uint64_t W = waits_all(c);
            if (W) {
                ntp++;
                int wi = w_index(W);
                upset[(size_t)wi * 8192 + (sup >> 3)] |= (uint8_t)(1 << (sup & 7));
            }
        }
        /* odometer with pruning on partial sum */
        int i = 0;
        for (;;) {
            if (i == 16) goto done;
            v[i]++;
            int ps = 0;
            for (int q = 0; q < 16; q++) ps += v[q];
            if (v[i] <= 4 && ps <= 13) break;
            v[i] = 0; i++;
        }
    }
done:
    printf("Part 2: hands over (one suit + 7 honors) = %lld ; tenpai = %lld ; classes = %d\n",
           (long long)nhands, (long long)ntp, nw);
    /* superset closure for each class, then count */
    int *N = calloc(65536, sizeof(int));
    for (int w = 0; w < nw; w++) {
        uint8_t *b = upset + (size_t)w * 8192;
        for (int bit = 0; bit < 16; bit++)
            for (int S = 0; S < 65536; S++)
                if (!((S >> bit) & 1)) {
                    int T = S | (1 << bit);
                    if ((b[S >> 3] >> (S & 7)) & 1) b[T >> 3] |= (uint8_t)(1 << (T & 7));
                }
        for (int S = 0; S < 65536; S++) if ((b[S >> 3] >> (S & 7)) & 1) N[S]++;
    }
    int found = 0, best = -999999, bestS = 0;
    for (int S = 1; S < 65536; S++) {
        int u = __builtin_popcount(S);
        int margin = N[S] - (int)ipow(u, 3);
        if (margin > best) { best = margin; bestS = S; }
        if (margin > 0) found++;
    }
    printf("  subsets with N(U) > |U|^3: %d ; best margin N-|U|^3 = %d at U = {", found, best);
    for (int i = 0; i < 16; i++) if ((bestS >> i) & 1) printf(" %s", TN[TU[i]]);
    printf(" } (N=%d, |U|^3=%lld)\n", N[bestS], (long long)ipow(__builtin_popcount(bestS), 3));
    printf("  the 10 best U (by N - |U|^3):\n");
    for (int rep = 0; rep < 10; rep++) {
        int bm = -999999, bs = 0;
        for (int S = 1; S < 65536; S++) {
            int u = __builtin_popcount(S);
            int margin = N[S] - (int)ipow(u, 3);
            if (margin > bm) { bm = margin; bs = S; }
        }
        printf("    N=%4d |U|=%2d |U|^3=%5lld margin=%5d  U={", N[bs], __builtin_popcount(bs),
               (long long)ipow(__builtin_popcount(bs), 3), bm);
        for (int i = 0; i < 16; i++) if ((bs >> i) & 1) printf(" %s", TN[TU[i]]);
        printf(" }\n");
        N[bs] = -1000000;
    }
}

int main(int argc, char **argv) {
    mj_init();
    uint64_t t0 = GetTickCount64();
    part1();
    if (argc > 1 && !strcmp(argv[1], "-part2")) part2();
    printf("elapsed %.1f s\n", (GetTickCount64() - t0) / 1000.0);
    return 0;
}
