/*
 * plan_split.c -- split the large kernel checks into declarations of bounded size.
 *
 * T1 and T2 are split along the prefix tree of `Tenpai.allVecs` (fix the lowest fields of the
 * outer category vector); T4 is split into ranges of shapes (index 196 n0 + 14 n1 + n2).
 * A cost model (seconds of kernel time, calibrated on single runs) decides where to cut.
 * Output lines (leaves only; the prefix tree is rebuilt by the generator):
 *   T1 k n cost d0 d1 ... dj-1
 *   T2 x y nx ny rev cost d0 ... dj-1          (rev = 1: outer loop over category y)
 *   T4A x lo hi cost
 *   T4B x y lo hi cost
 * usage: plan_split.exe out.txt [budget_sec]
 */
#include "../../src/mjcore.h"

static int LEN[4] = {9, 9, 9, 7};
static inline int st(int k, int idx) { return k < 3 ? ST_N[idx] : ST_Z[idx]; }

/* per-vector info: p = splits as pair + melds, wm = wait-to-melds mask (local) */
static int info_p(int k, int idx) { return (st(k, idx) >> 1) & 1; }
static int info_wm(int k, int idx) {
    int c[9], x = idx, m = 0;
    for (int i = 0; i < LEN[k]; i++) { c[i] = x % 5; x /= 5; }
    for (int i = 0; i < LEN[k]; i++) if (c[i] < 4 && (st(k, idx + P5[i]) & 1)) m |= 1 << i;
    return m;
}

/* ---------------- cost model (seconds) ---------------- */
static double BUDGET = 10.0;
static double C1[4] = {0.0033, 0.0033, 0.0033, 0.0020};          /* T1 per vector */
static double COUT[14] = {0, 0, 0.0008, 0, 0, 0.0016, 0, 0, 0.0017, 0, 0, 0.0018, 0, 0}; /* T2 per outer vector by size */
static double CPAIR = 0.00017, CUNIT = 0.0, CINNER = 0.0016;     /* T2 per pair / per unit / per inner vector built */

static FILE *OUT;
static int cnt_tab[10][40];
static int cnt(int L, int r) {
    if (r < 0 || r > 4 * L) return 0;
    if (L == 0) return r == 0;
    if (cnt_tab[L][r] >= 0) return cnt_tab[L][r];
    int s = 0;
    for (int d = 0; d <= 4 && d <= r; d++) s += cnt(L - 1, r - d);
    return cnt_tab[L][r] = s;
}

/* ---------------- T1 ---------------- */
static int T1leaves = 0;
static double T1cost = 0;
static void t1node(int k, int n, int *pre, int j, int r) {
    int m = LEN[k] - j;
    double cost = cnt(m, r) * C1[k];
    if (cost <= BUDGET || m == 0) {
        fprintf(OUT, "T1 %d %d %.2f", k, n, cost);
        for (int i = 0; i < j; i++) fprintf(OUT, " %d", pre[i]);
        fprintf(OUT, "\n");
        T1leaves++; T1cost += cost;
        return;
    }
    for (int d = 0; d <= 4; d++) {
        if (d > r || r - d > 4 * (m - 1)) continue;
        pre[j] = d;
        t1node(k, n, pre, j + 1, r - d);
    }
}

