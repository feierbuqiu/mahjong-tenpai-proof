/*
 * t4cost.c -- size of the kernel check T4 per shape (for splitting it into declarations).
 *
 * Mirrors `Tenpai.t4okA` / `Tenpai.t4okB`: for every shape (n0..n3, sum 13) accepted by shape1 / shape2,
 * the hands enumerated are the products of the candidate lists `t4list` (fields <= 2, at most one
 * single; inert categories must also be melds).  Prints, per check and shape:
 *   hands  = product of the list lengths (iterations of the inner loop)
 *   evals  = hands with exactly one single and a nonzero standard mask (these do a plan lookup)
 * usage: t4cost.exe
 */
#include "../../src/mjcore.h"

static int LEN[4] = {9, 9, 9, 7};
static inline int st(int k, int idx) { return k < 3 ? ST_N[idx] : ST_Z[idx]; }

typedef struct { int idx, singles, m, p, wm, wp; } V;
static V L[2][4][14][2000];
static int NL[2][4][14];

static void gen(int k, int pos, int rem, int idx, int singles, int n) {
    if (pos == LEN[k]) {
        if (rem != 0 || singles > 1) return;
        int s = st(k, idx), wm = 0, wp = 0, x = idx;
        int c[9];
        for (int i = 0; i < LEN[k]; i++) { c[i] = x % 5; x /= 5; }
        for (int i = 0; i < LEN[k]; i++)
            if (c[i] < 4) {
                int s2 = st(k, idx + P5[i]);
                if (s2 & 1) wm |= 1 << i;
                if (s2 & 2) wp |= 1 << i;
            }
        V v = {idx, singles, s & 1, (s >> 1) & 1, wm, wp};
        L[1][k][n][NL[1][k][n]++] = v;          /* active: all candidates */
        if (s & 1) L[0][k][n][NL[0][k][n]++] = v; /* inert: melds only */
        return;
    }
    for (int d = 0; d <= 2 && d <= rem; d++) gen(k, pos + 1, rem - d, idx + d * P5[pos], singles + (d == 1), n);
}

int main(void) {
    mj_init();
    for (int k = 0; k < 4; k++)
        for (int n = 0; n <= 13; n++) gen(k, 0, n, 0, 0, n);
    double totH = 0, totE = 0;
    for (int x = 0; x < 4; x++)
        for (int y = x; y < 4; y++) {          /* y == x : check A for x; y > x : check B for (x, y) */
            double cH = 0, cE = 0;
            int nshape = 0;
            for (int n0 = 0; n0 <= 13; n0++)
                for (int n1 = 0; n0 + n1 <= 13; n1++)
                    for (int n2 = 0; n0 + n1 + n2 <= 13; n2++) {
                        int n[4] = {n0, n1, n2, 13 - n0 - n1 - n2};
                        int ok = 1;
                        for (int k = 0; k < 4; k++) {
                            int act = (k == x || k == y);
                            int want = (y == x) ? (act ? 1 : 0) : (act ? 2 : 0);
                            if (n[k] % 3 != want) ok = 0;
                        }
                        if (y == x && n[x] < 4) ok = 0;
                        if (!ok) continue;
                        nshape++;
                        int a[4];
                        for (int k = 0; k < 4; k++) a[k] = (k == x || k == y);
                        double hands = 1;
                        for (int k = 0; k < 4; k++) hands *= NL[a[k]][k][n[k]];
                        /* evals: enumerate */
                        long ev = 0;
                        for (int i0 = 0; i0 < NL[a[0]][0][n[0]]; i0++)
                            for (int i1 = 0; i1 < NL[a[1]][1][n[1]]; i1++)
                                for (int i2 = 0; i2 < NL[a[2]][2][n[2]]; i2++)
                                    for (int i3 = 0; i3 < NL[a[3]][3][n[3]]; i3++) {
                                        V *v[4] = {&L[a[0]][0][n[0]][i0], &L[a[1]][1][n[1]][i1], &L[a[2]][2][n[2]][i2], &L[a[3]][3][n[3]][i3]};
                                        int s = v[0]->singles + v[1]->singles + v[2]->singles + v[3]->singles;
                                        if (s != 1) continue;
                                        long mask;
                                        if (y == x) mask = v[x]->wp;
                                        else mask = (v[y]->p ? v[x]->wm : 0) | (v[x]->p ? v[y]->wm : 0);
                                        if (mask) ev++;
                                    }
                        printf("%s x=%d y=%d shape=%d,%d,%d,%d lists=%d,%d,%d,%d hands=%.0f evals=%ld\n",
                               y == x ? "A" : "B", x, y, n[0], n[1], n[2], n[3],
                               NL[a[0]][0][n[0]], NL[a[1]][1][n[1]], NL[a[2]][2][n[2]], NL[a[3]][3][n[3]], hands, ev);
                        cH += hands; cE += ev;
                    }
            printf("TOTAL %s x=%d y=%d shapes=%d hands=%.0f evals=%.0f\n", y == x ? "A" : "B", x, y, nshape, cH, cE);
            totH += cH; totE += cE;
        }
    printf("GRAND hands=%.0f evals=%.0f\n", totH, totE);
    return 0;
}
