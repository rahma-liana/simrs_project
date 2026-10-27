document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('sidebar-open'));
  const passwordToggle = document.getElementById('togglePassword');
  const password = document.getElementById('password');
  if (passwordToggle && password) passwordToggle.addEventListener('click', () => {
    const hidden = password.type === 'password';
    password.type = hidden ? 'text' : 'password';
    passwordToggle.innerHTML = hidden ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
  });
  const editModal = document.getElementById('editPasien');
  if (editModal) editModal.addEventListener('show.bs.modal', function (event) {
    const button = event.relatedTarget;
    if (!button) return;
    const id = button.getAttribute('data-id');
    document.getElementById('editPasienForm').action = `/pasien/${id}/edit`;
    document.getElementById('editNama').value = button.getAttribute('data-nama') || '';
    document.getElementById('editTanggal').value = button.getAttribute('data-tanggal') || '';
    document.getElementById('editJK').value = button.getAttribute('data-jk') || 'Laki-laki';
    document.getElementById('editTelepon').value = button.getAttribute('data-telepon') || '';
    document.getElementById('editAlamat').value = button.getAttribute('data-alamat') || '';
  });
});
