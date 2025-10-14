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
  `contrasena` VARCHAR(255) NOT NULL, -- Más largo para almacenar hashes
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

-- INSERTAR DATOS INICIALES (para pruebas)
INSERT INTO Roles (nombre_rol) VALUES ('Administrador'), ('Cajero'), ('Mesero');

-- Insertar un usuario administrador de prueba (contraseña 'admin123' hashada)
-- La contraseña 'admin123' hasheada con bcrypt (simulación):
-- Para generar un hash real en Python:
-- from werkzeug.security import generate_password_hash
-- generate_password_hash('admin123')
-- EJEMPLO DE HASH (DEBES GENERAR EL TUYO):
-- $2b$12$f0h2N4C3v4J5k6L7m8O9P.q2w3e4r5t6y7u8i9o0a1s2d3f4g5h6j7k8l9z0x1c2v3b4n5m6
INSERT INTO Usuarios (nombre_usuario, contrasena, nombre_completo, id_rol)
VALUES ('admin', 'pbkdf2:sha256:1000000$7o8pzoGfJpdEWTpd$d8f5e9e48fa8ae1163ff2a4b48eabdc3261f01a5a7f1d8cf65b8fdc8722197b2', 'Administrador Principal', 1); -- Reemplaza el hash

