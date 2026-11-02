#!/usr/bin/env python3
"""rag.py - Resource-Allocation Graph dari matriks Allocation/Max/Available,
identifikasi 4 kondisi deadlock, dan deteksi deadlock.
Pemakaian:
  python3 rag.py                          # state awal dari matriks.json
  python3 rag.py --request T4 3 3 0       # state setelah T4 diberi (3,3,0)
Keluaran: teks di terminal + rag_<nama>.dot (+ .png bila Graphviz 'dot' terpasang)
"""
import argparse, json, shutil, subprocess


def cari_siklus(graf):
    warna, tumpuk = {}, []

    def dfs(u):
        warna[u] = 1; tumpuk.append(u)
        for v in graf.get(u, []):
            if warna.get(v, 0) == 0:
                r = dfs(v)
                if r: return r
            elif warna[v] == 1:
                return tumpuk[tumpuk.index(v):] + [v]
        warna[u] = 2; tumpuk.pop()
        return None

    for s in list(graf):
        if warna.get(s, 0) == 0:
            r = dfs(s)
            if r: return r
    return None


def deteksi(tasks, alloc, need, avail):
    """Algoritma deteksi (kasus terburuk: semua task meminta Need-nya)."""
    work, fin = list(avail), [False] * len(tasks)
    maju = True
    while maju:
        maju = False
        for i in range(len(tasks)):
            if not fin[i] and all(n <= w for n, w in zip(need[i], work)):
                work = [w + a for w, a in zip(work, alloc[i])]; fin[i] = True; maju = True
    return [t for t, f in zip(tasks, fin) if not f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="matriks.json")
    ap.add_argument("--request", nargs="+")
    a = ap.parse_args()
    d = json.load(open(a.data, encoding="utf-8"))
    tasks, res = d["tasks"], d["resources"]
    alloc = [r[:] for r in d["allocation"]]; mx = d["max"]; avail = d["available"][:]
    nama = "awal"
    if a.request:
        i = tasks.index(a.request[0]); rq = [int(x) for x in a.request[1:]]
        alloc[i] = [x + r for x, r in zip(alloc[i], rq)]
        avail = [x - r for x, r in zip(avail, rq)]
        nama = f"{a.request[0]}_{'-'.join(map(str, rq))}"
        print(f"*** State setelah {a.request[0]} diberi {rq} ***")
    need = [[m - x for m, x in zip(rm, ra)] for rm, ra in zip(mx, alloc)]
    print(f"Available = {avail}")

    # --- sisi graf ---
    ea = [(res[j], tasks[i], alloc[i][j]) for i in range(len(tasks)) for j in range(len(res)) if alloc[i][j] > 0]
    er = [(tasks[i], res[j], need[i][j]) for i in range(len(tasks)) for j in range(len(res)) if need[i][j] > avail[j]]
    print("\n=== RESOURCE-ALLOCATION GRAPH ===")
    print("Sisi alokasi (R -> T, jumlah instans yang dipegang):")
    for r, t, n in ea: print(f"  {r:<6} -> {t}  [{n}]")
    print("Sisi permintaan (T -> R, Need yang belum bisa dipenuhi Available):")
    for t, r, n in er: print(f"  {t} -> {r:<6} [{n}]")

    # --- wait-for graph & siklus ---
    wf = {}
    for i, t in enumerate(tasks):
        for j in range(len(res)):
            if need[i][j] > avail[j]:
                for k, u in enumerate(tasks):
                    if k != i and alloc[k][j] > 0 and u not in wf.setdefault(t, []):
                        wf[t].append(u)
    print("\n=== WAIT-FOR GRAPH (T_i -> T_k : T_i menunggu sumber daya yang dipegang T_k) ===")
    for t, vs in wf.items(): print(f"  {t} -> {', '.join(vs)}")
    sik = cari_siklus(wf)
    print("Siklus:", " -> ".join(sik) if sik else "tidak ada")

    macet = deteksi(tasks, alloc, need, avail)
    holders_wait = [tasks[i] for i in range(len(tasks)) if sum(alloc[i]) > 0 and any(need[i][j] > avail[j] for j in range(len(res)))]
    print("\n=== 4 KONDISI DEADLOCK (Coffman) ===")
    print("1. Mutual exclusion : TERPENUHI - tiap instans pompa/katup/slot I2C hanya dipakai satu task sekali waktu")
    print(f"2. Hold and wait    : {'TERPENUHI' if holders_wait else 'tidak terpenuhi'} - {', '.join(holders_wait) or '-'} memegang sumber daya sambil menunggu tambahan")
    print("3. No preemption    : TERPENUHI - pompa/katup/bus yang sedang dipakai tidak boleh direbut paksa")
    print(f"4. Circular wait    : {'TERPENUHI' if sik else 'tidak terpenuhi'} - {' -> '.join(sik) if sik else 'tidak ada siklus pada wait-for graph'}")
    print("\n=== DETEKSI DEADLOCK (semua task meminta Need-nya) ===")
    if macet:
        print(f"DEADLOCK: task {macet} tidak dapat menyelesaikan pekerjaan")
    else:
        print("TIDAK ADA DEADLOCK: semua task dapat selesai (state aman)")

    # --- berkas dot ---
    fn = f"rag_{nama}"
    with open(fn + ".dot", "w", encoding="utf-8") as f:
        f.write("digraph RAG {\n rankdir=LR; nodesep=0.4;\n")
        for j, r in enumerate(res):
            dots = "●" * min(sum(alloc[k][j] for k in range(len(tasks))) + avail[j], 12)
            f.write(f' "{r}" [shape=box, style=filled, fillcolor="#E8F0FA", label="{r}\\n{dots}"];\n')
        for t in tasks: f.write(f' "{t}" [shape=circle, style=filled, fillcolor="#FFF4D6"];\n')
        for r, t, n in ea: f.write(f' "{r}" -> "{t}" [label="{n}"];\n')
        for t, r, n in er: f.write(f' "{t}" -> "{r}" [label="{n}", style=dashed, color="#B03030", fontcolor="#B03030"];\n')
        f.write("}\n")
    print(f"\nBerkas {fn}.dot dibuat.")
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", "-Gdpi=130", fn + ".dot", "-o", fn + ".png"], check=True)
        print(f"Berkas {fn}.png dibuat.")
    else:
        print("Graphviz belum terpasang: jalankan 'sudo apt install -y graphviz' lalu ulangi.")


if __name__ == "__main__":
    main()
