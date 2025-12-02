// Función para abrir el modal y setear los datos
function openEnrollModal(userId, username) {
    const modal = document.getElementById('enrollModal');
    const inputId = document.getElementById('modalUserId');
    const title = document.getElementById('modalTitle');

    // Asignamos el ID del usuario al input oculto
    inputId.value = userId;

    // (Opcional) Ponemos el nombre en el título para que se vea pro
    title.innerText = `Inscribir a ${username} en un curso`;

    // Mostramos el modal
    modal.style.display = 'flex';
}

// Función para cerrar el modal
function closeEnrollModal() {
    const modal = document.getElementById('enrollModal');
    modal.style.display = 'none';
}

function openCreateTeamModal() {
    document.getElementById('createTeamModal').style.display = 'flex';
}

function closeCreateTeamModal() {
    document.getElementById('createTeamModal').style.display = 'none';
}

function openEditTeamModal(button) {
    const id = button.dataset.teamId;
    const name = button.dataset.teamName;
    const description = button.dataset.teamDesc;
    const supervisorId = button.dataset.teamSup;
    const url = button.dataset.url;

    document.getElementById('editTeamModal').style.display = 'flex';
    document.getElementById('editTeamName').value = name;
    document.getElementById('editTeamDescription').value = description;
    document.getElementById('editTeamSupervisor').value = supervisorId;
    document.getElementById('editTeamForm').action = url;
}

function closeEditTeamModal() {
    document.getElementById('editTeamModal').style.display = 'none';
}

function openManageMembersModal(button) {
    const teamId = button.dataset.teamId;
    const teamName = button.dataset.teamName;
    const url = button.dataset.url;

    document.getElementById('manageMembersModal').style.display = 'flex';
    document.getElementById('manageMembersTitle').innerText = 'Miembros de ' + teamName;
    document.getElementById('addMemberForm').action = url;

    // Populate members list
    var content = document.getElementById('team-members-' + teamId).innerHTML;
    document.getElementById('membersListContainer').innerHTML = content;
}

function closeManageMembersModal() {
    document.getElementById('manageMembersModal').style.display = 'none';
}

// Cerrar si se hace clic fuera de la cajita blanca
window.onclick = function (event) {
    const enrollModal = document.getElementById('enrollModal');
    const createTeamModal = document.getElementById('createTeamModal');
    const editTeamModal = document.getElementById('editTeamModal');
    const manageMembersModal = document.getElementById('manageMembersModal');

    if (event.target == enrollModal) {
        enrollModal.style.display = 'none';
    }
    if (event.target == createTeamModal) {
        createTeamModal.style.display = 'none';
    }
    if (event.target == editTeamModal) {
        editTeamModal.style.display = 'none';
    }
    if (event.target == manageMembersModal) {
        manageMembersModal.style.display = 'none';
    }
}
