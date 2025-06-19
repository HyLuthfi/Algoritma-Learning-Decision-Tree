import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
import math, random

data = pd.read_csv("C:\\Users\\Lenovo\\Downloads\\Train.csv")
data = data.drop(columns=["ID", "Customer_rating"])

kolom_label = ['Warehouse_block', 'Mode_of_Shipment', 'Product_importance', 'Gender']
pemetaan_label = {}
for kolom in kolom_label:
    nilai_unik = data[kolom].unique()
    pemetaan_label[kolom] = {v: i for i, v in enumerate(nilai_unik)}
    data[kolom] = data[kolom].map(pemetaan_label[kolom])

fitur = list(data.columns[:-1])
data_fitur = data[fitur].values.tolist()
data_target = data["Reached.on.Time_Y.N"].tolist()
data_gabungan = [x + [y] for x, y in zip(data_fitur, data_target)]

def bagi_data(data, rasio_uji=0.2, acak_seed=42):
    random.seed(acak_seed)
    data_acak = data[:]
    random.shuffle(data_acak)
    titik_bagi = int(len(data_acak) * (1 - rasio_uji))
    return data_acak[:titik_bagi], data_acak[titik_bagi:]

data_latih, data_uji = bagi_data(data_gabungan)

def entropi(baris):
    total = len(baris)
    jumlah_kelas = Counter(r[-1] for r in baris)
    return -sum((jumlah / total) * math.log2(jumlah / total) for jumlah in jumlah_kelas.values() if jumlah)

def bagi(baris, kolom, nilai):
    if isinstance(nilai, (int, float)):
        kiri = [r for r in baris if r[kolom] <= nilai]
        kanan = [r for r in baris if r[kolom] > nilai]
    else:
        kiri = [r for r in baris if r[kolom] == nilai]
        kanan = [r for r in baris if r[kolom] != nilai]
    return kiri, kanan

def keuntungan_info(baris, kolom, nilai):
    kiri, kanan = bagi(baris, kolom, nilai)
    if not kiri or not kanan:
        return 0
    proporsi = len(kiri) / len(baris)
    return entropi(baris) - (proporsi * entropi(kiri) + (1 - proporsi) * entropi(kanan))

def cari_pemisah_terbaik(baris):
    terbaik_gain = 0
    kolom_terbaik = None
    nilai_terbaik = None
    for k in range(len(baris[0]) - 1):
        nilai_unik = set(r[k] for r in baris)
        for v in nilai_unik:
            gain = keuntungan_info(baris, k, v)
            if gain > terbaik_gain:
                terbaik_gain, kolom_terbaik, nilai_terbaik = gain, k, v
    return terbaik_gain, kolom_terbaik, nilai_terbaik

def bangun_pohon(baris, kedalaman=0, maks_kedalaman=10, min_split=5):
    label = [r[-1] for r in baris]
    if label.count(label[0]) == len(label):
        return label[0]
    if len(baris) < min_split or kedalaman >= maks_kedalaman:
        return Counter(label).most_common(1)[0][0]
    gain, kolom, nilai = cari_pemisah_terbaik(baris)
    if gain == 0:
        return Counter(label).most_common(1)[0][0]
    kiri, kanan = bagi(baris, kolom, nilai)
    return {
        'kolom': kolom,
        'nilai': nilai,
        'kiri': bangun_pohon(kiri, kedalaman + 1, maks_kedalaman, min_split),
        'kanan': bangun_pohon(kanan, kedalaman + 1, maks_kedalaman, min_split)
    }

def prediksi(baris, simpul):
    if not isinstance(simpul, dict):
        return simpul
    nilai = baris[simpul['kolom']]
    arah = simpul['kiri'] if nilai <= simpul['nilai'] else simpul['kanan']
    return prediksi(baris, arah)

def evaluasi(data_uji, pohon):
    aktual = [r[-1] for r in data_uji]
    prediksi_ = [prediksi(r, pohon) for r in data_uji]
    tp = sum((a == 1 and p == 1) for a, p in zip(aktual, prediksi_))
    tn = sum((a == 0 and p == 0) for a, p in zip(aktual, prediksi_))
    fp = sum((a == 0 and p == 1) for a, p in zip(aktual, prediksi_))
    fn = sum((a == 1 and p == 0) for a, p in zip(aktual, prediksi_))
    akurasi = (tp + tn) / len(aktual)
    presisi = tp / (tp + fp + 1e-10)
    recall = tp / (tp + fn + 1e-10)
    f1 = 2 * presisi * recall / (presisi + recall + 1e-10)
    return akurasi, presisi, recall, f1

