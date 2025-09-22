// Funciones JavaScript para el Dashboard
function verificarTodos() {
    Swal.fire({
        title: '¿Verificar todos los ISPs?',
        text: 'Se verificarán todos los ISPs conectados',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, verificar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'Verificando todos los ISPs...',
                text: 'Conectando con todos los servidores GenieACS',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            // Simular verificación (en una implementación real, harías una petición AJAX)
            setTimeout(() => {
                Swal.fire({
                    icon: 'success',
                    title: '¡Verificación completada!',
                    text: 'Todos los ISPs han sido verificados',
                    timer: 2000,
                    showConfirmButton: false
                }).then(() => {
                    location.reload();
                });
            }, 3000);
        }
    });
}

function verificarISP(ispId) {
    Swal.fire({
        title: 'Verificando ISP...',
        text: 'Conectando con GenieACS',
        allowOutsideClick: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    fetch(`/verificar_dispositivos/${ispId}`)
        .then(response => response.json())
        .then(data => {
            Swal.fire({
                icon: 'success',
                title: '¡Verificado!',
                text: `Dispositivos actualizados: ${data.dispositivos_actuales}`,
                timer: 2000,
                showConfirmButton: false
            }).then(() => {
                location.reload();
            });
        })
        .catch(error => {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'Error al verificar el ISP'
            });
        });
}

function reenviarAlerta(alertaId, ispNombre) {
    Swal.fire({
        title: '¿Reenviar alerta?',
        text: `Se reenviará la alerta a ${ispNombre}`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, reenviar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'Reenviando alerta...',
                text: 'Por favor espera',
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            fetch(`/reenviar_alerta/${alertaId}`)
                .then(response => response.json())
                .then(data => {
                    Swal.close();
                    if (data.success) {
                        Swal.fire({
                            icon: 'success',
                            title: 'Alerta reenviada',
                            text: data.message
                        }).then(() => {
                            location.reload();
                        });
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: data.message
                        });
                    }
                })
                .catch(error => {
                    Swal.close();
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error de conexión'
                    });
                });
        }
    });
}
