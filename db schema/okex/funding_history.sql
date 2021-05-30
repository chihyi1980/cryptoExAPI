
CREATE TABLE `funding_history` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT,
	`time` DATETIME NULL DEFAULT NULL,
	`pair` VARCHAR(100) NOT NULL COLLATE 'utf8mb4_general_ci',
	`amount` FLOAT NOT NULL DEFAULT '0',
	`billId` BIGINT(20) NOT NULL DEFAULT '0',
	PRIMARY KEY (`id`) USING BTREE
)
COLLATE='utf8mb4_general_ci'
ENGINE=InnoDB
AUTO_INCREMENT=155
;