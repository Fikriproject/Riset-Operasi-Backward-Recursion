# 📉 Backward Recursion Optimization - Riset Operasi

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

## 📖 Deskripsi

Proyek ini merupakan implementasi algoritma **Backward Recursion** (Rekursi Mundur) untuk menyelesaikan permasalahan optimasi bertahap (*Multi-Stage Optimization Problem*) dalam mata kuliah Riset Operasi.

Sistem ini dirancang untuk mencari **rute dengan biaya minimum** dari titik awal hingga tujuan dengan menggunakan pendekatan **Dynamic Programming** dan **Persamaan Bellman**. Program bekerja dengan cara menghitung biaya dari tahap terakhir (*backward*) menuju tahap awal untuk menentukan keputusan optimal di setiap langkah, kemudian melakukan *Forward Tracing* untuk merekonstruksi jalur terbaik.

**Fitur Utama:**
* 🚀 **Dynamic Programming:** Menggunakan teknik memoization untuk efisiensi komputasi.
* Distance Calculation:** Mendukung perhitungan jarak geografis menggunakan rumus **Haversine**.
* 📊 **Data-Driven:** Input data fleksibel berbasis CSV (Node, Koordinat, Biaya).
* 🔍 **Traceability:** Menyediakan jejak audit keputusan per-stage.
* 📈 **Visualization:** (Opsional) Visualisasi graf rute menggunakan `networkx`.

---

## 👥 Team Members

Berikut adalah kontributor yang mengembangkan proyek ini:

| NPM | Nama Anggota | Role |
| :--- | :--- | :--- |
| **220511113** | **MUHAMMAD ILHAM RAMDHANI** | *Project Manager & Analyst* |
| **220511146** | **MUCHAMAD FIKRI ALI** | *Lead Programmer (Algorithm)* |
| **220511040** | **LUGAS NUSA BAKTI** | *Data Engineer & Documentation* |

---

## ⚙️ Installation

Pastikan sistem Anda telah memenuhi persyaratan berikut sebelum menjalankan program.

### Prerequisites
* **Python 3.8** atau lebih baru.
* **pip** (Python Package Installer).

### Setup

1.  Clone repositori ini:
    ```bash
    git clone https://github.com/Fikriproject/Riset-Operasi-Backward-Recursion.git
    cd Riset-Operasi-Backward-Recursion
    ```

2.  Buat virtual environment (Disarankan):
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  Install dependensi yang dibutuhkan:
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Usage

### Menjalankan Algoritma
Untuk menjalankan program :

```bash
streamlit run app.py