/*
 * mjcore.h -- independent implementation of the tenpai model in
 *             「呆饼问题（二）：听牌信息的排列编码问题.md」 (sections 2.1-2.3).
 *
 * Written from scratch for the independent review; it does not reuse any code
 * from the other party's package.
 *
 * Tiles: 0-8 = 1m..9m, 9-17 = 1p..9p, 18-26 = 1s..9s, 27-33 = E S W N P F C.
 * A hand is a count vector c[34] with 0 <= c[t] <= 4.
 *
 * Winning 14-tile shapes (set G of the definition):
 *   standard  : 4 melds + 1 pair; meld = pon (aaa) or chi (three consecutive
 *               number tiles of one suit); honors never form chi
 *   chiitoi   : exactly 7 distinct tile types with exactly 2 copies each
 *   kokushi   : the 13 terminal/honor types each >= 1, nothing else, 14 tiles
 * W(H) = { t : c_H(t) < 4 and H + t is winning }.
 */
#ifndef MJCORE_H
#define MJCORE_H
#include "minic.h"

#define NT 34
static const char *TN[NT] = {
    "1m","2m","3m","4m","5m","6m","7m","8m","9m",
    "1p","2p","3p","4p","5p","6p","7p","8p","9p",
    "1s","2s","3s","4s","5s","6s","7s","8s","9s",
    "E","S","W","N","P","F","C"};

static const int ORPHANS[13] = {0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33};
static uint64_t ORPHAN_MASK;

#define N5_9 1953125 /* 5^9 */
#define N5_7 78125   /* 5^7 */
/* status bits of one category vector: bit0 = splits into melds only (M),
 *                                     bit1 = splits into melds + exactly one pair (P) */
static uint8_t ST_N[N5_9];
static uint8_t ST_Z[N5_7];
static int P5[10];
static int CAT[NT], POS[NT];

static void mj_init(void) {
    P5[0] = 1;
    for (int i = 1; i < 10; i++) P5[i] = P5[i - 1] * 5;
    for (int t = 0; t < NT; t++) {
        CAT[t] = t < 27 ? t / 9 : 3;
        POS[t] = t < 27 ? t % 9 : t - 27;
    }
    ORPHAN_MASK = 0;
    for (int i = 0; i < 13; i++) ORPHAN_MASK |= 1ull << ORPHANS[i];
    int c[9];
    for (int idx = 0; idx < N5_9; idx++) {
        int x = idx;
        for (int i = 0; i < 9; i++) { c[i] = x % 5; x /= 5; }
        int i = 0;
        while (i < 9 && c[i] == 0) i++;
        int m = 0;
        if (i == 9) m = 1;
        else {
            /* the lowest tile present must start a pon or a chi */
            if (c[i] >= 3 && (ST_N[idx - 3 * P5[i]] & 1)) m = 1;
            if (!m && i <= 6 && c[i + 1] > 0 && c[i + 2] > 0 &&
                (ST_N[idx - P5[i] - P5[i + 1] - P5[i + 2]] & 1)) m = 1;
        }
        int p = 0;
        for (int j = 0; j < 9 && !p; j++)
            if (c[j] >= 2 && (ST_N[idx - 2 * P5[j]] & 1)) p = 1;
        ST_N[idx] = (uint8_t)(m | (p << 1));
    }
    for (int idx = 0; idx < N5_7; idx++) {
        int x = idx, n2 = 0, bad = 0;
        for (int i = 0; i < 7; i++) {
            int v = x % 5; x /= 5;
            if (v == 2) n2++;
            else if (v != 0 && v != 3) bad = 1;
        }
        ST_Z[idx] = (uint8_t)((!bad && n2 == 0) | ((!bad && n2 == 1) << 1));
    }
}

static inline int cat_status(int k, int idx) { return k < 3 ? ST_N[idx] : ST_Z[idx]; }

static inline void cat_index(const uint8_t *c, int *I) {
    for (int k = 0; k < 4; k++) {
        int base = 9 * k, n = k < 3 ? 9 : 7, v = 0;
        for (int i = n - 1; i >= 0; i--) v = v * 5 + c[base + i];
        I[k] = v;
    }
}

