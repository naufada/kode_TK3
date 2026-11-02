#!/usr/bin/env python3
"""banker.py - Algoritma Banker (safe state + resource-request) untuk TK-3 Deadlock.
Pemakaian:
  python3 banker.py                       # cek safe state
  python3 banker.py --request T1 1 0 2    # uji permintaan T1 meminta (1,0,2)
  python3 banker.py --data matriks.json
"""
import argparse, json, sys


def muat(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hitung_need(mx, alloc):
    return [[m - a for m, a in zip(rm, ra)] for rm, ra in zip(mx, alloc)]


def cetak_matriks(judul, tasks, res, rows, avail=None):
    print(f"\n{judul}")
    print("      " + " ".join(f"{r:>6}" for r in res))
    for t, row in zip(tasks, rows):
        print(f"{t:>4}  " + " ".join(f"{v:>6}" for v in row))
    if avail is not None:
        print(" Avl  " + " ".join(f"{v:>6}" for v in avail))


def cek_safe(tasks, alloc, need, avail, verbose=True):
    """Kembalikan (aman, urutan_aman)."""
    work = list(avail)
    finish = [False] * len(tasks)
    urutan = []
    langkah = 0
    while len(urutan) < len(tasks):
        ketemu = False
        for i, t in enumerate(tasks):
            if not finish[i] and all(n <= w for n, w in zip(need[i], work)):
                langkah += 1
                if verbose:
                    print(f"Langkah {langkah}: {t}  Need={need[i]} <= Work={work}"
                          f"  -> selesai, Work baru = {[w + a for w, a in zip(work, alloc[i])]}")
                work = [w + a for w, a in zip(work, alloc[i])]
                finish[i] = True
                urutan.append(t)
                ketemu = True
        if not ketemu:
            break
    aman = all(finish)
    if verbose and not aman:
        macet = [t for t, f in zip(tasks, finish) if not f]
        print(f"Tidak ada task yang Need-nya <= Work={work}. Task macet: {macet}")
    return aman, urutan


def uji_request(d, tugas, req):
    tasks, alloc, mx, avail = d["tasks"], d["allocation"], d["max"], d["available"]
    need = hitung_need(mx, alloc)
    i = tasks.index(tugas)
    print(f"\n=== Uji permintaan {tugas} meminta {req} ===")
    if any(r > n for r, n in zip(req, need[i])):
        print(f"DITOLAK: Request {req} melebihi Need {tugas} = {need[i]}"); return False
    if any(r > a for r, a in zip(req, avail)):
        print(f"DITUNDA: Request {req} > Available {avail}; {tugas} harus menunggu"); return False
    a2 = [a - r for a, r in zip(avail, req)]
    al2 = [row[:] for row in alloc]; al2[i] = [x + r for x, r in zip(al2[i], req)]
    nd2 = [row[:] for row in need];  nd2[i] = [x - r for x, r in zip(nd2[i], req)]
    print(f"Pura-pura dialokasikan -> Available={a2}, Allocation[{tugas}]={al2[i]}, Need[{tugas}]={nd2[i]}")
    aman, urut = cek_safe(tasks, al2, nd2, a2)
    if aman:
        print(f"DISETUJUI: state tetap aman, urutan aman: <{', '.join(urut)}>")
    else:
        print("DITOLAK: state hasil alokasi TIDAK aman (berisiko deadlock), permintaan ditunda")
    return aman


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="matriks.json")
    ap.add_argument("--request", nargs="+", metavar=("TASK", "R"))
    a = ap.parse_args()
    d = muat(a.data)
    tasks, res = d["tasks"], d["resources"]
    alloc, mx, avail = d["allocation"], d["max"], d["available"]

    total = [sum(col) + av for col, av in zip(zip(*alloc), avail)]
    if "total" in d and d["total"] != total:
        print(f"PERINGATAN: total di berkas {d['total']} != sum(Allocation)+Available {total}")
    print("=== ALGORITMA BANKER - Kasus Smart Farming ===")
    print("Sumber daya:", ", ".join(f"{r}={t}" for r, t in zip(res, total)))
    cetak_matriks("Allocation", tasks, res, alloc)
    cetak_matriks("Max", tasks, res, mx)
    need = hitung_need(mx, alloc)
    cetak_matriks("Need = Max - Allocation", tasks, res, need, avail)
    if any(v < 0 for r in need for v in r):
        sys.exit("ERROR: ada Need negatif (Allocation > Max). Periksa data.")

    print("\n=== Pengecekan safe state ===")
    aman, urut = cek_safe(tasks, alloc, need, avail)
    print("\nHASIL:", "State AMAN, urutan aman <" + ", ".join(urut) + ">" if aman
          else "State TIDAK AMAN (berpotensi deadlock)")

    if a.request:
        uji_request(d, a.request[0], [int(x) for x in a.request[1:]])


if __name__ == "__main__":
    main()
