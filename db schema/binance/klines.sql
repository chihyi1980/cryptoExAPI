CREATE TABLE `klines` (
	`trade_time` DATETIME NOT NULL,
	`pair` VARCHAR(50) NOT NULL COLLATE 'utf8mb4_general_ci',
	`intr` VARCHAR(50) NOT NULL COLLATE 'utf8mb4_general_ci',
	`start_price` FLOAT NULL DEFAULT NULL,
	`high_price` FLOAT NULL DEFAULT NULL,
	`low_price` FLOAT NULL DEFAULT NULL,
	`end_price` FLOAT NULL DEFAULT NULL,
	`volume` FLOAT NULL DEFAULT NULL,
	`money` FLOAT NULL DEFAULT NULL,
	`start_price_24h_rate` FLOAT NULL DEFAULT NULL,
	`high_price_24h_rate` FLOAT NULL DEFAULT NULL,
	`low_price_24h_rate` FLOAT NULL DEFAULT NULL,
	`end_price_24h_rate` FLOAT NULL DEFAULT NULL,
	`volume_24h_rate` FLOAT NULL DEFAULT NULL,
	`money_24h_rate` FLOAT NULL DEFAULT NULL,
	`class` VARCHAR(50) NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
	PRIMARY KEY (`trade_time`, `pair`, `intr`) USING BTREE
)
COLLATE='utf8mb4_general_ci'
ENGINE=InnoDB
;