/* standard-form waits of a 13-tile hand */
static inline uint64_t waits_std(const uint8_t *c) {
    int I[4], S[4];
    cat_index(c, I);
    for (int k = 0; k < 4; k++) S[k] = cat_status(k, I[k]);
    uint64_t W = 0;
    for (int t = 0; t < NT; t++) {
        if (c[t] >= 4) continue;
        int k = CAT[t];
        int ns = cat_status(k, I[k] + P5[POS[t]]);
        if (!ns) continue;
        int npair = (ns >> 1) & 1, ok = 1;
        for (int j = 0; j < 4; j++) {
            if (j == k) continue;
            if (!S[j]) { ok = 0; break; }
            npair += (S[j] >> 1) & 1;
        }
        if (ok && npair == 1) W |= 1ull << t;
    }
    return W;
}

/* seven-pairs waits: H + t must consist of exactly 7 distinct pairs */
static inline uint64_t waits_chiitoi(const uint8_t *c) {
    int n1 = 0, n2 = 0, other = 0, single = -1;
    for (int t = 0; t < NT; t++) {
        if (c[t] == 1) { n1++; single = t; }
        else if (c[t] == 2) n2++;
        else if (c[t] > 2) other++;
    }
    if (n1 == 1 && n2 == 6 && other == 0) return 1ull << single;
    return 0;
}

/* kokushi waits */
static inline uint64_t waits_kokushi(const uint8_t *c) {
    int distinct = 0, total = 0;
    for (int t = 0; t < NT; t++) {
        if (!c[t]) continue;
        if (!((ORPHAN_MASK >> t) & 1)) return 0;
        distinct++;
        total += c[t];
    }
    if (total != 13) return 0;
    if (distinct == 13) return ORPHAN_MASK;
    if (distinct == 12) {
        for (int i = 0; i < 13; i++)
            if (!c[ORPHANS[i]]) return 1ull << ORPHANS[i];
    }
    return 0;
}

static inline uint64_t waits_all(const uint8_t *c) {
    return waits_std(c) | waits_chiitoi(c) | waits_kokushi(c);
}

/* ---------- naive reference implementation (for cross-checking only) ---------- */
static int naive_melds(uint8_t *c, int left) {
    if (left == 0) return 1;
    int i = 0;
    while (i < NT && c[i] == 0) i++;
    if (i == NT) return left == 0;
    int ok = 0;
    if (c[i] >= 3) {
        c[i] -= 3;
        ok = naive_melds(c, left - 1);
        c[i] += 3;
        if (ok) return 1;
    }
    if (i < 27 && i % 9 <= 6 && c[i + 1] && c[i + 2]) {
        c[i]--; c[i + 1]--; c[i + 2]--;
        ok = naive_melds(c, left - 1);
        c[i]++; c[i + 1]++; c[i + 2]++;
    }
    return ok;
}

static int naive_is_win(uint8_t *c) {
    int tot = 0;
    for (int t = 0; t < NT; t++) { if (c[t] > 4) return 0; tot += c[t]; }
    if (tot != 14) return 0;
    for (int j = 0; j < NT; j++) {
        if (c[j] >= 2) {
            c[j] -= 2;
            int ok = naive_melds(c, 4);
            c[j] += 2;
            if (ok) return 1;
        }
    }
    int n2 = 0;
    for (int t = 0; t < NT; t++) if (c[t] == 2) n2++;
    if (n2 == 7) return 1;
    int kk = 1;
    for (int t = 0; t < NT; t++) {
        int orph = (ORPHAN_MASK >> t) & 1;
        if (orph && c[t] < 1) kk = 0;
        if (!orph && c[t] > 0) kk = 0;
    }
    return kk;
}

static uint64_t naive_waits(const uint8_t *c0) {
    uint8_t c[NT];
    memcpy(c, c0, NT);
    uint64_t W = 0;
    for (int t = 0; t < NT; t++) {
        if (c[t] >= 4) continue;
        c[t]++;
        if (naive_is_win(c)) W |= 1ull << t;
        c[t]--;
    }
    return W;
}

static void mask_to_str(uint64_t W, char *buf) {
    int L = 0, n = 0;
    for (int t = 0; t < NT; t++)
        if ((W >> t) & 1) {
            if (n++) buf[L++] = ',';
            int m = (int)strlen(TN[t]);
            memcpy(buf + L, TN[t], m);
            L += m;
        }
    buf[L] = 0;
}

static void hand_to_str(const uint8_t *c, char *buf) {
    int L = 0;
    for (int t = 0; t < NT; t++)
        for (int r = 0; r < c[t]; r++) {
            const char *s = TN[t];
            int n = (int)strlen(s);
            memcpy(buf + L, s, n);
            L += n;
        }
    buf[L] = 0;
}

static inline int popc64(uint64_t x) { return __builtin_popcountll(x); }
static inline int ctz64(uint64_t x) { return __builtin_ctzll(x); }

#endif
