/*
 * selftest.c -- cross-check the fast table-driven W(H) against the naive
 *               recursive reference on (a) hand-picked hands, (b) every
 *               single-suit and every honor-only 13-tile hand, (c) many random
 *               hands near tenpai.
 */
#include "mjcore.h"

static uint64_t rng = 88172645463325252ull;
static inline uint64_t xr(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng; }

static int parse_hand(const char *s, uint8_t *c) {
    /* compact notation like "1112345678999m" or "123m456p77z" (z: 1-7 = E S W N P F C) */
    memset(c, 0, NT);
    int digits[20], nd = 0, tot = 0;
    for (const char *p = s; *p; p++) {
        if (*p >= '0' && *p <= '9') digits[nd++] = *p - '0';
        else {
            int base = *p == 'm' ? 0 : *p == 'p' ? 9 : *p == 's' ? 18 : 27;
            for (int i = 0; i < nd; i++) { c[base + digits[i] - 1]++; tot++; }
            nd = 0;
        }
    }
    return tot;
}

static void show(const char *s) {
    uint8_t c[NT];
    int n = parse_hand(s, c);
    char wb[512];
    uint64_t W = waits_all(c), Wn = naive_waits(c);
    mask_to_str(W, wb);
    printf("  %-22s (%d tiles) W={%s}%s\n", s, n, wb, W == Wn ? "" : "   <-- MISMATCH with naive");
}

static int64_t mism = 0, checked = 0;
static void cmp_hand(const uint8_t *c) {
    checked++;
    uint64_t a = waits_all(c), b = naive_waits(c);
    if (a != b) {
        if (mism < 10) {
            char hb[128], wa[512], wb[512];
            hand_to_str(c, hb); mask_to_str(a, wa); mask_to_str(b, wb);
            printf("  MISMATCH %s fast={%s} naive={%s}\n", hb, wa, wb);
        }
        mism++;
    }
}

static void all_in(int base, int n) {
    uint8_t c[NT];
    int v[9];
    for (int i = 0; i < 9; i++) v[i] = 0;
    /* odometer over counts 0..4 */
    for (;;) {
        int s = 0;
        for (int i = 0; i < n; i++) s += v[i];
        if (s == 13) {
            memset(c, 0, NT);
            for (int i = 0; i < n; i++) c[base + i] = (uint8_t)v[i];
            cmp_hand(c);
        }
        int i = 0;
        while (i < n && v[i] == 4) { v[i] = 0; i++; }
        if (i == n) break;
        v[i]++;
    }
}

int main(void) {
    mj_init();
    printf("hand-picked examples:\n");
    show("1112345678999m");
    show("19m19p19s1234567z");
    show("19m19p19s1234566z");
    show("23m456p789s111z55s");
    show("1111p3p456m789m22z");
    show("1111m234p567p789s");
    show("1111m22m33p44p55s6s");
    show("11m22m33m44p55p66s7s");
    show("1112223334445m");
    show("2223334445556m");
    show("2345678m22233344p");
    show("5m");
    printf("all single-suit 13-tile hands (m):\n");
    all_in(0, 9);
    printf("  checked %lld, mismatches %lld\n", (long long)checked, (long long)mism);
    printf("all honor-only 13-tile hands:\n");
    all_in(27, 7);
    printf("  checked %lld, mismatches %lld\n", (long long)checked, (long long)mism);
    printf("random hands:\n");
    uint8_t c[NT];
    for (int it = 0; it < 3000000; it++) {
        memset(c, 0, NT);
        int mode = (int)(xr() % 3), tot = 0;
        if (mode == 0) { /* uniform random 13 tiles */
            while (tot < 13) { int t = (int)(xr() % NT); if (c[t] < 4) { c[t]++; tot++; } }
        } else { /* random melds + pair, then drop one tile and maybe swap one */
            int ok = 1;
            for (int m = 0; m < 4 && ok; m++) {
                if (xr() % 2) { int t = (int)(xr() % NT); if (c[t] + 3 > 4) { ok = 0; break; } c[t] += 3; }
                else {
                    int s = (int)(xr() % 3), r = (int)(xr() % 7), t = 9 * s + r;
                    if (c[t] > 3 || c[t + 1] > 3 || c[t + 2] > 3) { ok = 0; break; }
                    c[t]++; c[t + 1]++; c[t + 2]++;
                }
            }
            int pr = (int)(xr() % NT);
            if (!ok || c[pr] + 2 > 4) continue;
            c[pr] += 2;
            int t;
            do { t = (int)(xr() % NT); } while (!c[t]);
            c[t]--;
            if (mode == 2) {
                do { t = (int)(xr() % NT); } while (!c[t]);
                int u = (int)(xr() % NT);
                if (c[u] < 4) { c[t]--; c[u]++; }
            }
        }
        cmp_hand(c);
    }
    printf("  total checked %lld, mismatches %lld\n", (long long)checked, (long long)mism);
    return mism != 0;
}
