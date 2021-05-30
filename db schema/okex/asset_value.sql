CREATE TABLE `asset_value` (
	`date` DATE NOT NULL,
	`value` FLOAT NOT NULL,
	PRIMARY KEY (`date`) USING BTREE
)
COLLATE='utf8mb4_general_ci'
ENGINE=InnoDB
;
