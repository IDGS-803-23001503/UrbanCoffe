Drop Database if Exists Urban_Coffee;

Create Database Urban_Coffee;
use Urban_Coffee;

Create table Rol(
id_rol int auto_increment not null,
nombre varchar(20) unique,
constraint pk_rol primary key (id_rol)
);

Create table Usuario(
id_usuario int auto_increment not null,
id_rol int not null,
nombre varchar(50) not null,
ap_paterno varchar(50),
ap_materno varchar(50), 
telefono varchar(15) not null,
correo varchar(50) not null unique,
contrasena varchar(255) not null,
estatus boolean default true,
constraint pk_id_usuario primary key (id_usuario),
constraint fk_usuario_rol foreign key (id_rol) references Rol(id_rol)
);

Create table Sesion(
token varchar(254) not null,
id_usuario int not null,
fecha_inicio datetime,
fecha_expiracion datetime,
ultimo_acceso datetime,
constraint pk_sesion primary key (token),
constraint fk_sesion_usuario foreign key (id_usuario) references Usuario(id_usuario)
);
 
Create table Proveedor(
id_proveedor int not null auto_increment, 
RFC varchar(13) not null unique,
nombre varchar(100) not null,
correo varchar(50), 
telefono varchar(15),
direccion text,
estatus boolean default true,
constraint pk_proveedor primary key (id_proveedor)
);

Create table Unidad_medida(
id_unidad int auto_increment not null,
nombre varchar(10) not null,
abreviacion varchar(4) unique,
constraint pk_unidad primary key(id_unidad)
);

Create table Materia_prima(
id_materia int not null auto_increment,
nombre varchar(50) not null,
descripcion text, 
unidad_medida int not null, -- duda sobre la tabla 
stock_minimo decimal(10, 2) default 0,
stock_actual decimal(10, 2) default 0,
costo_promedio decimal(10, 2) default 0,
constraint pk_materia primary key (id_materia),
constraint fk_materia_unidad foreign key (unidad_medida) 
references Unidad_medida(id_unidad)
);

Create table Compra(
id_compra int not null auto_increment,
id_proveedor int not null,
fecha datetime not null,
precio_total numeric(10,2) not null,
constraint pk_compra primary key (id_compra),
constraint fk_compra_proveedor foreign key (id_proveedor) references Proveedor(id_proveedor)
);

Create table detalle_compra(
id_detalle_compra int not null auto_increment,
id_compra int not null,
id_materia int not null,
cantidad numeric(10, 2) not null,
unidad int not null,
costo_unitario numeric(10, 2) not null,
subtotal numeric(10,2) not null,
constraint pk_detalle_compra primary key (id_detalle_compra),
constraint fk_detalle_compra_unidad foreign key (unidad) references Unidad_medida(id_unidad),
constraint fk_detalle_compra_compra foreign key (id_compra) references Compra(id_compra),
constraint fk_detalle_compra_materia foreign key (id_materia) references Materia_prima(id_materia)
);

Create table Producto (
id_producto int not null auto_increment,
nombre varchar(50) not null,
categoria varchar(50),
precio_venta numeric(10, 2),
stock int not null default 0,
estatus boolean default true,
constraint pk_producto primary key (id_producto)
);

Create table Recetas(
id_receta int not null auto_increment,
id_producto int not null,
id_materia int not null,
cantidad numeric(10, 2) not null,
constraint pk_receta primary key (id_receta),
constraint fk_recetas_producto foreign key (id_producto) references Producto(id_producto),
constraint fk_recetas_materia foreign key (id_materia) references Materia_prima(id_materia),
unique(id_producto, id_materia)
);

create table Solicitud_produccion(
id_solicitud int not null auto_increment,
id_usuario int not null,
fecha datetime not null,
estado enum('pendiente','en_proceso','finalizado','cancelado'),
constraint pk_solicitud primary key (id_solicitud),
constraint fk_solicitud_usuario foreign key (id_usuario) references Usuario(id_usuario)
);

CREATE TABLE Detalle_produccion(
id_detalle INT AUTO_INCREMENT NOT NULL,
id_solicitud INT NOT NULL,
id_producto INT NOT NULL,
cantidad INT NOT NULL,
constraint pk_detalle_produccion primary key(id_detalle),

constraint fk_detalle_produccion_solicitud 
foreign key (id_solicitud) references Solicitud_produccion(id_solicitud),

constraint fk_detalle_produccion_producto
foreign key (id_producto) references Producto(id_producto)
);

create table Ventas(
id_venta int not null auto_increment,
fecha datetime not null,
id_usuario int not null,
metodo_pago varchar(30) not null,
total decimal(10,2) not null,
constraint pk_ventas primary key (id_venta),
constraint fk_ventas_usuario foreign key(id_usuario) references Usuario(id_usuario)
);

create table Detalle_venta(
id_detalle_venta int auto_increment not null,
id_venta int not null,
id_producto int not null,
cantidad int not null,
subtotal numeric(10,2) not null,
constraint pk_detalle_venta primary key (id_detalle_venta),
constraint fk_detalle_venta_venta foreign key(id_venta) references Ventas(id_venta),
constraint fk_detalle_venta_producto foreign key(id_producto) references Producto(id_producto),
UNIQUE(id_venta, id_producto)
);

create table Merma(
id_merma int not null auto_increment,
id_materia int not null,
cantidad numeric(10,2) not null,
fecha datetime not null,
motivo varchar(200),
id_usuario int,
constraint pk_merma primary key (id_merma),
constraint fk_merma_materia foreign key(id_materia) references Materia_prima(id_materia),
constraint fk_merma_usuario foreign key(id_usuario) references Usuario(id_usuario)
);

-- preguntar sobre creacion de tabla de utilidades