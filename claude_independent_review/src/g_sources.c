/*
 * g_sources.c -- what could "7,427,311 standard winning hands" (work/recon/TENPAI_COUNT.md,
 * path B) count?  We count, among the 11,498,658 distinct standard 14-tile hands G:
 *   (1) all of them,
 *   (2) those that are the canonical source G = H + min W_std(H) of at least one
 *       standard-tenpai hand H,
 *   (3) the same with min over the full W(H) (all three winning forms).
 */
#include "tenpai_enum.h"

static volatile int64_t NEXT, DONE;
static int64_t cnt_all[64], cnt_src_std[64], cnt_src_all[64];

static DWORD __stdcall worker(void *arg) {
    int id = (int)(intptr_t)arg;
    uint8_t c[NT];
    for (;;) {
        int64_t item = __atomic_fetch_add(&NEXT, 1, __ATOMIC_RELAXED);
        if (item >= nOPT_N) break;
        memset(c, 0, NT);
        const Opt *om = &OPT_N[item];
        memcpy(c, om->v, 9);
        int r1 = 14 - om->size;
        for (int sp = 0; sp <= r1; sp++)
            for (int ip = BN_lo[sp]; ip < BN_hi[sp]; ip++) {
                const Opt *op = &OPT_N[ip];
                int np2 = om->isP + op->isP;
                if (np2 > 1) continue;
                memcpy(c + 9, op->v, 9);
                int r2 = r1 - sp;
                for (int ss = 0; ss <= r2; ss++)
                    for (int is = BN_lo[ss]; is < BN_hi[ss]; is++) {
                        const Opt *os = &OPT_N[is];
                        int np3 = np2 + os->isP;
                        if (np3 > 1) continue;
                        memcpy(c + 18, os->v, 9);
                        int r3 = r2 - ss;
                        for (int iz = BZ_lo[r3]; iz < BZ_hi[r3]; iz++) {
                            const Opt *oz = &OPT_Z[iz];
                            if (np3 + oz->isP != 1) continue;
                            memcpy(c + 27, oz->v, 7);
                            cnt_all[id]++;
                            int s1 = 0, s2 = 0;
                            for (int t = 0; t < NT; t++) {
                                if (!c[t]) continue;
                                c[t]--;
                                uint64_t ws = waits_std(c), wa = waits_all(c);
                                if (ws && ctz64(ws) == t) s1 = 1;
                                if (wa && ctz64(wa) == t) s2 = 1;
                                c[t]++;
                            }
                            cnt_src_std[id] += s1;
                            cnt_src_all[id] += s2;
                        }
                    }
            }
        __atomic_fetch_add(&DONE, 1, __ATOMIC_RELAXED);
    }
    return 0;
}

int main(void) {
    mj_init();
    enum_prepare();
    int nth = 15;
    void *args[64];
    for (int i = 0; i < nth; i++) args[i] = (void *)(intptr_t)i;
    NEXT = 0;
    DONE = 0;
    int ok = run_threads(worker, args, nth);
    if (DONE != nOPT_N) { printf("ENUMERATION INCOMPLETE: %lld of %d work items processed\n", (long long)DONE, nOPT_N); ok = 0; }
    int64_t a = 0, b = 0, d = 0;
    for (int i = 0; i < nth; i++) { a += cnt_all[i]; b += cnt_src_std[i]; d += cnt_src_all[i]; }
    printf("distinct standard 14-tile winning hands: %lld\n", (long long)a);
    printf("  ... that are H + min W_std(H) for some standard-tenpai H: %lld\n", (long long)b);
    printf("  ... that are H + min W(H) for some tenpai H:              %lld\n", (long long)d);
    printf("RESULT: %s\n", ok ? "OK" : "FAILED");
    return ok ? 0 : 1;
}
