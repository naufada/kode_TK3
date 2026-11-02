#!/usr/bin/env python3
"""deadlock_demo.py - Demo deadlock nyata dengan thread + pencegahannya.
  python3 deadlock_demo.py macet   # urutan kunci berbeda -> deadlock (terdeteksi lewat timeout)
  python3 deadlock_demo.py aman    # urutan kunci seragam (mencegah circular wait) -> selesai
"""
import sys, threading, time

kunci = {"pompa": threading.Lock(), "katup": threading.Lock(), "i2c": threading.Lock()}
URUTAN_GLOBAL = ["pompa", "katup", "i2c"]      # hierarki sumber daya (aturan pencegahan)
hasil = {}
gerbang = threading.Barrier(2)                  # agar kedua task sama-sama "macet" sebelum melepas kunci


def tugas(nama, butuh, urut_seragam):
    pertama, kedua = sorted(butuh, key=URUTAN_GLOBAL.index) if urut_seragam else butuh
    kunci[pertama].acquire()
    print(f"[{nama}] memperoleh {pertama}", flush=True)
    time.sleep(0.5)                              # beri kesempatan task lain berinterleaving
    print(f"[{nama}] memegang {pertama}, meminta {kedua} ...", flush=True)
    if kunci[kedua].acquire(timeout=2):
        print(f"[{nama}] memperoleh {kedua} -> bekerja -> selesai", flush=True)
        hasil[nama] = "selesai"
        kunci[kedua].release()
    else:
        print(f"[{nama}] TIMEOUT 2 detik menunggu {kedua} -> indikasi DEADLOCK", flush=True)
        hasil[nama] = "macet"
        try:
            gerbang.wait(timeout=5)
        except threading.BrokenBarrierError:
            pass
    kunci[pertama].release()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "macet"
    seragam = mode == "aman"
    print(f"=== Mode: {mode} ({'urutan kunci seragam pompa<katup<i2c' if seragam else 'urutan kunci berbeda tiap task'}) ===")
    t1 = threading.Thread(target=tugas, args=("T1-Pompa", ["pompa", "katup"], seragam))
    t2 = threading.Thread(target=tugas, args=("T2-Katup", ["katup", "pompa"], seragam))
    t1.start(); t2.start(); t1.join(); t2.join()
    print("Hasil:", hasil)
    print("KESIMPULAN:", "DEADLOCK terjadi" if "macet" in hasil.values() else "Tidak ada deadlock")


if __name__ == "__main__":
    main()
