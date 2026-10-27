// ==========================================================================
// SIMRS INTERACTIVE JAVASCRIPT
// ==========================================================================

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
  }

  // 2. Auto Dismiss Flash Alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {}
    }, 5000);
  });

  // 3. Dropdown Dinamis: Load Dokter Berdasarkan Poli
  const poliSelect = document.getElementById('select-poli');
  const dokterSelect = document.getElementById('select-dokter');
  if (poliSelect && dokterSelect) {
    poliSelect.addEventListener('change', function () {
      const poliId = this.value;
      dokterSelect.innerHTML = '<option value="">-- Memuat Dokter... --</option>';
      dokterSelect.disabled = true;

      if (!poliId) {
        dokterSelect.innerHTML = '<option value="">-- Pilih Poliklinik Terlebih Dahulu --</option>';
        return;
      }

      fetch(`/dokter/api/by-poli/${poliId}`)
        .then(response => response.json())
        .then(data => {
          dokterSelect.innerHTML = '<option value="">-- Pilih Dokter --</option>';
          if (data.length === 0) {
            dokterSelect.innerHTML = '<option value="">(Tidak ada dokter aktif di poli ini)</option>';
          } else {
            data.forEach(doc => {
              const opt = document.createElement('option');
              opt.value = doc.id;
              opt.textContent = `${doc.nama_dokter} (${doc.spesialisasi})`;
              dokterSelect.appendChild(opt);
            });
            dokterSelect.disabled = false;
          }
        })
        .catch(err => {
          console.error('Gagal mengambil data dokter:', err);
          dokterSelect.innerHTML = '<option value="">Gagal memuat daftar dokter</option>';
        });
    });
  }

  // 4. Auto format input angka / rupiah
  const rupiahInputs = document.querySelectorAll('.input-rupiah');
  rupiahInputs.forEach(input => {
    input.addEventListener('input', function (e) {
      let val = this.value.replace(/\D/g, '');
      if (val) {
        this.value = parseInt(val, 10).toLocaleString('id-ID');
      }
    });
  });
});

// Helper Fungsi Modal Konfirmasi Hapus Data
function konfirmasiHapus(formId, namaItem) {
  const modalElem = document.getElementById('modalKonfirmasiHapus');
  const itemElem = document.getElementById('hapusItemNama');
  const btnSubmit = document.getElementById('btnSubmitHapus');

  if (itemElem) itemElem.textContent = namaItem;
  if (btnSubmit) {
    btnSubmit.onclick = function () {
      document.getElementById(formId).submit();
    };
  }

  if (modalElem) {
    const modal = new bootstrap.Modal(modalElem);
    modal.show();
  } else {
    if (confirm(`Apakah Anda yakin ingin menghapus data "${namaItem}"? Tindakan ini tidak dapat dibatalkan.`)) {
      document.getElementById(formId).submit();
    }
  }
}
