// Archivo de diagnóstico para el dashboard
console.log('Dashboard JavaScript cargado correctamente');

// Verificar que SweetAlert esté disponible
if (typeof Swal !== 'undefined') {
    console.log('SweetAlert2 cargado correctamente');
} else {
    console.error('SweetAlert2 NO está cargado');
}

// Verificar que las funciones estén definidas
if (typeof verificarTodos === 'function') {
    console.log('Función verificarTodos disponible');
} else {
    console.error('Función verificarTodos NO está disponible');
}

if (typeof verificarISP === 'function') {
    console.log('Función verificarISP disponible');
} else {
    console.error('Función verificarISP NO está disponible');
}

if (typeof reenviarAlerta === 'function') {
    console.log('Función reenviarAlerta disponible');
} else {
    console.error('Función reenviarAlerta NO está disponible');
}

// Verificar que jQuery esté disponible (si se usa)
if (typeof $ !== 'undefined') {
    console.log('jQuery cargado correctamente');
} else {
    console.log('jQuery no está cargado (esto es normal si no se usa)');
}

// Verificar que Bootstrap esté disponible
if (typeof bootstrap !== 'undefined') {
    console.log('Bootstrap cargado correctamente');
} else {
    console.log('Bootstrap no está cargado (esto es normal si no se usa)');
}

console.log('Diagnóstico completado');
