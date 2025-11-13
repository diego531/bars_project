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
-- Table `bars_db`.`Usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Usuarios` (
  `id_usuario` INT NOT NULL AUTO_INCREMENT,
  `nombre_usuario` VARCHAR(45) NOT NULL,
  `contrasena` VARCHAR(255) NOT NULL, 
  `nombre_completo` VARCHAR(45) NOT NULL,
  `id_rol` INT NOT NULL,
  PRIMARY KEY (`id_usuario`),
  UNIQUE INDEX `nombre_usuario_UNIQUE` (`nombre_usuario` ASC),
  INDEX `fk_Usuarios_Roles_idx` (`id_rol` ASC),
  CONSTRAINT `fk_Usuarios_Roles`
    FOREIGN KEY (`id_rol`)
    REFERENCES `bars_db`.`Roles` (`id_rol`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION);

-- -----------------------------------------------------
-- Table `bars_db`.`Sedes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Sedes` (
  `id_sede` INT NOT NULL AUTO_INCREMENT,
  `nombre_sede` VARCHAR(45) NOT NULL UNIQUE, -- Añadido NOT NULL UNIQUE
  PRIMARY KEY (`id_sede`));

-- -----------------------------------------------------
-- Table `bars_db`.`Mesas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `bars_db`.`Mesas` (
  `id_mesa` INT NOT NULL AUTO_INCREMENT,
  `estado` VARCHAR(45) NOT NULL DEFAULT 'libre', -- Añadido NOT NULL y DEFAULT 'libre'
  `id_sede` INT NOT NULL,
  PRIMARY KEY (`id_mesa`),
  INDEX `fk_Mesas_Sedes1_idx` (`id_sede` ASC),
  CONSTRAINT `fk_Mesas_Sedes1`
    FOREIGN KEY (`id_sede`)
    REFERENCES `bars_db`.`Sedes` (`id_sede`)
    ON DELETE CASCADE -- Cambiado a CASCADE para que al eliminar una sede, sus mesas se eliminen
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
  `codigo` VARCHAR(45) NULL UNIQUE, -- Añadido UNIQUE para el código
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
    ON DELETE RESTRICT -- Cambiado a RESTRICT para evitar eliminar categorías con productos
    ON UPDATE NO ACTION);

-- INSERTAR DATOS INICIALES (para pruebas)
INSERT INTO Roles (nombre_rol) VALUES ('Administrador'), ('Cajero'), ('Mesero');

-- Insertar un usuario administrador de prueba (contraseña 'admin123' hashada)
-- La contraseña 'admin123' hasheada con bcrypt (simulación):
-- Para generar un hash real en Python:
-- from werkzeug.security import generate_password_hash
-- generate_password_hash('admin123')
INSERT INTO Usuarios (nombre_usuario, contrasena, nombre_completo, id_rol)
VALUES ('admin', 'pbkdf2:sha256:1000000$7o8pzoGfJpdEWTpd$d8f5e9e48fa8ae1163ff2a4b48eabdc3261f01a5a7f1d8cf65b8fdc8722197b2', 'Administrador Principal', 1); 