/* ---------------- T2 ---------------- */
static int innerP[2000], innerW[2000], nInner, nInnerAll;
static int OK_, IK_;   /* outer category, inner category */
static double t2acc_n, t2acc_rel, t2acc_units;
/* enumerate outer vectors of category OK_ below a prefix: positions pos..LEN-1, remaining r, index idx */
static void t2enum(int pos, int r, int idx) {
    if (pos == LEN[OK_]) {
        if (r) return;
        t2acc_n += 1;
        int p = info_p(OK_, idx), w = info_wm(OK_, idx);
        if (!(p || w)) return;
        t2acc_rel += 1;
        for (int i = 0; i < nInner; i++)
            if ((innerP[i] && w) || (p && innerW[i])) t2acc_units += 1;
        return;
    }
    for (int d = 0; d <= 4 && d <= r; d++) t2enum(pos + 1, r - d, idx + d * P5[pos]);
}
static int t2gen_inner(int k, int pos, int r, int idx) {
    if (pos == LEN[k]) {
        if (r) return 0;
        nInnerAll++;
        int p = info_p(k, idx), w = info_wm(k, idx);
        if (p || w) { innerP[nInner] = p; innerW[nInner] = w; nInner++; }
        return 0;
    }
    for (int d = 0; d <= 4 && d <= r; d++) t2gen_inner(k, pos + 1, r - d, idx + d * P5[pos]);
    return 0;
}
static int T2leaves = 0;
static double T2cost = 0, T2units = 0;
static void t2node(int x, int y, int nx, int ny, int rev, int nout, int *pre, int j, int r, int idx) {
    int m = LEN[OK_] - j;
    t2acc_n = t2acc_rel = t2acc_units = 0;
    t2enum(j, r, idx);
    double cost = t2acc_n * COUT[nout] + t2acc_rel * nInner * CPAIR + t2acc_units * CUNIT + nInnerAll * CINNER;
    if (t2acc_n == 0) return;  /* cannot happen for valid children */
    if (cost <= BUDGET || m == 0) {
        fprintf(OUT, "T2 %d %d %d %d %d %.2f", x, y, nx, ny, rev, cost);
        for (int i = 0; i < j; i++) fprintf(OUT, " %d", pre[i]);
        fprintf(OUT, "\n");
        T2leaves++; T2cost += cost; T2units += t2acc_units;
        return;
    }
    for (int d = 0; d <= 4; d++) {
        if (d > r || r - d > 4 * (m - 1)) continue;
        pre[j] = d;
        t2node(x, y, nx, ny, rev, nout, pre, j + 1, r - d, idx + d * P5[j]);
    }
}

/* ---------------- T4 ---------------- */
typedef struct { int idx, singles, m, p, wm, wp; } V;
static V L4[2][4][14][600];
static int NL4[2][4][14];
static void gen4(int k, int pos, int rem, int idx, int singles, int n) {
    if (pos == LEN[k]) {
        if (rem != 0 || singles > 1) return;
        int s = st(k, idx);
        V v = {idx, singles, s & 1, (s >> 1) & 1, info_wm(k, idx), 0};
        int c[9], x = idx;
        for (int i = 0; i < LEN[k]; i++) { c[i] = x % 5; x /= 5; }
        for (int i = 0; i < LEN[k]; i++) if (c[i] < 4 && (st(k, idx + P5[i]) & 2)) v.wp |= 1 << i;
        L4[1][k][n][NL4[1][k][n]++] = v;
        if (s & 1) L4[0][k][n][NL4[0][k][n]++] = v;
        return;
    }
    for (int d = 0; d <= 2 && d <= rem; d++) gen4(k, pos + 1, rem - d, idx + d * P5[pos], singles + (d == 1), n);
}
static double T4cost = 0;
static int T4pieces = 0;
static void t4check(int x, int y) {   /* y == x: check A */
    double acc = 0;
    int lo = 0;
    double hcost = 0.00037, ecost = (y == x) ? 0.020 : 0.010;
    for (int n0 = 0; n0 <= 13; n0++)
        for (int n1 = 0; n1 <= 13; n1++)
            for (int n2 = 0; n2 <= 13; n2++) {
                if (n0 + n1 + n2 > 13) continue;
                int n[4] = {n0, n1, n2, 13 - n0 - n1 - n2}, ok = 1, a[4];
                for (int k = 0; k < 4; k++) {
                    a[k] = (k == x || k == y);
                    int want = (y == x) ? (a[k] ? 1 : 0) : (a[k] ? 2 : 0);
                    if (n[k] % 3 != want) ok = 0;
                }
                if (y == x && n[x] < 4) ok = 0;
                if (!ok) continue;
                double hands = 1;
                for (int k = 0; k < 4; k++) hands *= NL4[a[k]][k][n[k]];
                long ev = 0;
                for (int i0 = 0; i0 < NL4[a[0]][0][n[0]]; i0++)
                    for (int i1 = 0; i1 < NL4[a[1]][1][n[1]]; i1++)
                        for (int i2 = 0; i2 < NL4[a[2]][2][n[2]]; i2++)
                            for (int i3 = 0; i3 < NL4[a[3]][3][n[3]]; i3++) {
                                V *v[4] = {&L4[a[0]][0][n[0]][i0], &L4[a[1]][1][n[1]][i1], &L4[a[2]][2][n[2]][i2], &L4[a[3]][3][n[3]][i3]};
                                if (v[0]->singles + v[1]->singles + v[2]->singles + v[3]->singles != 1) continue;
                                long mask = (y == x) ? v[x]->wp : ((v[y]->p ? v[x]->wm : 0) | (v[x]->p ? v[y]->wm : 0));
                                if (mask) ev++;
                            }
                double c = hands * hcost + ev * ecost + 0.05;
                int index = 196 * n0 + 14 * n1 + n2;
                if (acc > 0 && acc + c > BUDGET * 1.5) {
                    if (y == x) fprintf(OUT, "T4A %d %d %d %.2f\n", x, lo, index, acc);
                    else fprintf(OUT, "T4B %d %d %d %d %.2f\n", x, y, lo, index, acc);
                    T4pieces++; T4cost += acc;
                    lo = index; acc = 0;
                }
                acc += c;
            }
    if (y == x) fprintf(OUT, "T4A %d %d %d %.2f\n", x, lo, 2744, acc);
    else fprintf(OUT, "T4B %d %d %d %d %.2f\n", x, y, lo, 2744, acc);
    T4pieces++; T4cost += acc;
}