def cetak_pohon(simpul, nama_fitur, spasi=""):
    if not isinstance(simpul, dict):
        print(spasi + "Prediksi:", "Terlambat" if simpul == 1 else "Tepat Waktu")
        return
    nama_kolom = nama_fitur[simpul['kolom']]
    nilai = simpul['nilai']
    print(spasi + f"[{nama_kolom} <= {nilai}]")
    print(spasi + "--> Ya:")
    cetak_pohon(simpul['kiri'], nama_fitur, spasi + "    ")
    print(spasi + "--> Tidak:")
    cetak_pohon(simpul['kanan'], nama_fitur, spasi + "    ")

pohon_keputusan = bangun_pohon(data_latih)
akurasi, presisi, recall, f1 = evaluasi(data_uji, pohon_keputusan)
hasil_akhir = f"""Akurasi: {round(akurasi * 100, 2)}%
Presisi: {round(presisi, 2)}
Recall: {round(recall, 2)}
F1-Score: {round(f1, 2)}"""

jendela = tk.Tk()
jendela.title("Prediksi Keterlambatan Paket (Pohon Keputusan Manual)")
jendela.geometry("550x520")
jendela.configure(bg="#f4f4f4")

ttk.Label(jendela, text=" Prediksi Keterlambatan Paket", font=("Segoe UI", 16, "bold")).pack(pady=10)
tk.Label(jendela, text=hasil_akhir, font=("Consolas", 10), bg="#f4f4f4").pack()

frame = ttk.Frame(jendela, padding=10)
frame.pack()

input_pengguna = {
    "Warehouse_block": tk.StringVar(),
    "Mode_of_Shipment": tk.StringVar(),
    "Gender": tk.StringVar(),
    "Customer_care_calls": tk.IntVar(),
    "Cost_of_the_Product": tk.IntVar(),
    "Prior_purchases": tk.IntVar(),
    "Product_importance": tk.StringVar(),
    "Discount_offered": tk.IntVar(),
    "Weight_in_gms": tk.IntVar()
}

default_combo = {
    "Warehouse_block": list(pemetaan_label['Warehouse_block'].keys()),
    "Mode_of_Shipment": list(pemetaan_label['Mode_of_Shipment'].keys()),
    "Gender": list(pemetaan_label['Gender'].keys()),
    "Product_importance": list(pemetaan_label['Product_importance'].keys())
}

for i, kunci in enumerate(input_pengguna):
    ttk.Label(frame, text=kunci.replace("_", " ")).grid(row=i, column=0, padx=5, pady=4, sticky="w")
    if kunci in default_combo:
        cb = ttk.Combobox(frame, textvariable=input_pengguna[kunci], values=default_combo[kunci], width=25)
        cb.grid(row=i, column=1, padx=5)
        cb.current(0)
    else:
        ttk.Entry(frame, textvariable=input_pengguna[kunci], width=27).grid(row=i, column=1, padx=5)

def tombol_prediksi():
    try:
        baris = []
        for kunci in input_pengguna:
            nilai = input_pengguna[kunci].get()
            if kunci in kolom_label:
                nilai = pemetaan_label[kunci][nilai]
            else:
                nilai = int(nilai)
            baris.append(nilai)
        hasil = prediksi(baris, pohon_keputusan)
        pesan = "Tepat Waktu" if hasil == 0 else "Terlambat"
        messagebox.showinfo("Hasil Prediksi", f"Hasil Prediksi: {pesan}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def tampilkan_struktur():
    print("\n=== Struktur Pohon Keputusan ===")
    cetak_pohon(pohon_keputusan, fitur)

ttk.Button(jendela, text="Prediksi", command=tombol_prediksi).pack(pady=10)
ttk.Button(jendela, text="Lihat Struktur Pohon", command=tampilkan_struktur).pack(pady=0)

jendela.mainloop()
