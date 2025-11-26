-- init.sql
-- Usar la base de datos bars_db
USE bars_db;

-- -----------------------------------------------------
-- Table `bars_db`.`Roles`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Roles` (
  `id_rol` INT NOT NULL AUTO_INCREMENT,
  `nombre_rol` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_rol`),
  UNIQUE INDEX `nombre_rol_UNIQUE` (`nombre_rol` ASC));

-- -----------------------------------------------------
-- Table `bars_db`.`Sedes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Sedes` (
  `id_sede` INT NOT NULL AUTO_INCREMENT,
  `nombre_sede` VARCHAR(45) NOT NULL UNIQUE,
  PRIMARY KEY (`id_sede`));

-- -----------------------------------------------------
-- Table `bars_db`.`Usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Usuarios` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nombre_usuario` VARCHAR(45) NOT NULL,
  `contrasena` VARCHAR(255) NOT NULL,
  `nombre_completo` VARCHAR(45) NOT NULL,
  `id_rol` INT NOT NULL,
  `id_sede` INT NULL,
  `pregunta_seguridad` VARCHAR(150) NULL,
  `respuesta_seguridad` VARCHAR(255) NULL,
  -- -----------------------------------------
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `nombre_usuario_UNIQUE` (`nombre_usuario` ASC),
  INDEX `fk_Usuarios_Roles_idx` (`id_rol` ASC),
  INDEX `fk_Usuarios_Sedes1_idx` (`id_sede` ASC),
  CONSTRAINT `fk_Usuarios_Roles`
    FOREIGN KEY (`id_rol`)
    REFERENCES `bars_db`.`Roles` (`id_rol`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Usuarios_Sedes1`
    FOREIGN KEY (`id_sede`)
    REFERENCES `bars_db`.`Sedes` (`id_sede`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
    
-- -----------------------------------------------------
-- Table `bars_db`.`Mesas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Mesas` (
  `id_mesa` INT NOT NULL AUTO_INCREMENT,
  `estado` VARCHAR(45) NOT NULL DEFAULT 'libre',
  `id_sede` INT NOT NULL,
  PRIMARY KEY (`id_mesa`),
  INDEX `fk_Mesas_Sedes1_idx` (`id_sede` ASC),
  CONSTRAINT `fk_Mesas_Sedes1`
    FOREIGN KEY (`id_sede`)
    REFERENCES `bars_db`.`Sedes` (`id_sede`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `bars_db`.`Categorias_Producto`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Categorias_Producto` (
  `id_categoria` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(45) NOT NULL,
  `descripcion` VARCHAR(100) NULL,
  PRIMARY KEY (`id_categoria`),
  UNIQUE INDEX `nombre_UNIQUE` (`nombre` ASC));


-- -----------------------------------------------------
-- Table `bars_db`.`Productos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Productos` (
  `id_producto` INT NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(45) NULL UNIQUE,
  `nombre` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(100) NULL,
  `costo_compra` DECIMAL(10,2) NOT NULL,
  `precio_venta` DECIMAL(10,2) NOT NULL,
  `id_categoria` INT NOT NULL,
  PRIMARY KEY (`id_producto`),
  INDEX `fk_Productos_Categorias_Producto1_idx` (`id_categoria` ASC),
  CONSTRAINT `fk_Productos_Categorias_Producto1`
    FOREIGN KEY (`id_categoria`)
    REFERENCES `bars_db`.`Categorias_Producto` (`id_categoria`)
    ON DELETE RESTRICT
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `bars_db`.`Inventario`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Inventario` (
  `id_inventario` INT NOT NULL AUTO_INCREMENT,
  `cantidad` INT NOT NULL DEFAULT 0,
  `esta_bloqueado` TINYINT(1) NOT NULL DEFAULT 0,
  `id_producto` INT NOT NULL,
  `id_sede` INT NOT NULL,
  PRIMARY KEY (`id_inventario`),
  UNIQUE INDEX `_producto_sede_uc` (`id_producto` ASC, `id_sede` ASC),
  INDEX `fk_Inventario_Productos1_idx` (`id_producto` ASC),
  INDEX `fk_Inventario_Sedes1_idx` (`id_sede` ASC),
  CONSTRAINT `fk_Inventario_Productos1`
    FOREIGN KEY (`id_producto`)
    REFERENCES `bars_db`.`Productos` (`id_producto`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Inventario_Sedes1`
    FOREIGN KEY (`id_sede`)
    REFERENCES `bars_db`.`Sedes` (`id_sede`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `bars_db`.`Pedidos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Pedidos` (
  `id_pedido` INT NOT NULL AUTO_INCREMENT,
  `estado` VARCHAR(20) NOT NULL DEFAULT 'pendiente',
  `total_pedido` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `fecha_creacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `id_usuario_mesero` INT NOT NULL,
  `id_mesa` INT NOT NULL,
  PRIMARY KEY (`id_pedido`),
  INDEX `fk_Pedidos_Usuarios1_idx` (`id_usuario_mesero` ASC),
  INDEX `fk_Pedidos_Mesas1_idx` (`id_mesa` ASC),
  CONSTRAINT `fk_Pedidos_Usuarios1`
    FOREIGN KEY (`id_usuario_mesero`)
    REFERENCES `bars_db`.`Usuarios` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Pedidos_Mesas1`
    FOREIGN KEY (`id_mesa`)
    REFERENCES `bars_db`.`Mesas` (`id_mesa`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `bars_db`.`Detalle_Pedido`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Detalle_Pedido` (
  `id_detalle_pedido` INT NOT NULL AUTO_INCREMENT,
  `cantidad` INT NOT NULL,
  `precio_unitario` DECIMAL(10,2) NOT NULL,
  `costo_unitario` DECIMAL(10,2) NOT NULL,
  `subtotal` DECIMAL(10,2) NOT NULL,
  `id_pedido` INT NOT NULL,
  `id_producto` INT NOT NULL,
  PRIMARY KEY (`id_detalle_pedido`),
  INDEX `fk_Detalle_Pedido_Pedidos1_idx` (`id_pedido` ASC),
  INDEX `fk_Detalle_Pedido_Productos1_idx` (`id_producto` ASC),
  CONSTRAINT `fk_Detalle_Pedido_Pedidos1`
    FOREIGN KEY (`id_pedido`)
    REFERENCES `bars_db`.`Pedidos` (`id_pedido`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Detalle_Pedido_Productos1`
    FOREIGN KEY (`id_producto`)
    REFERENCES `bars_db`.`Productos` (`id_producto`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `bars_db`.`Pagos`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Pagos` (
  `id_pago` INT NOT NULL AUTO_INCREMENT,
  `monto_pago` DECIMAL(10,2) NOT NULL,
  `metodo_pago` VARCHAR(45) NOT NULL,
  `fecha_hora_pago` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  `id_pedido` INT NOT NULL,
  `id_usuario_cajero` INT NOT NULL,
  PRIMARY KEY (`id_pago`),
  INDEX `fk_Pagos_Pedidos1_idx` (`id_pedido` ASC),
  INDEX `fk_Pagos_Usuarios1_idx` (`id_usuario_cajero` ASC),
  CONSTRAINT `fk_Pagos_Pedidos1`
    FOREIGN KEY (`id_pedido`)
    REFERENCES `bars_db`.`Pedidos` (`id_pedido`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_Pagos_Usuarios1`
    FOREIGN KEY (`id_usuario_cajero`)
    REFERENCES `bars_db`.`Usuarios` (`id_usuario`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);
    
-- INSERTAR DATOS INICIALES
INSERT INTO Roles (nombre_rol) VALUES ('Administrador'), ('Cajero'), ('Mesero');
INSERT INTO Sedes (nombre_sede) VALUES ('Parkway'), ('85'), ('Restrepo');

-- Insertar ADMIN con pregunta de seguridad
-- Contraseña: 'admin123'
-- Respuesta Seguridad: 'bars' (hasheada)
INSERT INTO Usuarios (nombre_usuario, contrasena, nombre_completo, id_rol, pregunta_seguridad, respuesta_seguridad)
VALUES (
    'admin', 
    'pbkdf2:sha256:1000000$7o8pzoGfJpdEWTpd$d8f5e9e48fa8ae1163ff2a4b48eabdc3261f01a5a7f1d8cf65b8fdc8722197b2', 
    'Administrador Principal', 
    1, 
    '¿Cual es el nombre del proyecto?', 
    'pbkdf2:sha256:600000$D5v8x2W1$a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1'
);