int main(int argc, char **argv) {
    mj_init();
    if (argc < 2) { printf("usage: plan_split out.txt [budget]\n"); return 1; }
    if (argc > 2) BUDGET = atoi(argv[2]);
    if (argc > 6 && argv[1][0] == 'P' && argv[1][1] == 0) {   /* probe: P x y nx ny rev d0 d1 ... */
        int x = atoi(argv[2]), y = atoi(argv[3]), nx = atoi(argv[4]), ny = atoi(argv[5]), rev = atoi(argv[6]);
        OK_ = rev ? y : x; IK_ = rev ? x : y;
        int nout = rev ? ny : nx, nin = rev ? nx : ny, r = nout, idx = 0, j = 0;
        for (int i = 7; i < argc; i++) { int d = atoi(argv[i]); r -= d; idx += d * P5[j]; j++; }
        nInner = nInnerAll = 0;
        t2gen_inner(IK_, 0, nin, 0);
        t2acc_n = t2acc_rel = t2acc_units = 0;
        t2enum(j, r, idx);
        printf("outer=%.0f rel=%.0f inner=%d innerAll=%d pairs=%.0f units=%.0f\n", t2acc_n, t2acc_rel, nInner,
               nInnerAll, t2acc_rel * nInner, t2acc_units);
        return 0;
    }
    for (int L = 0; L < 10; L++) for (int r = 0; r < 40; r++) cnt_tab[L][r] = -1;
    OUT = fopen(argv[1], "wb");
    int pre[16];
    int sizes1[4] = {4, 7, 10, 13};
    for (int k = 0; k < 4; k++)
        for (int si = 0; si < 4; si++) t1node(k, sizes1[si], pre, 0, sizes1[si]);
    printf("T1: %d leaves, est %.0f s\n", T1leaves, T1cost);
    int sizes2[4] = {2, 5, 8, 11};
    for (int x = 0; x < 4; x++)
        for (int y = x + 1; y < 4; y++)
            for (int a = 0; a < 4; a++)
                for (int b = 0; b < 4; b++) {
                    int nx = sizes2[a], ny = sizes2[b];
                    if (nx + ny > 13) continue;
                    int rev = ny > nx;
                    OK_ = rev ? y : x; IK_ = rev ? x : y;
                    int nout = rev ? ny : nx, nin = rev ? nx : ny;
                    nInner = nInnerAll = 0;
                    t2gen_inner(IK_, 0, nin, 0);
                    t2node(x, y, nx, ny, rev, nout, pre, 0, nout, 0);
                }
    printf("T2: %d leaves, est %.0f s, units %.0f\n", T2leaves, T2cost, T2units);
    for (int k = 0; k < 4; k++) for (int n = 0; n <= 13; n++) gen4(k, 0, n, 0, 0, n);
    for (int x = 0; x < 4; x++)
        for (int y = x; y < 4; y++) t4check(x, y);
    printf("T4: %d pieces, est %.0f s\n", T4pieces, T4cost);
    fclose(OUT);
    return 0;
}
