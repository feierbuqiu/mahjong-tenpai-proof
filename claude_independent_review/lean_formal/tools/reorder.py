# Build reorder_plan.c from analyze_plan.c: count, per code, how many T1/T2 units it fits; reorder each class's
# codes by that count (descending), write the reordered plan, and report average scan lengths before/after.
src = open('analyze_plan.c', encoding='utf-8').read()
main_start = src.index('int main(')
pre = src[:main_start]
body = r'''
static int64_t *FITCNT;
static int64_t scan_sum = 0, scan_units = 0;
static int scan_len(uint64_t W, const uint8_t *c) {
    int ci = pm_find(W); if (ci < 0) return -1;
    for (int i = 0; i < PC_n[ci]; i++) if (code_fits(PC_start[ci] + i, c)) return i + 1;
    return -1;
}
static void count_fits(uint64_t W, const uint8_t *c) {
    int ci = pm_find(W); if (ci < 0) return;
    int s = scan_len(W, c); if (s > 0) { scan_sum += s; scan_units++; }
    for (int i = 0; i < PC_n[ci]; i++) if (code_fits(PC_start[ci] + i, c)) FITCNT[PC_start[ci] + i]++;
}
static void for_all_units(int pass) {
    uint8_t h[NT];
    for (int k = 0; k < 4; k++)
        for (int idx = 0; idx < NV(k); idx++) {
            int s = vsize(k, idx);
            if (s % 3 != 1 || s > 13 || s == 1) continue;
            uint64_t W = WPm(k, idx); if (!W) continue;
            memset(h, 0, NT); vec_of(k, idx, h + OFF[k]);
            if (pass == 0) count_fits(W, h); else { int q = scan_len(W, h); if (q > 0) { scan_sum += q; scan_units++; } }
        }
    for (int x = 0; x < 4; x++)
        for (int y = x + 1; y < 4; y++)
            for (int i = 0; i < nl[x]; i++)
                for (int j = 0; j < nl[y]; j++) {
                    if (LS[x][i] + LS[y][j] > 13) continue;
                    uint64_t W = (LP[y][j] ? LWM[x][i] : 0) | (LP[x][i] ? LWM[y][j] : 0);
                    if (!W) continue;
                    memset(h, 0, NT); vec_of(x, lst[x][i], h + OFF[x]); vec_of(y, lst[y][j], h + OFF[y]);
                    if (pass == 0) count_fits(W, h); else { int q = scan_len(W, h); if (q > 0) { scan_sum += q; scan_units++; } }
                }
}
static int64_t *KEYCNT;
static int cmp_code(const void *a, const void *b) {
    int x = *(const int *)a, y = *(const int *)b;
    if (KEYCNT[x] != KEYCNT[y]) return KEYCNT[x] > KEYCNT[y] ? -1 : 1;
    return x - y;
}
int main(int argc, char **argv) {
    mj_init();
    if (argc < 3 || !load_plan(argv[1])) { printf("usage: reorder_plan in.txt out.txt\n"); return 1; }
    FITCNT = calloc(nCodes, sizeof(int64_t));
    for (int k = 0; k < 4; k++) {
        nl[k] = 0;
        for (int idx = 0; idx < NV(k); idx++) {
            int s = vsize(k, idx);
            if (s % 3 != 2 || s > 11) continue;
            uint64_t wm = WMm(k, idx); int p = (st(k, idx) >> 1) & 1;
            if (!wm && !p) continue;
            lst[k][nl[k]] = idx; LWM[k][nl[k]] = wm; LP[k][nl[k]] = (uint8_t)p; LS[k][nl[k]] = (uint8_t)s; nl[k]++;
        }
    }
    for_all_units(0);
    printf("before: units %lld, average scan length %.2f\n", (long long)scan_units, (double)scan_sum / scan_units);
    KEYCNT = FITCNT;
    uint8_t *NEW = malloc(nCodes * PK);
    int *ord = malloc(sizeof(int) * 4096);
    for (int ci = 0; ci < nPC; ci++) {
        for (int i = 0; i < PC_n[ci]; i++) ord[i] = PC_start[ci] + i;
        qsort(ord, PC_n[ci], sizeof(int), cmp_code);
        for (int i = 0; i < PC_n[ci]; i++) memcpy(NEW + (PC_start[ci] + i) * PK, CODE + ord[i] * PK, PK);
    }
    memcpy(CODE, NEW, nCodes * PK);
    scan_sum = scan_units = 0;
    for_all_units(1);
    printf("after:  units %lld, average scan length %.2f\n", (long long)scan_units, (double)scan_sum / scan_units);
    FILE *f = fopen(argv[2], "wb");
    char buf[64];
    for (int ci = 0; ci < nPC; ci++) {
        int L = snprintf(buf, sizeof buf, "%llx %d %d", (unsigned long long)PC_mask[ci], PC_n[ci], PK);
        fwrite(buf, 1, L, f);
        for (int i = 0; i < PC_n[ci] * PK; i++) { L = snprintf(buf, sizeof buf, " %d", CODE[PC_start[ci] * PK + i]); fwrite(buf, 1, L, f); }
        fwrite("\n", 1, 1, f);
    }
    fclose(f);
    return 0;
}
'''
open('reorder_plan.c', 'w', encoding='utf-8').write(pre + body)
